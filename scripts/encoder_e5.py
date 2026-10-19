"""Encoder de embedding LOCAL em numpy puro — `intfloat/multilingual-e5-base`.

**Por que existe (2026-10-19).** A checagem de apoio dos bullets
(`scripts/checagem_bullets.py`, Parte 1b) recupera, para cada bullet, as
reviews do grupo mais parecidas com ele. Os bullets estão em português; as
reviews, em inglês, alemão, espanhol, português… — a busca é TRANSLÍNGUE, e
nenhuma chamada paga é permitida. Este módulo roda o modelo inteiro no Mac,
com numpy, sem torch e sem rede.

**Por que este modelo** (a escolha, com o que pesou):
- é treinado PARA RECUPERAÇÃO assimétrica (prefixos `query:` / `passage:`),
  que é exatamente a forma do problema — um bullet curto procurando reviews;
  os modelos de paráfrase (p.ex. `paraphrase-multilingual-MiniLM-L12-v2`)
  são simétricos, treinados para similaridade de frases do mesmo tamanho;
- cobre os ~100 idiomas do XLM-R, com o alinhamento translíngue medido pelos
  autores (MIRACL, Mr.TyDi, recuperação de bitexto);
- JÁ ESTÁ NO DISCO (`~/.cache/huggingface`): nenhum download. O `bge-m3`
  seria mais forte e aceita textos mais longos, mas exigiria baixar ~2 GB e
  é um XLM-R large (3× mais lento em numpy) — fica como alternativa
  registrada, não como necessidade: as reviews da amostra têm mediana de
  ~300 caracteres e as longas são tratadas por janelas (`janelas`).

**O que é implementado, e só isso.** O forward do `XLMRobertaModel` (BERT com
posições deslocadas por `padding_idx + 1`), mean pooling com a máscara e
normalização L2 — os três módulos de `modules.json` do sentence-transformers.
Pesos lidos do `model.safetensors` por `np.memmap` (a matriz de vocabulário,
768 MB, não é carregada inteira). O tokenizador é o `tokenizer.json` do
próprio modelo, pela biblioteca `tokenizers` (Rust, da Hugging Face) —
importada só quando um texto é codificado, para que o resto do projeto não
dependa dela.

**Validação.** `tests/test_encoder_e5.py`: invariância à máscara (padding não
muda o vetor), posições do XLM-R, GELU exata, leitor de safetensors; e, com o
modelo no disco, o exemplo do próprio cartão do modelo (cada query fica mais
perto da sua passagem) e pares de tradução PT↔EN acima de pares sem relação.
"""
from __future__ import annotations

import json
import os
import re
import struct
from pathlib import Path

import numpy as np

MODELO_ID = "intfloat/multilingual-e5-base"
MAX_TOKENS = 512
# Janela de texto por pedaço. ~900 caracteres ≈ 220-260 tokens do XLM-R em
# inglês: folga de 2× sob o teto de 512 tokens, para que nenhum pedaço seja
# truncado em silêncio (o que o modelo não lê não pode ser recuperado).
JANELA_CHARS = 900

_DTYPES = {"F32": np.float32, "F16": np.float16, "I64": np.int64}


def diretorio_do_modelo(modelo_id: str = MODELO_ID) -> Path:
    """O snapshot que `refs/main` aponta no cache da Hugging Face. Sem rede:
    modelo ausente é erro com instrução, nunca download implícito."""
    raiz = Path(os.environ.get("HF_HOME") or Path.home() / ".cache" / "huggingface")
    base = raiz / "hub" / ("models--" + modelo_id.replace("/", "--"))
    ref = base / "refs" / "main"
    if not ref.exists():
        raise FileNotFoundError(
            f"{modelo_id} não está em {base}. Este módulo não baixa nada; "
            f"baixe uma vez com `huggingface-cli download {modelo_id}`.")
    return base / "snapshots" / ref.read_text().strip()


# ---------------------------------------------------------------------------
# safetensors
# ---------------------------------------------------------------------------

def ler_safetensors(caminho: Path) -> dict[str, np.ndarray]:
    """`{nome: array}` por memmap. Formato: 8 bytes little-endian com o
    tamanho do cabeçalho JSON, o cabeçalho, e o buffer cru."""
    caminho = Path(caminho)
    with caminho.open("rb") as fh:
        n = struct.unpack("<Q", fh.read(8))[0]
        cab = json.loads(fh.read(n))
    base = 8 + n
    mm = np.memmap(caminho, dtype=np.uint8, mode="r")
    fora = {}
    for nome, meta in cab.items():
        if nome == "__metadata__":
            continue
        ini, fim = meta["data_offsets"]
        dt = _DTYPES[meta["dtype"]]
        fora[nome] = mm[base + ini: base + fim].view(dt).reshape(meta["shape"])
    return fora


# ---------------------------------------------------------------------------
# forward
# ---------------------------------------------------------------------------

def gelu(x: np.ndarray) -> np.ndarray:
    """GELU EXATA (com erf), a `hidden_act: gelu` do config — não a
    aproximação por tanh."""
    from scipy.special import erf

    return 0.5 * x * (1.0 + erf(x / np.sqrt(2.0)))


def layer_norm(x: np.ndarray, w: np.ndarray, b: np.ndarray, eps: float) -> np.ndarray:
    mu = x.mean(-1, keepdims=True)
    var = ((x - mu) ** 2).mean(-1, keepdims=True)
    return (x - mu) / np.sqrt(var + eps) * w + b


def posicoes(ids: np.ndarray, padding_idx: int | None) -> np.ndarray:
    """XLM-R (`create_position_ids_from_input_ids`): conta só os tokens reais,
    a partir de `padding_idx + 1`; padding fica em `padding_idx`. BERT
    (`padding_idx=None`): 0..L-1."""
    if padding_idx is None:
        return np.broadcast_to(np.arange(ids.shape[1]), ids.shape)
    mask = (ids != padding_idx).astype(np.int64)
    return np.cumsum(mask, axis=1) * mask + padding_idx


class Encoder:
    def __init__(self, pesos: dict[str, np.ndarray], config: dict):
        self.p = pesos
        self.cfg = config
        self.n_camadas = config["num_hidden_layers"]
        self.n_cabecas = config["num_attention_heads"]
        self.eps = config.get("layer_norm_eps", 1e-12)
        self.pad = config.get("pad_token_id", 1)
        self.pad_pos = self.pad if config.get("model_type") == "xlm-roberta" else None
        self._tok = None
        self._dir: Path | None = None

    @classmethod
    def do_disco(cls, diretorio: Path | None = None) -> "Encoder":
        d = Path(diretorio) if diretorio else diretorio_do_modelo()
        enc = cls(ler_safetensors(d / "model.safetensors"),
                  json.loads((d / "config.json").read_text()))
        enc._dir = d
        return enc

    def _w(self, nome: str) -> np.ndarray:
        return np.asarray(self.p[nome], dtype=np.float32)

    def forward(self, ids: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """`ids`, `mask`: (B, L). Devolve o último estado oculto (B, L, H)."""
        B, L = ids.shape
        x = (np.asarray(self.p["embeddings.word_embeddings.weight"])[ids]
             .astype(np.float32)
             + self._w("embeddings.position_embeddings.weight")[
                 posicoes(ids, self.pad_pos)]
             + self._w("embeddings.token_type_embeddings.weight")[0])
        x = layer_norm(x, self._w("embeddings.LayerNorm.weight"),
                       self._w("embeddings.LayerNorm.bias"), self.eps)
        H = x.shape[-1]
        h, dh = self.n_cabecas, H // self.n_cabecas
        neg = (1.0 - mask[:, None, None, :].astype(np.float32)) * np.float32(-1e9)
        for i in range(self.n_camadas):
            pre = f"encoder.layer.{i}."
            lin = lambda t, n: t @ self._w(pre + n + ".weight").T + self._w(pre + n + ".bias")  # noqa: E731
            q = lin(x, "attention.self.query").reshape(B, L, h, dh).transpose(0, 2, 1, 3)
            k = lin(x, "attention.self.key").reshape(B, L, h, dh).transpose(0, 2, 1, 3)
            v = lin(x, "attention.self.value").reshape(B, L, h, dh).transpose(0, 2, 1, 3)
            s = q @ k.transpose(0, 1, 3, 2) / np.float32(np.sqrt(dh)) + neg
            s = s - s.max(-1, keepdims=True)
            a = np.exp(s)
            a /= a.sum(-1, keepdims=True)
            ctx = (a @ v).transpose(0, 2, 1, 3).reshape(B, L, H)
            x = layer_norm(lin(ctx, "attention.output.dense") + x,
                           self._w(pre + "attention.output.LayerNorm.weight"),
                           self._w(pre + "attention.output.LayerNorm.bias"), self.eps)
            m = gelu(lin(x, "intermediate.dense"))
            x = layer_norm(lin(m, "output.dense") + x,
                           self._w(pre + "output.LayerNorm.weight"),
                           self._w(pre + "output.LayerNorm.bias"), self.eps)
        return x

    def vetores(self, lotes_de_ids: list[list[int]]) -> np.ndarray:
        """Mean pooling com máscara + L2, um vetor por sequência. Agrupa por
        tamanho para não pagar padding: o resultado NÃO depende do lote
        (`tests/test_encoder_e5.py`, invariância à máscara)."""
        fora = np.zeros((len(lotes_de_ids), self.cfg["hidden_size"]), np.float32)
        ordem = sorted(range(len(lotes_de_ids)), key=lambda i: len(lotes_de_ids[i]))
        for ini in range(0, len(ordem), 16):
            idx = ordem[ini: ini + 16]
            L = max(len(lotes_de_ids[i]) for i in idx)
            ids = np.full((len(idx), L), self.pad, np.int64)
            mask = np.zeros((len(idx), L), np.int64)
            for j, i in enumerate(idx):
                s = lotes_de_ids[i]
                ids[j, :len(s)], mask[j, :len(s)] = s, 1
            hs = self.forward(ids, mask)
            m = mask[..., None].astype(np.float32)
            emb = (hs * m).sum(1) / np.maximum(m.sum(1), 1e-9)
            emb /= np.linalg.norm(emb, axis=1, keepdims=True)
            fora[idx] = emb
        return fora

    # --- texto ------------------------------------------------------------

    def tokenizador(self):
        if self._tok is None:
            try:
                from tokenizers import Tokenizer
            except ImportError as e:  # pragma: no cover - depende do ambiente
                raise SystemExit(
                    "a biblioteca `tokenizers` não está instalada neste Python "
                    "(`pip install tokenizers`) — ela lê o tokenizer.json do "
                    "modelo; o resto do encoder é numpy") from e
            self._tok = Tokenizer.from_file(str(self._dir / "tokenizer.json"))
        return self._tok

    def ids(self, texto: str) -> list[int]:
        """Com `<s>`/`</s>` e truncado em `MAX_TOKENS` — truncamento que as
        janelas existem para nunca acionar (`truncou`)."""
        ids = self.tokenizador().encode(texto).ids
        if len(ids) > MAX_TOKENS:
            ids = ids[:MAX_TOKENS - 1] + [ids[-1]]
        return ids

    def truncou(self, texto: str) -> bool:
        return len(self.tokenizador().encode(texto).ids) > MAX_TOKENS

    def queries(self, textos: list[str]) -> np.ndarray:
        return self.vetores([self.ids("query: " + t) for t in textos])

    def passagens(self, textos: list[str]) -> np.ndarray:
        return self.vetores([self.ids("passage: " + t) for t in textos])


def janelas(texto: str, limite: int = JANELA_CHARS) -> list[str]:
    """Pedaços de até `limite` caracteres, cortados em fim de frase. Review
    curta (a maioria) é UM pedaço — o texto inteiro. Frase maior que o
    limite é cortada em palavras. Nada do texto se perde: a concatenação dos
    pedaços (com espaço) reproduz as palavras do original, na ordem."""
    texto = " ".join(texto.split())
    if len(texto) <= limite:
        return [texto] if texto else []
    frases = re.split(r"(?<=[.!?…])\s+", texto)
    pedacos: list[str] = []
    atual = ""
    for f in frases:
        while len(f) > limite:
            corte = f.rfind(" ", 0, limite)
            corte = corte if corte > 0 else limite
            if atual:
                pedacos.append(atual)
                atual = ""
            pedacos.append(f[:corte].strip())
            f = f[corte:].strip()
        if not f:
            continue
        if atual and len(atual) + 1 + len(f) > limite:
            pedacos.append(atual)
            atual = f
        else:
            atual = f"{atual} {f}".strip()
    if atual:
        pedacos.append(atual)
    return pedacos
