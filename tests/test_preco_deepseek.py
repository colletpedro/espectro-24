"""[2026-09-18] Preço do DeepSeek: a tabela V4.1-Flash e a janela de pico.

O que está sob teste, e por quê:

1. os NÚMEROS da tabela. As constantes antigas (14/08) reportavam 38% do custo
   real no pico — o lote noturno de 18/09 calculou US$0,66 e custou US$1,75,
   e o saldo zerou duas vezes sem aviso. Estes valores são a tabela LIDA em
   `preco.TABELA_VERIFICADA_EM`; se o provider mudar o preço, este teste deve
   falhar junto com a atualização de `preco.py` — não é para "afrouxar", é
   para lembrar que o número tem validade;
2. a JANELA (seg-sex, 01-04 e 06-10 UTC), nas fronteiras, e contra um oráculo
   INDEPENDENTE: a página em chinês dá a mesma regra em horário de Pequim
   (9-12 e 14-18, UTC+8), e as duas têm de concordar em todos os instantes;
3. `sem horário → PICO`: superestimar é o lado seguro;
4. nenhum script volta a definir `PRECO_*` com literal numérico.
"""
from __future__ import annotations

import ast
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import preco as P  # noqa: E402

UTC = timezone.utc


def _utc(ano, mes, dia, h=0, m=0, s=0):
    return datetime(ano, mes, dia, h, m, s, tzinfo=UTC)


# --- 1. a tabela --------------------------------------------------------------

def test_a_tabela_e_a_v41_flash_lida_em_2026_09_18():
    assert (P.PICO.entrada_miss, P.PICO.entrada_hit, P.PICO.saida) == (
        0.30, 0.006, 1.20)
    assert (P.FORA_DE_PICO.entrada_miss, P.FORA_DE_PICO.entrada_hit,
            P.FORA_DE_PICO.saida) == (0.15, 0.003, 0.60)
    assert P.TABELA_VIGENTE_DESDE == date(2026, 9, 10)
    assert P.TABELA_VERIFICADA_EM == date(2026, 9, 18)


def test_fora_de_pico_e_metade_do_pico_em_toda_a_tabela():
    """A regra da própria página (`Off-peak rates are half of the peak
    rates`): se um dos três números for digitado errado, este acusa."""
    assert P.FORA_DE_PICO.entrada_miss * 2 == pytest.approx(P.PICO.entrada_miss)
    assert P.FORA_DE_PICO.entrada_hit * 2 == pytest.approx(P.PICO.entrada_hit)
    assert P.FORA_DE_PICO.saida * 2 == pytest.approx(P.PICO.saida)


def test_o_custo_de_um_milhao_de_cada_tipo_de_token():
    uso = {"cache_miss_tokens": 1_000_000, "cache_hit_tokens": 1_000_000,
           "completion_tokens": 1_000_000}
    assert P.custo_usd(uso, _utc(2026, 9, 18, 8)) == pytest.approx(1.506)   # pico
    assert P.custo_usd(uso, _utc(2026, 9, 20, 8)) == pytest.approx(0.753)   # sáb


def test_o_lote_noturno_de_18_09_custa_1_75_e_nao_0_66():
    """O incidente, com os tokens MEDIDOS do passe 1 (6.559 chamadas, rodou
    às 08:48-09:04 UTC de uma sexta: pico). Com as constantes velhas dava
    US$0,3020; o real é 2,6× isso."""
    uso = {"cache_miss_tokens": 1_543_218, "cache_hit_tokens": 6_505_856,
           "completion_tokens": 241_942}
    velho = (uso["cache_miss_tokens"] * 0.14 + uso["cache_hit_tokens"] * 0.0028
             + uso["completion_tokens"] * 0.28) / 1_000_000
    real = P.custo_usd(uso, _utc(2026, 9, 18, 8, 50))
    assert velho == pytest.approx(0.3020, abs=1e-4)
    assert real == pytest.approx(0.7923, abs=1e-4)
    assert real / velho > 2.5


def test_uso_vazio_ou_ausente_custa_zero():
    assert P.custo_usd(None) == 0.0
    assert P.custo_usd({}) == 0.0


# --- 2. a janela --------------------------------------------------------------

# 2026-09-18 é SEXTA; 09-19 sábado; 09-20 domingo; 09-21 segunda.
@pytest.mark.parametrize("quando, pico", [
    (_utc(2026, 9, 18, 0, 59, 59), False),
    (_utc(2026, 9, 18, 1, 0, 0), True),        # início inclusivo
    (_utc(2026, 9, 18, 3, 59, 59), True),
    (_utc(2026, 9, 18, 4, 0, 0), False),       # fim exclusivo
    (_utc(2026, 9, 18, 5, 59, 59), False),
    (_utc(2026, 9, 18, 6, 0, 0), True),
    (_utc(2026, 9, 18, 9, 59, 59), True),
    (_utc(2026, 9, 18, 10, 0, 0), False),
    (_utc(2026, 9, 18, 23, 59, 59), False),
    (_utc(2026, 9, 19, 2, 0, 0), False),       # sábado dentro do horário
    (_utc(2026, 9, 19, 8, 0, 0), False),
    (_utc(2026, 9, 20, 8, 0, 0), False),       # domingo
    (_utc(2026, 9, 21, 1, 0, 0), True),        # segunda
    (_utc(2026, 9, 16, 5, 57, 49), False),     # início do lote de 44 (quarta)
    (_utc(2026, 9, 16, 6, 30, 0), True),       # ...e o resto dele
])
def test_fronteiras_da_janela(quando, pico):
    assert P.em_pico(quando) is pico


def test_o_fuso_e_convertido_para_utc():
    brt = timezone(timedelta(hours=-3))
    assert P.em_pico(datetime(2026, 9, 18, 3, 0, tzinfo=brt)) is True    # 06:00Z
    assert P.em_pico(datetime(2026, 9, 18, 7, 0, tzinfo=brt)) is False   # 10:00Z


def test_o_dia_da_semana_e_o_do_utc_nao_o_do_fuso_local():
    """Sexta 22:00 em BRT já é sábado 01:00Z: fora de pico."""
    brt = timezone(timedelta(hours=-3))
    assert P.em_pico(datetime(2026, 9, 18, 22, 0, tzinfo=brt)) is False


def test_datetime_ingenuo_e_recusado_por_ser_ambiguo():
    with pytest.raises(ValueError, match="sem fuso"):
        P.em_pico(datetime(2026, 9, 18, 8, 0))


def test_a_janela_concorda_com_a_regra_em_horario_de_pequim_em_toda_a_semana():
    """Oráculo independente. A página em chinês dá o pico como segunda a sexta,
    9:00-12:00 e 14:00-18:00 em Pequim (UTC+8). Varre uma semana inteira de 5
    em 5 minutos: a regra em UTC e a de Pequim precisam dar a mesma resposta em
    TODOS os instantes — inclusive a virada do dia, onde os dias da semana
    poderiam divergir."""
    pequim = timezone(timedelta(hours=8))

    def pico_em_pequim(dt):
        local = dt.astimezone(pequim)
        if local.weekday() > 4:
            return False
        minuto = local.hour * 60 + local.minute
        return 9 * 60 <= minuto < 12 * 60 or 14 * 60 <= minuto < 18 * 60

    t, fim, n = _utc(2026, 9, 14, 0, 0), _utc(2026, 9, 21, 0, 0), 0
    while t < fim:
        assert P.em_pico(t) == pico_em_pequim(t), t.isoformat()
        t += timedelta(minutes=5)
        n += 1
    assert n == 7 * 24 * 12


def test_sem_horario_o_preco_e_o_de_pico():
    """Pior caso: superestimar é o lado seguro — o erro que zerou o saldo foi
    o de SUBESTIMAR."""
    assert P.preco_em(None) is P.PICO
    uso = {"cache_miss_tokens": 1000, "completion_tokens": 100}
    assert P.custo_usd(uso) == P.custo_usd(uso, _utc(2026, 9, 18, 8))
    assert P.custo_usd(uso) == pytest.approx(2 * P.custo_usd(
        uso, _utc(2026, 9, 20, 8)))


# --- agregação de registros ---------------------------------------------------

def test_cada_registro_e_cobrado_no_preco_do_seu_instante():
    uso = {"cache_miss_tokens": 1_000_000}
    registros = [
        {"uso": uso, "ts": "2026-09-18T08:00:00+00:00"},   # pico    0,30
        {"uso": uso, "ts": "2026-09-19T08:00:00+00:00"},   # sábado  0,15
        {"uso": uso},                                       # sem ts  0,30
        {"uso": uso, "ts": "lixo"},                         # ilegível → pico
        {"uso": uso, "provider": "gemini"},                 # outro provider: fora
    ]
    ag = P.custo_de_registros(registros)
    assert ag.custo_usd == pytest.approx(0.30 + 0.15 + 0.30 + 0.30)
    assert ag.n_chamadas == 4
    assert ag.n_sem_horario == 2
    assert ag.custo_pico_usd == pytest.approx(0.90)
    assert ag.custo_fora_de_pico_usd == pytest.approx(0.15)


def test_o_ts_gravado_pelo_registro_e_lido_de_volta_como_utc_com_fuso():
    ts = P.agora_utc_iso()
    assert datetime.fromisoformat(ts).tzinfo is not None
    ag = P.custo_de_registros([{"uso": {"completion_tokens": 10}, "ts": ts}])
    assert ag.n_sem_horario == 0


# --- validade -----------------------------------------------------------------

def test_a_tabela_avisa_quando_passa_da_validade():
    assert P.aviso_de_validade(date(2026, 9, 18)) is None
    assert P.aviso_de_validade(date(2026, 10, 18)) is None            # 30 dias
    aviso = P.aviso_de_validade(date(2026, 10, 19))                   # 31 dias
    assert aviso and "2026-09-18" in aviso and "quick_start/pricing/" in aviso


# --- 4. ninguém volta a redefinir preço --------------------------------------

def _atribuicoes_de_preco_com_literal(caminho: Path) -> list[str]:
    tree = ast.parse(caminho.read_text(encoding="utf-8"))
    achados = []
    for no in ast.walk(tree):
        if not isinstance(no, ast.Assign):
            continue
        for alvo in no.targets:
            if isinstance(alvo, ast.Name) and alvo.id.startswith("PRECO_"):
                if any(isinstance(n, ast.Constant)
                       and isinstance(n.value, (int, float))
                       for n in ast.walk(no.value)):
                    achados.append(f"{caminho.name}:{no.lineno} {alvo.id}")
    return achados


def test_nenhum_script_ou_modulo_define_preco_com_literal_numerico():
    """Os três scripts que carregavam o número velho agora importam de
    `espectro24.preco`. Um `PRECO_X = 0.14 / 1_000_000` novo reabre a
    divergência, e a falha aponta o arquivo e a linha."""
    achados = []
    for caminho in sorted((RAIZ / "scripts").glob("*.py")) + sorted(
            (RAIZ / "src" / "espectro24").glob("*.py")):
        if caminho.name == "preco.py":
            continue
        achados += _atribuicoes_de_preco_com_literal(caminho)
    assert not achados, f"preço definido fora de preco.py: {achados}"


def test_a_varredura_de_literais_detecta_o_defeito(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("PRECO_SAIDA = 0.28 / 1_000_000\n", encoding="utf-8")
    assert _atribuicoes_de_preco_com_literal(f) == ["x.py:1 PRECO_SAIDA"]


def test_os_scripts_usam_o_pior_caso_do_modulo():
    import classificar_10 as c10
    import gate_taxonomia as gt
    import verificador_impacto as vi
    for m in (c10, gt, vi):
        assert m.PRECO_ENTRADA_MISS == P.PICO.miss_por_token
        assert m.PRECO_ENTRADA_HIT == P.PICO.hit_por_token
        assert m.PRECO_SAIDA == P.PICO.saida_por_token
