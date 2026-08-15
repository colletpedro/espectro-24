"""CLI --tom (v1.2.0): estruturado NÃO chama o narrador; narrativo/ambos sim.

Usa o caminho --reuse-synthesis (carrega um JSON existente) para exercitar a
decisão de narração sem tocar em rede/coleta. `narrate_output` é mockado.

O editor [E2] foi APOSENTADO na v1.9.10 (ver SPEC.md) — o CLI não o chama
mais em caminho nenhum; os testes que exerciam `--no-edicao`/`--com-editor`
foram removidos junto com as flags. `EdicaoResult` mora agora em
`experimentos-editor-e2-arquivado/editor.py`.
"""
import json

import pytest

from espectro24 import cli
from espectro24.models import (
    BucketResult,
    LevelResult,
    NarrativaBriefingResult,
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
    # isola do .env real e fixa chaves fake. v1.9.11: AS DUAS, porque sem
    # `--provider` cada estágio usa o seu (`PROVIDER_POR_ESTAGIO`) —
    # classificação em DeepSeek, narrativa em Gemini — e o CLI agora checa a
    # chave de CADA estágio que vai rodar, antes da coleta. Até a v1.9.10
    # bastava a do DeepSeek porque o default do argparse forçava tudo nele
    # (o defeito que esta versão corrige).
    monkeypatch.setattr(cli, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def _mock_narrate(monkeypatch, verificacao=None):
    """v1.9.11: o CLI chama `narrador.narrar` (briefing + best-of-3), não
    mais `narrate_output`. O dublê devolve o mesmo formato de resultado."""
    calls = []

    def fake(output, provider=None, model=None):
        calls.append(output)
        return NarrativaBriefingResult(
            texto="PROSA_MOCK",
            escolha={"indice": 0, "motivo": "melhor_entre_limpos",
                     "criterio_decisivo": "ritmo", "candidatos": []},
            verificacao=verificacao or {"n_flags": 0, "n_resenha_speak": 0},
            candidatos=["PROSA_MOCK"], provider="gemini", modelo="m",
            n_chamadas=3, uso={"prompt_tokens": 1, "completion_tokens": 2},
            latencia_s=1.0)
    monkeypatch.setattr(cli, "narrar", fake)
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
    # v1.9.11: `narrativa_flags` (as flags DECLARADAS pelo narrador antigo)
    # dá lugar às flags MECÂNICAS + ao registro da escolha do best-of-3.
    assert "narrativa_flags" not in salvo
    assert salvo["verificacao_narrativa"]["n_flags"] == 0
    assert salvo["narrativa_selecao"]["motivo"] == "melhor_entre_limpos"
    assert salvo["narrativa_selecao"]["n_chamadas"] == 3


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

def test_telemetria_do_best_of_3_persiste_e_renderiza(tmp_path, monkeypatch,
                                                     _iso_env, capsys):
    """v1.9.11: `consensos_usados` era DECLARADO pelo narrador antigo (o
    teste correspondente foi para o arquivo dele). Sob briefing o narrador
    não declara nada — a telemetria que importa é a da ESCOLHA."""
    _escreve_json(tmp_path)
    _mock_narrate(monkeypatch, verificacao={"n_flags": 0, "n_resenha_speak": 0,
                                            "n_paragrafos": 5})
    monkeypatch.setattr(cli, "buscar_ficha", lambda *a, **k: (None, None, None))
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "narrativo"])
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["narrativa_selecao"]["indice_escolhido"] == 0
    assert salvo["narrativa_selecao"]["criterio_decisivo"] == "ritmo"
    assert salvo["verificacao_narrativa"]["n_paragrafos"] == 5
    out = capsys.readouterr().out
    assert "best-of" in out.lower() or "candidato" in out.lower()


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
# v1.9.10 — editor [E2] APOSENTADO: o CLI não o chama em caminho nenhum.
# =====================================================================

def test_editor_nao_e_mais_chamado_e_narrativa_e_a_do_narrador(
        tmp_path, monkeypatch, _iso_env, capsys):
    """Regressão da aposentadoria: `narrativa` é exatamente o texto do
    narrador, sem `edicao_flags`/`narrativa_bruta` — o mesmo formato que o
    antigo caminho "editor desligado" já publicava."""
    _escreve_json(tmp_path)
    _mock_narrate(monkeypatch)
    cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
              "--tom", "ambos"])
    salvo = json.loads((tmp_path / "cure.json").read_text(encoding="utf-8"))
    assert salvo["narrativa"] == "PROSA_MOCK"
    assert "edicao_flags" not in salvo
    assert "narrativa_bruta" not in salvo


def test_flags_de_edicao_nao_existem_mais(tmp_path, monkeypatch, _iso_env):
    """`--no-edicao`/`--com-editor` foram removidas — não há mais o que
    ligar ou desligar."""
    _escreve_json(tmp_path)
    _mock_narrate(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
                  "--tom", "ambos", "--no-edicao"])
    with pytest.raises(SystemExit):
        cli.main(["--slug", "cure", "--reuse-synthesis", "--out-dir", str(tmp_path),
                  "--tom", "ambos", "--com-editor"])
