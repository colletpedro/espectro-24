"""Comum da fase 0 do fine-tuning da SÍNTESE: caminhos, filmes, prompts, tokens.

Quem importa este módulo já importou `_guarda` (sem chave, sem rede). Nada aqui
chama LLM: os prompts são REMONTADOS pelo código de produção
(`synthesize.build_system_prompt` / `build_user_message`, e os `montar_briefing`
de narrativa, veredito e condições) a partir de `dados/bruto` e do JSON
publicado, que é só lido.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "scripts")]

RESULTADO_DIR = RAIZ / "resultado"
BRUTO_DIR = RAIZ / "dados" / "bruto"
FINETUNE_DIR = RAIZ / "finetune"
BUCKETS = ("negativas", "medianas", "positivas")

# Os 5 filmes da medição de referência (checagem-bullets, branch gate-local).
# Vão OBRIGATORIAMENTE para o teste e nunca entram em treino.
REFERENCIA_5 = ("anatomy-of-a-fall", "incendies", "mother-2017", "napoleon-2023",
                "the-substance")

# --- Proveniência da síntese, por commit em que os temas ATUAIS apareceram ---
# (achado por `git log` de cada resultado/<slug>.json; ver inventario.py).
# O modelo servido: `deepseek-v4-flash` em config.py em todas as épocas
# DeepSeek, mas o alias é roteado para o V4.1-Flash desde 2026-09-10 04:00 UTC
# (`preco.TABELA_VIGENTE_DESDE`). Época = modelo-professor, não só data.
LOTES = {
    "b3f3f732c": {"lote": "demo-v1.1.3", "data": "2026-07-20",
                  "professor": "nenhum: 3 buckets sem_analise, 0 chamadas de síntese",
                  "deepseek": False},
    "d0dee5159": {"lote": "republicacao-3", "data": "2026-08-16",
                  "professor": "deepseek-v4-flash (V4-Flash)", "deepseek": True},
    "31c463528": {"lote": "catalogo-35", "data": "2026-08-22",
                  "professor": "deepseek-v4-flash (V4-Flash)", "deepseek": True},
    "0a777c3e2": {"lote": "obsession-migracao", "data": "2026-09-08",
                  "professor": "deepseek-v4-flash (V4-Flash)", "deepseek": True},
    "1253eb73d": {"lote": "expansao-53", "data": "2026-09-14",
                  "professor": "deepseek-v4-flash → V4.1-Flash", "deepseek": True},
    "594786f55": {"lote": "fallback-conteudo", "data": "2026-09-14",
                  "professor": "deepseek-v4-flash → V4.1-Flash (+1 bucket Gemini)",
                  "deepseek": True},
    "7d2fa09eb": {"lote": "expansao-99", "data": "2026-09-17",
                  "professor": "deepseek-v4-flash → V4.1-Flash", "deepseek": True},
}
EPOCA_V41 = "2026-09-10"


def epoca_do_professor(data: str) -> str:
    return "V4.1-Flash" if data >= EPOCA_V41 else "V4-Flash"


# --- Exclusões PROPOSTAS (decisão do dono) --------------------------------
# Fora de TODOS os conjuntos (treino, validação, teste), em todos os estágios.
EXCLUIR_FILMES = {
    "obsession-2025": "família obsession-*: o corpus publicado começou como o do "
                      "curta (obsession-2026) e foi migrado para o do longa em "
                      "v1.9.50 (ABERTO C13); o gabarito humano ainda tem 6 "
                      "reviews do curta",
    "como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual":
        "JSON de v1.1.3 (2026-07-20): os 3 buckets são sem_analise (0 chamadas "
        "de síntese) e não há eixos, narrativa, veredito nem condições — "
        "nenhum estágio utilizável",
}
# Fora como EXEMPLO de síntese, mas o filme fica no seu conjunto (a unidade do
# split é o filme): bucket cuja síntese não é DeepSeek.
EXCLUIR_BUCKETS_SINTESE_MOTIVO = "fallback_conteudo: síntese deste bucket feita pelo Gemini"


def rodar_texto(args: list[str], **kw) -> subprocess.CompletedProcess:
    """`subprocess.run` que lê a saída como TEXTO sem depender do locale.

    No Windows o padrão de `text=True` é o cp1252: o `ollama create` imprime
    bytes que não existem nele (0x8f, do spinner em UTF-8), a thread de leitura
    cai com UnicodeDecodeError e `stderr` volta None (2026-10-30). Aqui a
    saída é sempre UTF-8 com `errors="replace"`, e `stdout`/`stderr` voltam
    `""` em vez de None. Captura por padrão; `timeout` e `env` passam direto."""
    kw.setdefault("capture_output", True)
    r = subprocess.run(args, text=True, encoding="utf-8", errors="replace", **kw)
    r.stdout = r.stdout or ""
    r.stderr = r.stderr or ""
    return r


def ler_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha256_arquivo(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def sha256_texto(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def publicados() -> dict[str, dict]:
    return {p.stem: ler_json(p) for p in sorted(RESULTADO_DIR.glob("*.json"))}


# ---------------------------------------------------------------------------
# Síntese: o par entrada → saída
# ---------------------------------------------------------------------------

def buckets_remontados(slug: str, pub: dict):
    """Os `BucketResult` que a síntese leria hoje: `selecionar` sobre o bruto
    persistido, com o histograma e o orçamento gravados no `coleta` do
    publicado (o caminho de `prosa_local._buckets_do_bruto`)."""
    from espectro24.prosa_local import _buckets_do_bruto
    return _buckets_do_bruto(slug, pub["coleta"], BRUTO_DIR)


def prompt_sintese(bucket) -> tuple[str, str]:
    from espectro24.synthesize import build_system_prompt, build_user_message
    return build_system_prompt(bucket.nome), build_user_message(bucket)


CAMPOS_TEMA_MODELO = ("tema", "mencoes_aproximadas", "n_reviews_analisadas",
                      "exemplo_parafraseado")


def alvo_publicado(bpub: dict) -> dict:
    """O JSON-alvo no formato que o prompt pede, a partir do PUBLICADO. Os
    campos que o código acrescenta (`mencoes_clampadas`, `aspas_removidas`,
    ...) saem; `mencoes_aproximadas` é o valor publicado (pós-clamp)."""
    return {"bucket": bpub["bucket"],
            "temas": [{k: t[k] for k in CAMPOS_TEMA_MODELO} for t in bpub.get("temas") or []],
            "observacao_geral": bpub.get("observacao_geral") or ""}


def serializar_alvo(alvo: dict) -> str:
    """Formato PROPOSTO do alvo de treino: JSON com indentação 2, chaves na
    ordem do schema do prompt, UTF-8 cru. O DeepSeek devolveu um texto cujo
    formato exato não foi gravado; este é o lado conservador em tokens."""
    return json.dumps(alvo, ensure_ascii=False, indent=2)


def bucket_e_exemplo_de_sintese(bpub: dict) -> tuple[bool, str | None]:
    """(utilizável, motivo_se_não)."""
    if bpub.get("modo") == "sem_analise":
        return False, "sem_analise (abaixo do piso)"
    if not bpub.get("temas"):
        return False, "sem temas"
    if bpub.get("fallback_conteudo"):
        return False, EXCLUIR_BUCKETS_SINTESE_MOTIVO
    return True, None


# ---------------------------------------------------------------------------
# Outros estágios: o prompt do PRIMEIRO candidato, capturado sem chamar nada
# ---------------------------------------------------------------------------

class _Capturado(BaseException):
    """BaseException de propósito: atravessa os `except Exception` do
    best-of-N e para na primeira chamada."""

    def __init__(self, system, user):
        self.system, self.user = system, user


def _capturar(gerador, pub: dict, **kw) -> tuple[str, str] | None:
    def gerar(system, user):
        raise _Capturado(system, user)
    try:
        r = gerador(pub, n=1, provider="injetado", model="injetado", gerar=gerar, **kw)
    except _Capturado as c:
        return c.system, c.user
    if r is None:
        return None
    raise RuntimeError("o estágio terminou sem chamar o modelo")


def prompt_narrativa(pub: dict):
    from espectro24.narrador import narrar
    return _capturar(narrar, pub)


def prompt_veredito(pub: dict):
    from espectro24 import veredito as V
    return _capturar(V.gerar, pub)


def prompt_condicoes(pub: dict):
    from espectro24 import condicoes as C
    return _capturar(C.gerar, pub)


def saida_narrativa(pub: dict) -> str | None:
    t = pub.get("narrativa")
    return json.dumps({"narrativa": t}, ensure_ascii=False) if t else None


def saida_veredito(pub: dict) -> str | None:
    v = pub.get("veredito") or {}
    t = v.get("texto_modelo") or v.get("texto")
    return json.dumps({"veredito": t}, ensure_ascii=False) if t else None


def saida_condicoes(pub: dict) -> str | None:
    """ESTIMADA: o formato que `condicoes.extrair` lê, montado do publicado
    (que passou por leitura humana; é o dado do dono, não a saída do Gemini)."""
    c = pub.get("condicoes")
    if not c:
        return None
    d = {lado: [{"tema_origem": i.get("tema_origem"), "texto": i.get("texto")}
                for i in c.get(lado) or []] for lado in ("vale_a_pena", "talvez_evite")}
    d["sem_condicao"] = [{"tema_origem": r.get("tema_origem"), "regra": r.get("regra"),
                          "motivo": r.get("motivo")}
                         for r in c.get("sem_condicao_publicavel") or []]
    return json.dumps(d, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tokenizers dos candidatos (só o tokenizer; nenhum peso)
# ---------------------------------------------------------------------------

# Revisão fixada: o commit do repositório no Hugging Face em 2026-10-20.
CANDIDATOS = {
    "Qwen3.5-9B": {"repo": "Qwen/Qwen3.5-9B",
                   "revisao": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
                   "familia": "qwen"},
    "Gemma-4-E4B": {"repo": "google/gemma-4-E4B-it",
                    "revisao": "ee0ef6023621cff504d758262d4e04895a5af4a2",
                    "familia": "gemma"},
    "Gemma-4-12B": {"repo": "google/gemma-4-12B-it",
                    "revisao": "707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7",
                    "familia": "gemma"},
}
# Qwen3-8B (reserva): o repositório que o Kaggle carrega (`smoke_treino.py`), na
# revisão confirmada no pré-voo. Fora de `CANDIDATOS` de propósito: os scripts
# da fase 0 (inventário, reconstrução) iteram `CANDIDATOS` e não mudam.
CANDIDATOS_EXTRA = {
    "Qwen3-8B": {"repo": "unsloth/Qwen3-8B-unsloth-bnb-4bit",
                 "revisao": "62efd7f9d748e394734a7adae2adf96e13a2abc8",
                 "familia": "qwen"},
}
ARQUIVOS_TOKENIZER = ("tokenizer.json", "tokenizer_config.json", "chat_template.jinja",
                      "config.json")
TOKENIZERS_DIR_PADRAO = Path(os.environ.get(
    "ESPECTRO24_FINETUNE_TOKENIZERS",
    Path.home() / ".cache" / "espectro24-finetune" / "tokenizers"))


def _candidato(nome: str) -> dict:
    return CANDIDATOS.get(nome) or CANDIDATOS_EXTRA[nome]


def pasta_do_candidato(raiz: Path, nome: str) -> Path:
    return Path(raiz) / _candidato(nome)["repo"].replace("/", "_")


def carregar_tokenizer(nome: str, raiz: Path = TOKENIZERS_DIR_PADRAO):
    """Um só tokenizer (inclui os de `CANDIDATOS_EXTRA`)."""
    from tokenizers import Tokenizer
    return Tokenizer.from_file(str(pasta_do_candidato(raiz, nome) / "tokenizer.json"))


def carregar_tokenizers(raiz: Path = TOKENIZERS_DIR_PADRAO) -> dict:
    from tokenizers import Tokenizer
    return {n: Tokenizer.from_file(str(pasta_do_candidato(raiz, n) / "tokenizer.json"))
            for n in CANDIDATOS}


def chat(familia: str, system: str, user: str, saida: str | None) -> str:
    """O texto que o modelo vê, montado à mão a partir do `chat_template.jinja`
    de cada repositório (não há jinja2 no venv), com o raciocínio DESLIGADO:

    - Qwen3.5: `enable_thinking=false` = bloco `<think>\\n\\n</think>\\n\\n`
      vazio aberto pelo próprio template no turno do assistente;
    - Gemma 4: o padrão do template já é `enable_thinking=false` (sem o
      token `<|think|>` no system).

    `saida=None` devolve só o prompt (até o início da resposta).

    Qwen3: o template NÃO apara o conteúdo. Até 2026-10-30 o `user` era aparado
    aqui, e o `\\n` final do prompt de síntese sumia; o Kaggle (v4 do smoke)
    renderizou com ele, e os 6 exemplos ficaram com 1 caractere a mais (e até 1
    token) do que o `chat_esperado` gravado no dataset `ae74737d…`."""
    if familia == "qwen":
        p = (f"<|im_start|>system\n{system}<|im_end|>\n"
             f"<|im_start|>user\n{user}<|im_end|>\n"
             f"<|im_start|>assistant\n<think>\n\n</think>\n\n")
        fim = "<|im_end|>\n"
    elif familia == "gemma":
        p = (f"<bos><|turn>system\n{system.strip()}<turn|>\n"
             f"<|turn>user\n{user.strip()}<turn|>\n<|turn>model\n")
        fim = "<turn|>\n"
    else:
        raise ValueError(familia)
    return p if saida is None else p + saida + fim


def contar(tok, texto: str) -> int:
    return len(tok.encode(texto, add_special_tokens=False).ids)


def tokens_do_par(toks: dict, system: str, user: str, saida: str) -> dict:
    """Por candidato: entrada (prompt com template), saída (com o fim de turno)
    e o total do exemplo de treino."""
    fora = {}
    for nome, tok in toks.items():
        fam = _candidato(nome)["familia"]
        p = contar(tok, chat(fam, system, user, None))
        tot = contar(tok, chat(fam, system, user, saida))
        fora[nome] = {"entrada": p, "saida": tot - p, "total": tot}
    return fora


def quantis(vals: list[int]) -> dict:
    if not vals:
        return {"n": 0}
    v = sorted(vals)

    def q(p):
        # quantil "nearest-rank": o menor valor com ao menos p% abaixo ou igual
        return v[max(0, math.ceil(p * len(v)) - 1)]
    return {"n": len(v), "mediana": statistics.median(v), "p90": q(0.90),
            "p99": q(0.99), "max": v[-1]}


def arredondar(n: int, passo: int = 1024) -> int:
    return int(math.ceil(n / passo) * passo)
