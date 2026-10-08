"""[2026-09-22, C22] Dispensa do passe 3 quando os passes 1 e 2 concordam.

A afirmação a provar: se os passes 1 e 2 votaram o MESMO conjunto de eixos,
o consenso 2-de-3 é o mesmo QUALQUER que seja o passe 3 — e é o mesmo que o
consenso com o passe 3 dispensado.

**Sobre o que `_consensuar` de fato usa.** Do voto, SÓ `r["eixos"]` (como
`_ler_passe` o entrega: inválido recuperado, ordenado, sem repetição). Do
resto, lê `registros[0]` para os metadados da linha (slug, bucket, id,
nivel, n_chars, perfil) e a marca `fallback_conteudo`/`excecao` de cada um.
`temas_livres` e `eixos_invalidos` crus NÃO entram. Então a igualdade é sobre
`eixos` — `livre` incluído, porque é um rótulo votado como os outros.

**O que NÃO é igual, e é registrado:** `votos` e `eixos_por_passe` da linha
dependem do passe 3 (são o próprio voto dele). Com o passe dispensado, a
linha tem DOIS votos, e a medida de reprodutibilidade de 3 passes deixa de
existir para essa review. Nenhum consumidor de produção lê esses campos
(`pipeline`/`eixos` leem `eixos` e as marcas de proveniência).

**Exaustivo, não por exemplo.** O domínio de `eixos` depois de `_ler_passe` é
um subconjunto de `EIXOS_VALIDOS` (10 eixos + `livre`): 2^11 = 2.048
conjuntos. O teste varre TODO par (voto dos passes 1-2, voto do passe 3):
2.048 × 2.048 = 4.194.304 combinações.
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import excecao_gemini_c22 as C22  # noqa: E402
import votacao_3 as v3  # noqa: E402
from classificar_10 import EIXOS_VALIDOS  # noqa: E402

ROTULOS = sorted(EIXOS_VALIDOS)
assert len(ROTULOS) == 11 and "livre" in ROTULOS


def _todos_os_conjuntos() -> list[list[str]]:
    return [sorted(c) for k in range(len(ROTULOS) + 1)
            for c in combinations(ROTULOS, k)]


CONJUNTOS = _todos_os_conjuntos()


def _reg(eixos: list[str], passe: int, excecao: bool = True, **extra) -> dict:
    r = {"ok": True, "passe": passe, "slug": "f", "perfil": "x",
         "bucket": "negativas", "id": "r", "nivel": 3.0, "n_chars": 100,
         "eixos": list(eixos), "provider": "gemini",
         "modelo": "gemini-3.7-flash", "modelo_efetivo": "gemini-3.7-flash",
         "camada": "flex", **extra}
    if excecao:
        r["excecao"] = C22.EXCECAO
    return r


def test_o_dominio_tem_2048_conjuntos():
    assert len(CONJUNTOS) == 2 ** 11
    assert len({tuple(c) for c in CONJUNTOS}) == 2048


def test_p1_igual_p2_da_o_mesmo_consenso_para_todo_passe_3_possivel():
    """4.194.304 combinações: para cada voto v dos passes 1-2 e cada voto x
    do passe 3, `eixos` do consenso é v — e é o mesmo do consenso com o
    passe 3 dispensado."""
    chaves = [("f", "negativas", f"x{i}") for i in range(len(CONJUNTOS))]
    p3 = {c: _reg(x, 3) for c, x in zip(chaves, CONJUNTOS)}
    falhas = 0
    for v in CONJUNTOS:
        r1, r2 = _reg(v, 1), _reg(v, 2)
        p1 = dict.fromkeys(chaves, r1)
        p2 = dict.fromkeys(chaves, r2)
        com_x = v3._consensuar([p1, p2, p3], chaves)
        # sem o passe 3 a linha não depende de x: uma chave basta
        [sem_x] = v3._consensuar([{chaves[0]: r1}, {chaves[0]: r2}, {}],
                                 chaves[:1])
        assert len(com_x) == len(chaves)
        esperado = sorted(set(v))
        assert sem_x["eixos"] == esperado
        falhas += sum(1 for a in com_x if a["eixos"] != esperado)
    assert falhas == 0


def test_a_linha_dispensada_se_declara_e_tem_dois_votos():
    v = ["atuacao", "livre"]
    [linha] = v3._consensuar([{("f", "b", "r"): _reg(v, 1)},
                              {("f", "b", "r"): _reg(v, 2)}, {}],
                             [("f", "b", "r")])
    assert linha["passe_3_dispensado"] is True
    assert linha["eixos_por_passe"] == [v, v]
    assert linha["votos"] == {"atuacao": 2, "livre": 2}
    assert linha["classificacao_excecao"]["excecao"] == C22.EXCECAO
    assert linha["classificacao_excecao"]["provider"] == "gemini"
    assert linha["classificacao_excecao"]["modelos_efetivos"] == ["gemini-3.7-flash"]


def test_p1_diferente_de_p2_nao_dispensa_e_espera_o_passe_3():
    c = ("f", "b", "r")
    p = [{c: _reg(["atuacao"], 1)}, {c: _reg(["ritmo"], 2)}, {}]
    assert not v3.passe_3_dispensavel(p[0][c], p[1][c])
    assert v3.chaves_consensuaveis(p) == set()
    assert v3._consensuar(p, [c]) == []


def test_temas_livres_diferentes_nao_impedem_a_dispensa():
    """`_consensuar` não lê `temas_livres`: a igualdade é sobre `eixos`."""
    assert v3.passe_3_dispensavel(_reg(["livre"], 1, temas_livres=["a"]),
                                  _reg(["livre"], 2, temas_livres=["b"]))


@pytest.mark.parametrize("marca1,marca2", [(False, False), (True, False),
                                           (False, True)])
def test_fora_da_excecao_os_tres_passes_continuam_obrigatorios(marca1, marca2):
    """Os 99 publicados (sem a marca) não ganham dispensa: review cujo passe
    3 falhou continua FORA do consenso, como sempre foi."""
    c = ("f", "b", "r")
    p = [{c: _reg(["atuacao"], 1, excecao=marca1)},
         {c: _reg(["atuacao"], 2, excecao=marca2)}, {}]
    assert not v3.passe_3_dispensavel(p[0][c], p[1][c])
    assert v3.chaves_consensuaveis(p) == set()


def test_linha_sem_excecao_nao_ganha_campo_novo():
    """As linhas dos 99 saem byte a byte como eram."""
    c = ("f", "b", "r")
    p = [{c: _reg(["atuacao"], n, excecao=False)} for n in (1, 2, 3)]
    [linha] = v3._consensuar(p, [c])
    assert "classificacao_excecao" not in linha
    assert "passe_3_dispensado" not in linha


def test_votos_de_dentro_e_de_fora_da_excecao_na_mesma_review_levantam():
    c = ("f", "b", "r")
    p = [{c: _reg(["atuacao"], 1)}, {c: _reg(["atuacao"], 2)},
         {c: _reg(["atuacao"], 3, excecao=False)}]
    with pytest.raises(v3.ProviderMisturadoNoVoto):
        v3._consensuar(p, [c])


def test_a_excecao_recusa_slug_fora_dos_55():
    with pytest.raises(C22.ForaDaExcecao):
        C22.exigir_no_escopo(["the-godfather"])
    C22.exigir_no_escopo(sorted(C22.SLUGS)[:3])
    assert len(C22.SLUGS) == 55
