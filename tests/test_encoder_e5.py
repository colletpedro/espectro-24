"""[2026-10-19] O encoder de embedding local em numpy (`scripts/encoder_e5.py`):
leitor de safetensors, posições do XLM-R, GELU exata, invariância à máscara,
janelas que não perdem texto — e, com o modelo no disco, o comportamento do
multilingual-e5-base em pares conhecidos."""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import encoder_e5 as E  # noqa: E402


def _escrever_safetensors(caminho: Path, tensores: dict[str, np.ndarray]) -> None:
    cab, buf, pos = {"__metadata__": {"format": "pt"}}, b"", 0
    for nome, arr in tensores.items():
        dados = np.ascontiguousarray(arr).tobytes()
        dt = {np.dtype(np.float32): "F32", np.dtype(np.int64): "I64"}[arr.dtype]
        cab[nome] = {"dtype": dt, "shape": list(arr.shape),
                     "data_offsets": [pos, pos + len(dados)]}
        buf += dados
        pos += len(dados)
    h = json.dumps(cab).encode()
    caminho.write_bytes(struct.pack("<Q", len(h)) + h + buf)


def test_safetensors_le_o_que_foi_escrito(tmp_path):
    a = np.arange(12, dtype=np.float32).reshape(3, 4)
    b = np.array([[7, 8, 9]], dtype=np.int64)
    _escrever_safetensors(tmp_path / "m.safetensors", {"a": a, "b": b})
    lido = E.ler_safetensors(tmp_path / "m.safetensors")
    assert set(lido) == {"a", "b"}
    np.testing.assert_array_equal(lido["a"], a)
    np.testing.assert_array_equal(lido["b"], b)


def test_posicoes_do_xlmr_comecam_depois_do_padding_idx():
    ids = np.array([[0, 5, 6, 2, 1, 1]])
    assert E.posicoes(ids, padding_idx=1).tolist() == [[2, 3, 4, 5, 1, 1]]
    assert E.posicoes(ids, padding_idx=None).tolist() == [[0, 1, 2, 3, 4, 5]]


def test_gelu_e_a_exata_com_erf():
    x = np.linspace(-4, 4, 33)
    ref = np.array([0.5 * v * (1 + math.erf(v / math.sqrt(2))) for v in x])
    np.testing.assert_allclose(E.gelu(x), ref, rtol=1e-12, atol=1e-12)


def _encoder_minusculo(seed: int = 0) -> E.Encoder:
    rng = np.random.default_rng(seed)
    H, I, V, P = 8, 16, 30, 20
    p = {"embeddings.word_embeddings.weight": rng.normal(size=(V, H)),
         "embeddings.position_embeddings.weight": rng.normal(size=(P, H)),
         "embeddings.token_type_embeddings.weight": rng.normal(size=(1, H)),
         "embeddings.LayerNorm.weight": np.ones(H), "embeddings.LayerNorm.bias": np.zeros(H)}
    for i in range(2):
        pre = f"encoder.layer.{i}."
        for n, (o, d) in {"attention.self.query": (H, H), "attention.self.key": (H, H),
                          "attention.self.value": (H, H), "attention.output.dense": (H, H),
                          "intermediate.dense": (I, H), "output.dense": (H, I)}.items():
            p[pre + n + ".weight"] = rng.normal(size=(o, d)) * 0.3
            p[pre + n + ".bias"] = rng.normal(size=o) * 0.1
        for n in ("attention.output.LayerNorm", "output.LayerNorm"):
            p[pre + n + ".weight"], p[pre + n + ".bias"] = np.ones(H), np.zeros(H)
    p = {k: v.astype(np.float32) for k, v in p.items()}
    cfg = {"num_hidden_layers": 2, "num_attention_heads": 2, "hidden_size": H,
           "layer_norm_eps": 1e-5, "pad_token_id": 1, "model_type": "xlm-roberta"}
    return E.Encoder(p, cfg)


def test_o_vetor_nao_depende_do_lote_nem_do_padding():
    enc = _encoder_minusculo()
    curta = [0, 5, 6, 2]
    sozinha = enc.vetores([curta])[0]
    com_longa = enc.vetores([curta, [0, 7, 8, 9, 10, 11, 12, 2]])[0]
    np.testing.assert_allclose(sozinha, com_longa, atol=1e-5)
    assert abs(np.linalg.norm(sozinha) - 1) < 1e-5


def test_vetores_devolvem_na_ordem_de_entrada():
    enc = _encoder_minusculo()
    seqs = [[0, 5, 6, 7, 8, 2], [0, 9, 2], [0, 3, 4, 2]]
    junto = enc.vetores(seqs)
    for i, s in enumerate(seqs):
        np.testing.assert_allclose(junto[i], enc.vetores([s])[0], atol=1e-5)


def test_janelas_curta_e_um_pedaco_so():
    assert E.janelas("  Um   texto curto.  ") == ["Um texto curto."]
    assert E.janelas("") == []


def test_janelas_respeitam_o_limite_e_nao_perdem_palavra():
    frases = [f"Frase numero {i} com algumas palavras a mais." for i in range(60)]
    texto = " ".join(frases) + " " + "palavra " * 300   # cauda sem pontuação
    pedacos = E.janelas(texto, limite=200)
    assert len(pedacos) > 1
    assert all(len(p) <= 200 for p in pedacos)
    assert " ".join(pedacos).split() == texto.split()


# --- com o modelo no disco ----------------------------------------------------

def _modelo():
    try:
        return E.Encoder.do_disco()
    except FileNotFoundError as e:
        pytest.skip(f"multilingual-e5-base fora do cache da Hugging Face: {e}")


# Ids do tokenizer.json do próprio modelo (biblioteca `tokenizers` 0.22.2,
# 2026-10-19), congelados aqui para que o teste do FORWARD rode sem ela.
# 0-1: as queries do cartão do modelo; 2-3: o começo das passagens dele;
# 4: query PT; 5-6: passagens EN (a tradução e uma sem relação).
IDS = [
    [0, 41, 1294, 12, 3642, 5045, 21308, 5608, 10, 117776, 73203, 2],
    [0, 41, 1294, 12, 6, 4617, 39613, 43, 1433, 6856, 115371, 2],
    [0, 46692, 12, 1301, 10, 4537, 17997, 2256, 4, 70, 7915, 441, 25, 7, 83080, 64209,
     674, 111, 21308, 100, 24793, 10, 4188, 953, 47, 2358, 83, 7621, 16190, 7, 117,
     5155, 5, 2],
    [0, 46692, 12, 615, 7318, 54107, 4617, 39613, 59580, 6, 105336, 12, 88232, 4617,
     39613, 6193, 3294, 6, 17619, 8794, 12, 243853, 37, 152890, 37, 3515, 25407, 37,
     60793, 8539, 2],
    [0, 41, 1294, 12, 55185, 48121, 28, 10298, 590, 246, 2],
    [0, 46692, 12, 581, 249, 21896, 83, 221, 72803, 4, 442, 24911, 7, 100, 6626, 21974, 5, 2],
    [0, 46692, 12, 581, 217148, 83, 51, 2472, 3794, 22819, 5, 2],
]


def test_cartao_do_modelo_cada_query_perto_da_sua_passagem():
    v = _modelo().vetores(IDS)
    s = v[:2] @ v[2:4].T
    assert s[0, 0] > s[0, 1] + 0.1 and s[1, 1] > s[1, 0] + 0.1
    # valores desta implementação em 2026-10-19 (regressão, não oráculo externo)
    np.testing.assert_allclose(s, [[0.9001, 0.7390], [0.7335, 0.9029]], atol=2e-3)


def test_translingue_a_traducao_fica_acima_da_frase_sem_relacao():
    v = _modelo().vetores(IDS)
    assert float(v[4] @ v[5]) > float(v[4] @ v[6]) + 0.02
