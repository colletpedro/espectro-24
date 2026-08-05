"""CLI --tom (v1.2.0): estruturado NÃO chama o narrador; narrativo/ambos sim.

Usa o caminho --reuse-synthesis (carrega um JSON existente) para exercitar a
decisão de narração sem tocar em rede/coleta. `narrate_output` é mockado.
"""
import json

import pytest

from espectro24 import cli
from espectro24.models import (
    BucketResult,
    EdicaoResult,
    LevelResult,
    NarrativaResult,
    Review,
    Tema,
)
from espectro24.render import build_output


def _escreve_json(out_dir, slug="cure"):
    lvl = LevelResult(4.0, 150, 1, 3, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"v{i}", rating=4.0, text="x" * 200,
                          truncated=False, full_text_url=None, spoiler=False,
                          full_text="x" * 200) for i in range(3)]
    b = BucketResult(nome="positivas", alvo=30, modo="completo", niveis=[lvl],
                     temas=[Tema("ritmo", 2, 3, "grupo achou o ritmo bom")],
                     observacao_geral="as reviews positivas destacam o ritmo")
    out = build_output(slug, [b], "2026-01-01", {}, 42)
    (out_dir / f"{slug}.json").write_text(json.dumps(out, ensure_ascii=False),
                                          encoding="utf-8")


@pytest.fixture
def _iso_env(monkeypatch):
    # isola do .env real e fixa uma chave fake. v1.8.0: DEEPSEEK_API_KEY,
    # não mais GEMINI_API_KEY — o provider default do CLI (sem --provider)
    # passou a ser "deepseek" (DEFAULT_PROVIDER, config.py); narrate_output/
    # editar_narrativa são mockados nestes testes, então só a PRESENÇA da
    # chave do provider resolvido importa, não qual provider é.
    monkeypatch.setattr(cli, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def _mock_narrate(monkeypatch, consensos_usados=None):
    calls = []

    def fake(output, model=None, provider=None):
        calls.append(output)
        return NarrativaResult(texto="PROSA_MOCK", idioma_invalido=False,
                               escopo_suspeito=False, aspas_removidas=False,
                               consensos_usados=consensos_usados or [])
    monkeypatch.setattr(cli, "narrate_output", fake)
    _mock_editor(monkeypatch)   # v1.6.0: o CLI chama [E2] logo após o narrador
    return calls


def _mock_editor(monkeypatch, texto=None, descartada=False):
    """v1.6.0: mocka o passe de edição [E2]. Por default é IDENTIDADE — o
    texto do narrador passa intacto —, para que os testes de --tom continuem
    medindo só a decisão de narrar."""
    calls = []

    def fake_editar(narrativa_result, protegidos, output=None, model=None,
                    provider=None):
        calls.append((narrativa_result.texto, protegidos))
        bruto = narrativa_result.texto
        return EdicaoResult(texto=texto if texto is not None else bruto,
                            texto_bruto=bruto, edicao_descartada=descartada)

    monkeypatch.setattr(cli, "editar_narrativa", fake_editar)
    monkeypatch.setattr(cli, "montar_protegidos", lambda res, out: [])
    return calls


def test_tom_estruturado_nao_chama_narrador(tmp_path, monkeypatch, _iso_env, capsys):
    _escreve_json(tmp_path)
    calls = _mock_narrate(monkeypatch)
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "estruturado"])
    assert calls == []                       # narrador NÃO chamado
    out = capsys.readouterr().out
    assert "mencionado em" in out            # estruturado renderizado
    assert "PROSA_MOCK" not in out


def test_tom_narrativo_chama_narrador_uma_vez(tmp_path, monkeypatch, _iso_env, capsys):
    _escreve_json(tmp_path)
    calls = _mock_narrate(monkeypatch)
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "narrativo"])
    assert len(calls) == 1                   # narrador chamado 1x
    out = capsys.readouterr().out
    assert "PROSA_MOCK" in out
    assert "mencionado em" not in out        # temas escondidos no narrativo


def test_tom_ambos_chama_narrador_e_persiste_no_json(tmp_path, monkeypatch, _iso_env, capsys):
    _escreve_json(tmp_path)
    calls = _mock_narrate(monkeypatch)
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "ambos"])
    assert len(calls) == 1
    out = capsys.readouterr().out
    assert "mencionado em" in out and "PROSA_MOCK" in out
    # narrativa persistida no JSON
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["narrativa"] == "PROSA_MOCK"
    assert salvo["narrativa_flags"]["falhou"] is False


def test_reuse_sem_json_existente_falha(tmp_path, monkeypatch, _iso_env):
    with pytest.raises(SystemExit):
        cli.main(["--slug", "inexistente", "--reuse-synthesis",
                  "--out-dir", str(tmp_path), "--tom", "narrativo"])


# --- v1.3.0: ficha TMDB é aditiva — sucesso e falha não quebram o pipeline ---

def test_ficha_sucesso_entra_no_json(tmp_path, monkeypatch, _iso_env, capsys):
    _escreve_json(tmp_path)
    _mock_narrate(monkeypatch)
    ficha_mock = {"titulo": "Cure", "sinopse_oficial": "s", "sinopse_fallback_en": False,
                 "generos": ["Terror"], "duracao_min": 111, "diretor": "Kiyoshi Kurosawa",
                 "ano": 1997, "fonte": "tmdb"}
    monkeypatch.setattr(cli, "buscar_ficha", lambda *a, **k: (ficha_mock, None, None))
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "estruturado"])
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["ficha"]["diretor"] == "Kiyoshi Kurosawa"


def test_ficha_falha_da_api_nao_quebra_pipeline(tmp_path, monkeypatch, _iso_env, capsys):
    _escreve_json(tmp_path)
    _mock_narrate(monkeypatch)
    monkeypatch.setattr(cli, "buscar_ficha",
                        lambda *a, **k: (None, "TMDB indisponível (erro simulado) — ficha pulada.", None))
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "estruturado"])
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["ficha"] is None
    err = capsys.readouterr().err
    assert "Ficha TMDB" in err


# --- v1.3.1: consensos_usados persiste no JSON e aparece no render ---

def test_consensos_usados_persiste_no_json_e_renderiza(tmp_path, monkeypatch, _iso_env, capsys):
    _escreve_json(tmp_path)
    consensos = [{"propriedade": "ritmo lento", "grupos_de_origem": ["negativas", "positivas"],
                 "temas_de_origem": ["ritmo"]}]
    _mock_narrate(monkeypatch, consensos_usados=consensos)
    monkeypatch.setattr(cli, "buscar_ficha", lambda *a, **k: (None, None, None))
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "narrativo"])
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["consensos_usados"] == consensos
    assert salvo["narrativa_flags"]["consenso_suspeito"] is False
    out = capsys.readouterr().out
    assert "Consensos do movimento 2:" in out
    assert "ritmo lento" in out


def test_no_ficha_pula_a_busca(tmp_path, monkeypatch, _iso_env, capsys):
    _escreve_json(tmp_path)
    _mock_narrate(monkeypatch)
    chamou = []
    monkeypatch.setattr(cli, "buscar_ficha", lambda *a, **k: chamou.append(1) or (None, None, None))
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "estruturado", "--no-ficha"])
    assert chamou == []
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["ficha"] is None


# =====================================================================
# v1.7.0 (Tarefa 1) — resolução de ano: slug -> Letterboxd -> sem ficha
# =====================================================================
# Defeito real corrigido: `espectro24 --slug cure` sem --ano resolvia no
# TMDB para o filme errado (nenhum ano para desambiguar). Cobre a cadeia
# INTEIRA de resolução tal como o CLI a executa, não só `ficha.py` isolado.

def test_ano_do_slug_e_usado_direto_sem_letterboxd(tmp_path, monkeypatch, _iso_env):
    """slug com sufixo -YYYY: ano vem do slug, resolver_ano_letterboxd nunca
    é chamado (nenhuma requisição extra)."""
    _escreve_json(tmp_path, slug="the-invite-2026")
    _mock_narrate(monkeypatch)
    chamado = []
    monkeypatch.setattr(cli, "resolver_ano_letterboxd",
                        lambda *a, **k: chamado.append(1))
    recebido = {}

    def fake_buscar(titulo, ano, cache_dir, ano_fonte=None, **k):
        recebido["ano"] = ano
        recebido["ano_fonte"] = ano_fonte
        return None, None, None
    monkeypatch.setattr(cli, "buscar_ficha", fake_buscar)
    cli.main(["--slug", "the-invite-2026", "--reuse-synthesis",
              "--out-dir", str(tmp_path), "--tom", "estruturado"])
    assert chamado == []
    assert recebido == {"ano": 2026, "ano_fonte": "slug"}


def test_ano_ausente_no_slug_cai_para_letterboxd(tmp_path, monkeypatch, _iso_env):
    """slug sem ano ('cure'): resolver_ano_letterboxd é chamado, e o ano que
    ele devolve é o usado na busca TMDB — é o teste da Tarefa 1 (o defeito
    real: sem isso, a busca ia sem ano e resolvia para o filme errado)."""
    _escreve_json(tmp_path, slug="cure")
    _mock_narrate(monkeypatch)
    monkeypatch.setattr(cli, "resolver_ano_letterboxd", lambda fetcher, slug: 1997)
    recebido = {}

    def fake_buscar(titulo, ano, cache_dir, ano_fonte=None, **k):
        recebido["titulo"] = titulo
        recebido["ano"] = ano
        recebido["ano_fonte"] = ano_fonte
        ficha = {"titulo": "Cure", "diretor": "Kiyoshi Kurosawa", "ano": 1997,
                "ano_fonte": ano_fonte, "fonte": "tmdb"}
        return ficha, None, None
    monkeypatch.setattr(cli, "buscar_ficha", fake_buscar)
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "estruturado"])
    assert recebido == {"titulo": "cure", "ano": 1997, "ano_fonte": "letterboxd"}
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["ficha"]["diretor"] == "Kiyoshi Kurosawa"


def test_ano_indisponivel_em_lugar_nenhum_pula_a_busca_com_flag(tmp_path, monkeypatch, _iso_env):
    """Tarefa 1.1c: sem ano nem no slug nem no Letterboxd, NÃO busca a ficha
    (melhor nenhuma do que a do filme errado) — e o motivo fica registrado."""
    _escreve_json(tmp_path, slug="cure")
    _mock_narrate(monkeypatch)
    monkeypatch.setattr(cli, "resolver_ano_letterboxd", lambda fetcher, slug: None)
    chamou = []
    monkeypatch.setattr(cli, "buscar_ficha", lambda *a, **k: chamou.append(1))
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "estruturado"])
    assert chamou == []                    # buscar_ficha nunca chamado
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["ficha"] is None
    assert salvo["ficha_indisponivel"] == "ano_desconhecido"


def test_ficha_descartada_por_ano_divergente_fica_registrada_no_json(tmp_path, monkeypatch, _iso_env):
    """Tarefa 1.2: quando `buscar_ficha` descarta por divergência de ano, o
    CLI persiste `ficha_descartada` no JSON (não só imprime o aviso)."""
    _escreve_json(tmp_path, slug="cure")
    _mock_narrate(monkeypatch)
    monkeypatch.setattr(cli, "resolver_ano_letterboxd", lambda fetcher, slug: 1997)
    descarte = {"motivo": "ano_divergente", "esperado": 1997, "recebido": 2026}
    monkeypatch.setattr(cli, "buscar_ficha",
                        lambda *a, **k: (None, "TMDB: ficha descartada — ano divergente.", descarte))
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "estruturado"])
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["ficha"] is None
    assert salvo["ficha_descartada"] == descarte


# =====================================================================
# v1.8.0 (Tarefa 2/4) — editor [E2] DESLIGADO por padrão (EDITOR_ATIVO)
# =====================================================================

def test_editor_desativado_por_padrao_nao_chama_o_llm_do_editor(
        tmp_path, monkeypatch, _iso_env, capsys):
    """Sem --com-editor: `editar_narrativa` NUNCA é chamado — 0 chamadas
    LLM além do narrador —, e o pipeline publica a narrativa do narrador
    tal como está (mesmo texto em `narrativa` e `narrativa_bruta`)."""
    _escreve_json(tmp_path)
    calls_narrar = _mock_narrate(monkeypatch)   # também mocka editar_narrativa
    import espectro24.cli as cli_mod
    chamou_editor = []
    original = cli_mod.editar_narrativa
    def _falha_se_chamado(*a, **k):
        chamou_editor.append(1)
        return original(*a, **k)
    monkeypatch.setattr(cli_mod, "editar_narrativa", _falha_se_chamado)

    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "ambos"])

    assert len(calls_narrar) == 1              # narrador chamado normalmente
    assert chamou_editor == []                 # editor NUNCA chamado
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["narrativa"] == "PROSA_MOCK"
    assert salvo["narrativa_bruta"] == "PROSA_MOCK"   # bruta == final, sem edição
    assert salvo["edicao_flags"] == {"editor_desativado": True}
    out = capsys.readouterr().out
    assert "DESLIGADA por padrão" in out


def test_com_editor_reativa_o_passe_de_edicao(tmp_path, monkeypatch, _iso_env, capsys):
    """--com-editor liga o editor de volta — mesmo comportamento de antes
    da v1.8.0 (editar_narrativa É chamado, 1 chamada LLM a mais)."""
    _escreve_json(tmp_path)
    calls_narrar = _mock_narrate(monkeypatch)
    import espectro24.cli as cli_mod
    calls_editor = []
    def fake_editar(narrativa_result, protegidos, output=None, model=None,
                    provider=None):
        calls_editor.append(1)
        from espectro24.models import EdicaoResult
        return EdicaoResult(texto=narrativa_result.texto,
                            texto_bruto=narrativa_result.texto,
                            edicao_descartada=False)
    monkeypatch.setattr(cli_mod, "editar_narrativa", fake_editar)

    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "ambos", "--com-editor"])

    assert len(calls_narrar) == 1
    assert len(calls_editor) == 1
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert "editor_desativado" not in salvo["edicao_flags"]
    assert salvo["edicao_flags"]["edicao_descartada"] is False


def test_no_edicao_vence_mesmo_com_com_editor(tmp_path, monkeypatch, _iso_env):
    """--no-edicao sempre desliga, mesmo se --com-editor também foi
    passado — desempate explícito documentado no CLI."""
    _escreve_json(tmp_path)
    _mock_narrate(monkeypatch)
    import espectro24.cli as cli_mod
    chamou_editor = []
    monkeypatch.setattr(cli_mod, "editar_narrativa",
                        lambda *a, **k: chamou_editor.append(1))

    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "ambos", "--com-editor", "--no-edicao"])

    assert chamou_editor == []
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["edicao_flags"] == {"editor_desativado": True}
