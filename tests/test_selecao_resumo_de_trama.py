"""Regra R2 da seleção: review que abre com `### ` é resumo de trama, não opinião.

Decisão do dono (2026-11-26). Medição que a sustenta: `scripts/medir_resumo_de_trama.py`
(11 reviews em 193 brutos, as 11 resumos de trama). O caso de teste obrigatório é a
review de `clebcinestats` em boogie-nights (18.735 caracteres, o filme inteiro contado
com o final, sem marca de spoiler).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from espectro24 import selecao as S
from espectro24.bruto import ReviewBruta, carregar

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "dados" / "bruto"
HIST = {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10, 2.5: 10, 3.0: 10, 3.5: 10, 4.0: 10, 4.5: 10, 5.0: 10}
LONGO = "opinião com bastante conteúdo " * 8     # > 150 caracteres


def _r(id_, nivel=1.0, texto=LONGO, spoiler=False):
    return ReviewBruta(id=id_, nivel=nivel, texto=texto, n_chars=len(texto),
                       spoiler_flag=spoiler, pagina_origem=1, url="", autor_hash="h",
                       truncada=False, texto_completo=True, data="2026-01-01")


def _ids(sel):
    return {r.id for b in sel.values() for n in b.niveis.values() for r in n.validas}


# --- o detector ----------------------------------------------------------

@pytest.mark.parametrize("texto", [
    "### Boogie Nights: Prazer Sem Limites — Resumo completo do filme (1997)",
    "### Casablanca (1942) — Michael Curtiz",
    "   ### com até três espaços de recuo",
    "\n### título depois de quebra de linha",
    "###\tcom tab",
])
def test_abre_com_titulo_h3_e_resumo(texto):
    assert S.e_resumo_de_trama(texto)


@pytest.mark.parametrize("texto", [
    "", None, "## título de nível 2",
    "#### título de nível 4",
    "###sem espaço depois",
    "opinião normal ### com marcador no meio",
    "#hashtag e mais texto",
    "    ### recuo de quatro espaços (bloco de código)",
    "Resumo completo do filme sem o cabeçalho",
])
def test_nao_e_resumo(texto):
    assert not S.e_resumo_de_trama(texto)


# --- a seleção -----------------------------------------------------------

def test_resumo_e_excluido_com_motivo_proprio_e_a_vaga_vai_para_a_proxima():
    rs = [_r("resumo", texto="### Filme (1999)\n" + LONGO * 40), _r("a"), _r("b")]
    sel = S.selecionar(rs, HIST, cota_por_bucket=1)
    assert _ids(sel) == {"a"}                      # a próxima na ordem de sempre
    nivel = sel["negativas"].niveis[1.0]
    assert nivel.motivos_descarte["resumo_de_trama"] == 1
    assert nivel.motivos_descarte["excedente_cota"] == 1       # "b"
    assert sum(nivel.motivos_descarte.values()) == nivel.n_brutas - nivel.n_validas


def test_a_chave_so_existe_quando_ha_resumo_no_nivel():
    sel = S.selecionar([_r("a"), _r("b")], HIST)
    assert all("resumo_de_trama" not in n.motivos_descarte
               for b in sel.values() for n in b.niveis.values())


def test_parametro_false_reproduz_a_selecao_anterior():
    rs = [_r("resumo", texto="### Filme\n" + LONGO), _r("a")]
    assert "resumo" in _ids(S.selecionar(rs, HIST, excluir_resumo_de_trama=False))
    assert "resumo" not in _ids(S.selecionar(rs, HIST))     # default de produção: exclui


def test_resumo_nao_entra_nem_pela_cascata():
    """A cascata só desce quando o degrau dá ZERO; um nível só com o resumo fica
    vazio em vez de relaxar para aceitá-lo."""
    rs = [_r("resumo", texto="### Filme\n" + LONGO)]
    sel = S.selecionar(rs, HIST)
    assert _ids(sel) == set()


def test_spoiler_tem_precedencia_na_discriminacao():
    rs = [_r("s", texto="### Filme\n" + LONGO, spoiler=True), _r("a")]
    n = S.selecionar(rs, HIST)["negativas"].niveis[1.0]
    assert n.motivos_descarte["spoiler"] == 1
    assert "resumo_de_trama" not in n.motivos_descarte


def test_filme_sem_resumo_tem_selecao_identica_com_e_sem_a_regra():
    """A regra não toca nenhum filme que não tenha o padrão: nem a seleção nem
    o schema do dict de descartes."""
    for slug in ("12-angry-men", "alien", "fight-club"):
        meta, rs = carregar(slug, raiz=BRUTO)
        if not rs:
            continue
        hist = {float(k): v for k, v in meta["histograma_bruto"].items()}
        orc = {float(k): v for k, v in (meta.get("orcamento_paginas_por_nivel") or {}).items()}
        com = S.selecionar(rs, hist, orcamento_paginas_por_nivel=orc)
        sem = S.selecionar(rs, hist, orcamento_paginas_por_nivel=orc, excluir_resumo_de_trama=False)
        assert [r.id for b in com.values() for n in b.niveis.values() for r in n.validas] == \
               [r.id for b in sem.values() for n in b.niveis.values() for r in n.validas], slug
        assert [n.motivos_descarte for b in com.values() for n in b.niveis.values()] == \
               [n.motivos_descarte for b in sem.values() for n in b.niveis.values()], slug


# --- o caso obrigatório: clebcinestats em boogie-nights ---------------------

def test_clebcinestats_era_selecionada_e_agora_e_excluida_por_resumo_de_trama():
    meta, rs = carregar("boogie-nights", raiz=BRUTO)
    hist = {float(k): v for k, v in meta["histograma_bruto"].items()}
    alvo = next(r for r in rs if "/clebcinestats/" in r.id)
    assert alvo.n_chars == 18735 and alvo.nivel == 1.0 and not alvo.spoiler_flag

    antes = S.selecionar(rs, hist, excluir_resumo_de_trama=False)
    depois = S.selecionar(rs, hist)
    assert alvo.id in _ids(antes)                  # nenhum filtro antigo a pegava
    assert alvo.id not in _ids(depois)
    assert depois["negativas"].niveis[1.0].motivos_descarte["resumo_de_trama"] == 1
    # o pool do nível esgotou: ninguém entra no lugar e a negativa fecha com 36
    assert antes["negativas"].n_final == 37 and depois["negativas"].n_final == 36
    assert _ids(antes) - _ids(depois) == {alvo.id}
    assert _ids(depois) - _ids(antes) == set()
    # as outras reviews longas (ensaios) continuam: o tamanho NÃO é o critério
    assert any(r.n_chars > 7000 and r.id in _ids(depois) for r in rs)


def test_os_onze_resumos_do_corpus_abrem_com_h3_e_nenhum_ensaio_cai():
    """Trava a medição: a regra tira exatamente os resumos conhecidos."""
    achados = []
    for d in sorted(BRUTO.iterdir()):
        if (d / "reviews.jsonl").exists():
            _, rs = carregar(d.name, raiz=BRUTO)
            achados += [(d.name, r.n_chars) for r in rs if S.e_resumo_de_trama(r.texto)]
    assert len(achados) == 11
    assert all(n >= 13000 for _, n in achados)
    assert {s for s, _ in achados} >= {"boogie-nights", "casablanca", "its-a-wonderful-life",
                                       "modern-times", "seven-samurai", "rear-window"}
