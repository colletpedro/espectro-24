"""`scripts/finetune/c22_fallback.py`: o fallback da guarda só nos buckets pendentes do C22.
Cliente falso, zero rede, zero modelo; dados sintéticos em tmp_path."""
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import _cego  # noqa: E402
_PASTA_CEGA_ANTES = _cego.PASTA
import c22_fallback as FB  # noqa: E402
_cego.PASTA = _PASTA_CEGA_ANTES
import comum as K  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402
from espectro24.models import Tema  # noqa: E402

PENDENTE = "Poucos gostaram do final."
LIMPO = "Espectadores não gostaram do final."


def _resp(exemplos, obs="Este grupo tem opiniões mistas."):
    return json.dumps({"temas": [{"tema": f"Tema {i} do filme", "mencoes_aproximadas": 3,
                                  "exemplo_parafraseado": e} for i, e in enumerate(exemplos)],
                       "observacao_geral": obs}, ensure_ascii=False)


def _entrada():
    return {"bucket": "medianas", "alvo": 40, "modo": "completo", "estado_piso": "ok",
            "reviews": [{"viewing_id": f"viewing:{i}", "rating": 3.5, "text": f"review {i} completa"}
                        for i in range(6)]}


def _registro(slug="filme", bucket="medianas", exemplos=(PENDENTE, "A trilha é marcante.")):
    temas = S._construir_temas(json.loads(_resp(list(exemplos))), 6)
    return {"slug": slug, "bucket": bucket, "ok": True,
            "bucket_final": {"temas": [asdict(t) for t in temas], "observacao_geral": "Este grupo tem opiniões mistas.",
                             "n_validas": 6, "n_analisadas": 6, "idioma_invalido": False, "escopo_suspeito": False}}


def test_pendentes_so_conta_bucket_ok_com_tema_pendente(tmp_path):
    (tmp_path / "filme__medianas.json").write_text(json.dumps(_registro()))
    (tmp_path / "filme__positivas.json").write_text(json.dumps(
        _registro(bucket="positivas", exemplos=("A fotografia chama atenção.",))))
    ruim = _registro(bucket="negativas")
    ruim["ok"] = False
    (tmp_path / "filme__negativas.json").write_text(json.dumps(ruim))
    (tmp_path / "manifesto.json").write_text("{}")
    r = FB.listar_pendentes(tmp_path)
    assert r["buckets_total"] == 3 and r["buckets_pendentes"] == 1 and r["bullets_pendentes"] == 1
    assert r["itens"][0]["bucket"] == "medianas" and r["itens"][0]["n_temas"] == 2


def test_rodar_um_aceita_sem_regerar_a_primeira_chamada():
    chamadas = []

    def chamar(system, user):
        chamadas.append(system)
        return _resp([LIMPO, "A trilha é marcante."])

    novo = FB.rodar_um(_registro(), _entrada(), chamar)
    assert len(chamadas) == 1 and chamadas[0].endswith(S._REFORCO_QUANTIDADE)   # UMA chamada, a do reforço
    assert novo["quantidade_fallback"] == "aceito"
    assert (novo["pendentes_antes"], novo["pendentes_depois"]) == (1, 0)
    assert novo["n_temas_antes"] == novo["n_temas_depois"] == 2
    assert novo["bucket_final_antes"]["temas"][0]["quantidade_pendente"] is True


def test_rodar_um_recusado_mantem_o_texto_do_c22():
    novo = FB.rodar_um(_registro(), _entrada(), lambda s, u: _resp([PENDENTE, "A trilha é marcante."]))
    assert novo["quantidade_fallback"] == "recusado_sem_ganho"
    assert novo["bucket_final"] == novo["bucket_final_antes"] and novo["pendentes_depois"] == 1


def test_rodar_um_recusa_prompt_diferente_do_plano():
    plano = {"system_sha256": "0" * 64, "user_sha256": "0" * 64}
    with pytest.raises(SystemExit, match="prompt remontado"):
        FB.rodar_um(_registro(), _entrada(), lambda s, u: _resp([LIMPO]), plano)


def test_montar_producao_so_substitui_o_aceito(tmp_path):
    sint, fb = tmp_path / "s", tmp_path / "f"
    sint.mkdir(), fb.mkdir()
    for nome, ex in (("a__medianas", (PENDENTE, "x")), ("b__medianas", (PENDENTE, "x")),
                     ("c__medianas", ("A trilha é marcante.", "y")), ("d__medianas", (PENDENTE, "x"))):
        slug, bucket = nome.split("__")
        (sint / f"{nome}.json").write_text(json.dumps(_registro(slug, bucket, ex)))
    aceito = FB.rodar_um(_registro("a", "medianas"), _entrada(), lambda s, u: _resp([LIMPO, "x"]))
    recusado = FB.rodar_um(_registro("b", "medianas"), _entrada(), lambda s, u: _resp([PENDENTE, "x"]))
    (fb / "a__medianas.json").write_text(json.dumps(aceito))
    (fb / "b__medianas.json").write_text(json.dumps(recusado))
    por = {f"{r['slug']}": r for r in FB.montar_producao(sint, fb)}
    assert por["a"]["origem"] == "c22_fallback_aceito" and por["a"]["pendentes_depois"] == 0
    assert por["b"]["origem"] == "c22_fallback_recusado_sem_ganho" and por["b"]["pendentes_depois"] == 1
    assert por["c"]["origem"] == "c22_sem_fallback" and por["c"]["quantidade_fallback"] is None
    assert por["d"]["origem"] == "c22_pendente_sem_fallback_rodado"
