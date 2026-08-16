"""Render (§E) — foco na mudança v1.1.4: bucket sem_analise aponta para a
URL de reviews em vez de exibir texto bruto."""
import json

from espectro24 import render
from espectro24.models import BucketResult, LevelResult, Review, Tema
from espectro24.render import build_output, render_terminal, reviews_url_de


def _nivel(nivel, n_validas, texto="x" * 200):
    lvl = LevelResult(nivel, 0, 1, n_validas, 0, 0, 0, 0)
    lvl.validas = [
        Review(viewing_id=f"v{nivel}_{i}", rating=nivel, text=texto,
               truncated=False, full_text_url=None, spoiler=False, full_text=texto)
        for i in range(n_validas)
    ]
    return lvl


def _bucket_sem_analise(nome="negativas", n=1, texto="SEGREDO_DO_ENREDO"):
    b = BucketResult(nome=nome, alvo=50, modo="sem_analise",
                     niveis=[_nivel(2.0, n, texto)])
    b.observacao_geral = (
        f"Bucket sem análise temática: apenas {n} review(s) válida(s) (piso é 3).")
    return b


def _output(bucket, slug="cure"):
    return build_output(slug, [bucket], "2026-01-01T00:00:00Z", {}, 9)


def test_build_output_inclui_reviews_url():
    out = _output(_bucket_sem_analise(), slug="cure")
    assert out["reviews_url"] == "https://letterboxd.com/film/cure/reviews/"
    assert reviews_url_de("cure") == out["reviews_url"]


def test_sem_analise_exibe_contagem_e_url():
    out = _output(_bucket_sem_analise(n=2), slug="cure")
    render = render_terminal(out)
    # contagem atual mantida
    assert "Bucket sem análise temática: apenas 2 review(s) válida(s)" in render
    # linha nova de URL, com a contagem do bucket
    assert "→ 2 review(s) disponíveis em https://letterboxd.com/film/cure/reviews/" in render


def test_sem_analise_nao_exibe_texto_bruto_da_review():
    # regressão v1.1.4: o texto integral da review NÃO deve aparecer no render
    # (removido do §3[C] por risco de spoiler)
    out = _output(_bucket_sem_analise(n=1, texto="SEGREDO_DO_ENREDO"), slug="cure")
    render = render_terminal(out)
    assert "SEGREDO_DO_ENREDO" not in render


def test_sem_analise_nao_inventa_temas_no_render():
    out = _output(_bucket_sem_analise(n=2), slug="cure")
    render = render_terminal(out)
    assert "mencionado em" not in render  # nenhum tema renderizado


def test_render_deriva_url_se_faltar_no_dict():
    # robustez: dict antigo sem reviews_url ainda renderiza a linha corretamente
    out = _output(_bucket_sem_analise(n=1), slug="oppenheimer-2023")
    del out["reviews_url"]
    render = render_terminal(out)
    assert "https://letterboxd.com/film/oppenheimer-2023/reviews/" in render


def test_bucket_completo_nao_ganha_linha_de_url():
    # a linha de URL é exclusiva de sem_analise
    lvl = _nivel(4.0, 3)
    b = BucketResult(nome="positivas", alvo=30, modo="completo", niveis=[lvl],
                     temas=[Tema("ritmo", 2, 3, "este grupo achou o ritmo lento")],
                     observacao_geral="as reviews positivas destacam o ritmo")
    render = render_terminal(_output(b))
    assert "review(s) disponíveis em" not in render
    assert "mencionado em ~2 de 3 reviews" in render


# --- v1.2.0: tons de saída ---

def _output_completo_com_narrativa():
    lvl = _nivel(4.0, 3)
    b = BucketResult(nome="positivas", alvo=30, modo="completo", niveis=[lvl],
                     temas=[Tema("ritmo", 2, 3, "este grupo achou o ritmo bom")],
                     observacao_geral="as reviews positivas destacam o ritmo")
    out = _output(b)
    out["narrativa"] = "PROSA_NARRATIVA_DO_FILME sobre quem gostou e quem não."
    out["narrativa_flags"] = {"idioma_invalido": False, "escopo_suspeito": False,
                              "aspas_removidas": False, "falhou": False}
    return out


def test_tom_estruturado_mostra_temas_sem_narrativa():
    out = _output_completo_com_narrativa()
    render = render_terminal(out, tom="estruturado")
    assert "mencionado em ~2 de 3 reviews" in render
    assert "NARRATIVA" not in render
    assert "PROSA_NARRATIVA_DO_FILME" not in render


def test_tom_narrativo_esconde_temas_mostra_prosa_e_metadados():
    out = _output_completo_com_narrativa()
    render = render_terminal(out, tom="narrativo")
    assert "PROSA_NARRATIVA_DO_FILME" in render
    assert "mencionado em" not in render          # temas escondidos
    assert "▸ POSITIVAS" in render                 # metadados permanecem
    assert "filtro aplicado" in render
    assert "Total de reviews observadas" in render


def test_tom_ambos_mostra_temas_e_prosa():
    out = _output_completo_com_narrativa()
    render = render_terminal(out, tom="ambos")
    assert "mencionado em ~2 de 3 reviews" in render
    assert "PROSA_NARRATIVA_DO_FILME" in render


def test_tom_narrativo_mantem_avisos_de_degradado():
    # modo degradado continua visível no tom narrativo
    out = _output(_bucket_sem_analise(n=1), slug="cure")
    out["narrativa"] = "poucas reviews; sem padrão claro."
    out["narrativa_flags"] = {"idioma_invalido": False, "escopo_suspeito": False,
                              "aspas_removidas": False, "falhou": False}
    render = render_terminal(out, tom="narrativo")
    assert "sem análise temática" in render        # aviso de degradado
    assert "review(s) disponíveis em" in render    # URL permanece
    assert "poucas reviews; sem padrão claro." in render


def test_tom_narrativo_flags_da_narrativa_visiveis():
    out = _output_completo_com_narrativa()
    out["narrativa_flags"]["escopo_suspeito"] = True
    render = render_terminal(out, tom="narrativo")
    assert "narrativa: possível generalização de escopo" in render


# --- v1.3.1: bloco de consensos_usados (revisão humana do MOVIMENTO 2) ---

def test_consensos_usados_renderizados_em_bloco_compacto():
    out = _output_completo_com_narrativa()
    out["consensos_usados"] = [
        {"propriedade": "ritmo lento", "grupos_de_origem": ["negativas", "positivas"],
         "temas_de_origem": ["ritmo"]},
    ]
    render = render_terminal(out, tom="narrativo")
    assert "Consensos do movimento 2:" in render
    assert "ritmo lento" in render
    assert "negativas, positivas" in render


def test_sem_consensos_usados_nao_gera_bloco():
    out = _output_completo_com_narrativa()
    out["consensos_usados"] = []
    render = render_terminal(out, tom="narrativo")
    assert "Consensos do movimento 2:" not in render


def test_consenso_suspeito_mostra_aviso():
    out = _output_completo_com_narrativa()
    out["narrativa_flags"]["consenso_suspeito"] = True
    render = render_terminal(out, tom="narrativo")
    assert "consensos_usados citou grupo/tema inexistente" in render


# ===========================================================================
# [v1.9.14, Entrega 2] O bloco global `eixos` no JSON de resultado (§4)
# ===========================================================================

def _bloco_eixos():
    return {"taxonomia_id": "ebab2667de74", "margem_lift_pp": 20,
            "contraste": "valorativo",
            "fonte_classificacao": {"arquivo": "x", "criterio": "y",
                                    "por_bucket": {}},
            "linhas": []}


def test_output_sem_classificacao_NAO_emite_a_chave_eixos():
    """Chave ausente distingue 'filme não classificado' de 'classificado e
    sem eixo' — a mesma política de `share_real` desde a v1.4.0."""
    out = render.build_output("cure", [], "2026-01-01", {}, 100)
    assert "eixos" not in out


def test_output_com_classificacao_carrega_o_bloco_inteiro():
    out = render.build_output("cure", [], "2026-01-01", {}, 100,
                              eixos=_bloco_eixos())
    assert out["eixos"]["contraste"] == "valorativo"
    assert out["eixos"]["taxonomia_id"] == "ebab2667de74"


def test_o_bloco_de_eixos_e_serializavel(tmp_path):
    out = render.build_output("cure", [], "2026-01-01", {}, 100,
                              eixos=_bloco_eixos())
    caminho = render.write_json(out, out_dir=tmp_path)
    assert json.loads(caminho.read_text(encoding="utf-8"))["eixos"]["margem_lift_pp"] == 20
