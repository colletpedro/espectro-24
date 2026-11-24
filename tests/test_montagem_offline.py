"""`montagem_offline.py`: a síntese INJETADA no bucket (sem chamar modelo). A validação campo a campo contra os 29 de
08/11 está em `scripts/validar_montador_29.py` (precisa de `execucoes/`, fora do git); aqui, o contrato da injeção."""
import json

import pytest

from espectro24 import montagem_offline as M
from espectro24.models import BucketResult, LevelResult, Review


def _bucket(n=6):
    lvl = LevelResult(3.0, 150, 1, 0, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"v{i}", rating=3.5, text=f"review {i}", truncated=False,
                          full_text_url=None, spoiler=False, full_text=f"review {i} completa") for i in range(n)]
    return BucketResult(nome="medianas", alvo=40, modo="completo", niveis=[lvl])


def _registro(**kw):
    base = {"temas": [{"tema": "Trilha", "mencoes_aproximadas": 3, "n_reviews_analisadas": 6,
                       "exemplo_parafraseado": "A trilha é marcante.", "mencoes_clampadas": False,
                       "mencoes_valor_original": None, "aspas_removidas": False,
                       "quantidade_pendente": True, "campo_desconhecido": 1}],
            "observacao_geral": "Este grupo elogia a trilha.", "n_validas": 6, "n_analisadas": 6,
            "idioma_invalido": False, "escopo_suspeito": True}
    return {**base, **kw}


def test_aplicar_sintese_preenche_o_bucket_e_ignora_campo_desconhecido():
    b = M.aplicar_sintese(_bucket(), _registro(), "aceito")
    assert b.temas[0].tema == "Trilha" and b.temas[0].quantidade_pendente is True
    assert b.observacao_geral == "Este grupo elogia a trilha."
    assert (b.idioma_invalido, b.escopo_suspeito, b.quantidade_fallback) == (False, True, "aceito")


def test_aplicar_sintese_recusa_amostra_diferente():
    with pytest.raises(ValueError, match="n_validas"):
        M.aplicar_sintese(_bucket(), _registro(n_validas=40))
    with pytest.raises(ValueError, match="n_analisadas"):
        M.aplicar_sintese(_bucket(), _registro(n_analisadas=40))


def test_sha256_arquivo(tmp_path):
    p = tmp_path / "a"
    p.write_text("x")
    assert M.sha256_arquivo(p) == "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881"
