"""[v1.9.5] Estratificação E1 da seleção por profundidade — SPEC §3[C2].

Escritos ANTES da mudança em `selecao.py`.

A garantia que mais importa está em
`test_sem_orcamento_o_comportamento_e_identico_ao_da_v194`: a estratificação é
uma ADIÇÃO, não uma substituição. Sem `orcamento_paginas_por_nivel`, a seleção
tem de se comportar exatamente como antes — é isso que mantém o caminho
offline e os testes anteriores válidos.
"""
from __future__ import annotations

from espectro24.bruto import ReviewBruta
from espectro24.selecao import faixas_de_profundidade, selecionar


def _rev(nivel: float, pagina: int, i: int, n_chars: int = 300) -> ReviewBruta:
    return ReviewBruta(
        id=f"v{nivel}-{pagina}-{i}", nivel=nivel, texto="x" * n_chars,
        n_chars=n_chars, spoiler_flag=False, pagina_origem=pagina,
        url="", autor_hash="h", truncada=False, texto_completo=True,
        data="2026-01-01")


def _corpus(niveis, paginas, por_pagina=12, n_chars=300):
    """Material farto: `por_pagina` reviews em cada página de cada nível."""
    return [_rev(n, p, i, n_chars)
            for n in niveis for p in paginas for i in range(por_pagina)]


# orçamento 16 → n_raso 12, n_profundo 4
ORC = {n: 16 for n in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)}
HIST = {n: 1000 for n in ORC}


# --- as faixas ------------------------------------------------------------

def test_faixas_sao_estruturais_raso_metade_metade_e_profundo():
    """1..6 · 7..12 · >12, para n_raso=12. Não é tercil da distribuição
    observada: é a estrutura que a coleta já produz."""
    pool = [_rev(4.0, p, 0) for p in (1, 6, 7, 12, 13, 200)]
    f1, f2, f3 = faixas_de_profundidade(pool, n_raso=12)
    assert [r.pagina_origem for r in f1] == [1, 6]
    assert [r.pagina_origem for r in f2] == [7, 12]
    assert [r.pagina_origem for r in f3] == [13, 200]


def test_faixas_com_n_raso_1():
    f1, f2, f3 = faixas_de_profundidade([_rev(4.0, p, 0) for p in (1, 2, 3)],
                                        n_raso=1)
    assert [r.pagina_origem for r in f1] == [1]
    assert [r.pagina_origem for r in f2] == []
    assert [r.pagina_origem for r in f3] == [2, 3]


# --- regressão: sem orçamento, nada muda ----------------------------------

def test_sem_orcamento_o_comportamento_e_identico_ao_da_v194():
    """A estratificação é ADIÇÃO, não substituição."""
    todas = _corpus([2.0], range(1, 30))
    sem = selecionar(todas, HIST)
    ids_sem = [r.id for r in sem["negativas"].niveis[2.0].validas]
    # a seleção antiga é `pool[:n]` na ordem (pagina_origem, ordem no jsonl)
    assert ids_sem == sorted(ids_sem, key=lambda i: (
        int(i.split("-")[1]), int(i.split("-")[2])))


def test_com_orcamento_a_amostra_alcanca_o_profundo():
    todas = _corpus([2.0], range(1, 30))
    sem = selecionar(todas, HIST)
    com = selecionar(todas, HIST, orcamento_paginas_por_nivel=ORC)
    p_sem = max(r.pagina_origem for r in sem["negativas"].niveis[2.0].validas)
    p_com = max(r.pagina_origem for r in com["negativas"].niveis[2.0].validas)
    assert p_com > p_sem


# --- a cota é respeitada ---------------------------------------------------

def test_cota_do_bucket_nao_muda_com_estratificacao():
    todas = _corpus([0.5, 1.0, 1.5, 2.0], range(1, 30))
    sem = selecionar(todas, HIST)
    com = selecionar(todas, HIST, orcamento_paginas_por_nivel=ORC)
    for nome in sem:
        assert com[nome].n_final == sem[nome].n_final, nome


def test_composicao_por_nivel_e_preservada():
    """A alocação proporcional por nível (§3[C1]) tem PRECEDÊNCIA — a
    estratificação redistribui DENTRO da cota de cada nível, nunca entre
    níveis."""
    todas = _corpus([0.5, 1.0, 1.5, 2.0], range(1, 30))
    sem = selecionar(todas, HIST)
    com = selecionar(todas, HIST, orcamento_paginas_por_nivel=ORC)
    assert com["negativas"].composicao_atingida == \
        sem["negativas"].composicao_atingida


def test_bucket_que_fecha_hoje_continua_fechando():
    todas = _corpus([0.5, 1.0, 1.5, 2.0], range(1, 30))
    com = selecionar(todas, HIST, orcamento_paginas_por_nivel=ORC)
    assert com["negativas"].n_final == 40


# --- quem cede quando os dois critérios competem ---------------------------

def test_cota_de_nivel_menor_que_3_cede_para_a_alocacao():
    """9% dos pares (bucket, nível) têm cota < 3 e não cabem em três faixas.
    Aí a estratificação CEDE: o resultado é idêntico ao da seleção antiga."""
    # histograma desbalanceado: 2,0★ domina, os outros ficam no piso de 2
    hist = {0.5: 1, 1.0: 1, 1.5: 1, 2.0: 100_000,
            2.5: 1000, 3.0: 1000, 3.5: 1000, 4.0: 1000, 4.5: 1000, 5.0: 1000}
    todas = _corpus([0.5, 1.0, 1.5, 2.0], range(1, 30))
    sem = selecionar(todas, hist)
    com = selecionar(todas, hist, orcamento_paginas_por_nivel=ORC)
    for n in (0.5, 1.0, 1.5):
        alvo = sem["negativas"].niveis[n].n_alvo
        assert alvo < 3
        assert [r.id for r in com["negativas"].niveis[n].validas] == \
               [r.id for r in sem["negativas"].niveis[n].validas]


def test_faixa_vazia_devolve_as_vagas_as_outras():
    """Nível sem material profundo nenhum: as vagas da faixa 3 voltam ao
    raso e a cota fecha igual."""
    todas = _corpus([2.0], range(1, 13))     # só bloco raso
    com = selecionar(todas, HIST, orcamento_paginas_por_nivel=ORC)
    sem = selecionar(todas, HIST)
    assert com["negativas"].n_final == sem["negativas"].n_final


def test_material_escasso_nao_quebra():
    todas = [_rev(2.0, 1, 0), _rev(2.0, 200, 1)]
    com = selecionar(todas, HIST, orcamento_paginas_por_nivel=ORC)
    assert com["negativas"].n_final == 2


def test_bucket_vazio_nao_quebra():
    com = selecionar([], HIST, orcamento_paginas_por_nivel=ORC)
    assert all(b.n_final == 0 for b in com.values())


# --- o efeito que justifica a mudança --------------------------------------

def test_estratificacao_aumenta_o_uso_do_material_profundo():
    todas = _corpus([0.5, 1.0, 1.5, 2.0], range(1, 30))
    def frac_profunda(sel):
        vs = [r for n in sel["negativas"].niveis
              for r in sel["negativas"].niveis[n].validas]
        return sum(1 for r in vs if r.pagina_origem > 12) / len(vs)
    sem = frac_profunda(selecionar(todas, HIST))
    com = frac_profunda(selecionar(todas, HIST,
                                   orcamento_paginas_por_nivel=ORC))
    assert com > sem
    assert com >= 0.25
