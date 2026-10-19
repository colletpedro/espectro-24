"""Home nova — busca, filme do dia, prateleiras, recém-chegados.

Como em `test_faixa_stills.py`, a lógica da home foi escrita em funções
PURAS (`busca.js`, `selecao.js`, `textos_home.js`, sem DOM) e é EXECUTADA
aqui sob `node`, não só lida como texto. Sem `node`, os testes que dependem
dele são pulados com motivo visível; os que leem só arquivos continuam.

O que cada bloco trava:
  1. filme do dia: determinismo, ciclo sem repetição, fuso de São Paulo,
     lista de exclusão, e a regra escrita para quando a lista muda;
  2. busca: normalização (acentos, caixa, pontuação, artigos) e ordem;
  3. prateleiras: piso, exclusão, ordem alfabética e rotação;
  4. invariante "sem nota": varre o HTML e o JS gerado da home;
  5. justificativas: sem número de proporção, sem veredito, os três grupos
     sempre juntos, e só metadado + nome de eixo como insumo;
  6. nenhuma seleção depende da distribuição dos grupos;
  7. `js/indice.js` em dia com `js/data.js`.
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import textwrap
import unicodedata
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FRONT = RAIZ / "frontend"
JS = FRONT / "js"

precisa_node = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node não encontrado — a lógica da home (busca.js, selecao.js, "
           "textos_home.js) não pôde ser EXECUTADA; fica sem verificação")


def _node(corpo: str, dados=None):
    """Roda `corpo` em node com `B`, `S`, `T` = busca, seleção e textos, e
    `D` = `dados` (JSON). Devolve o JSON que o corpo imprimir."""
    script = textwrap.dedent(f"""
        const B = require({json.dumps(str(JS / "busca.js"))});
        const S = require({json.dumps(str(JS / "selecao.js"))});
        const T = require({json.dumps(str(JS / "textos_home.js"))});
        const D = JSON.parse(require("fs").readFileSync(0, "utf8"));
        {textwrap.dedent(corpo)}
    """)
    r = subprocess.run(["node", "-e", script], input=json.dumps(dados),
                       capture_output=True, text=True)
    assert r.returncode == 0, f"node falhou:\n{r.stderr}"
    return json.loads(r.stdout)


def _modulo_build_indice():
    spec = importlib.util.spec_from_file_location(
        "build_indice_teste", FRONT / "build_indice.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _indice() -> dict:
    texto = (JS / "indice.js").read_text(encoding="utf-8")
    return json.loads(texto[texto.index("=") + 1:].strip().rstrip(";"))


def _filme(slug, titulo=None, **kw):
    f = {"slug": slug, "titulo": titulo or slug, "titulo_letterboxd": None,
         "chave_slug": slug.replace("-", " "), "ano": 2000, "imagens": {},
         "distribuicao": {"negativas": 10, "medianas": 20, "positivas": 70},
         "contraste": "valorativo", "eixos_acima": [], "entrada": "2026-01-01"}
    f.update(kw)
    return f


FILMES_REAIS = _indice()["filmes"]


# ===========================================================================
# 1. FILME DO DIA
# ===========================================================================

@precisa_node
def test_mesma_data_mesmo_filme():
    out = _node("""
        const a = S.filmeDoDia(D, "2026-10-19").slug;
        const b = S.filmeDoDia(D, "2026-10-19").slug;
        const c = S.filmeDoDia(JSON.parse(JSON.stringify(D)).reverse(), "2026-10-19").slug;
        console.log(JSON.stringify([a, b, c]));
    """, FILMES_REAIS)
    assert out[0] == out[1] == out[2]   # nem a ORDEM do índice importa


@precisa_node
def test_ciclo_completo_sem_repeticao():
    """Em N dias seguidos (N = nº de elegíveis), cada elegível aparece
    exatamente uma vez — começando em qualquer dia, inclusive antes da
    época (dias negativos)."""
    out = _node("""
        const n = S.elegiveis(D).length;
        const base = Date.UTC(2026, 9, 19);
        const ciclos = [0, -400, 1234].map(desloc => {
            const vistos = [];
            for (let i = 0; i < n; i++) {
                const dia = new Date(base + (desloc + i) * 86400000)
                    .toISOString().slice(0, 10);
                vistos.push(S.filmeDoDia(D, dia).slug);
            }
            return vistos;
        });
        console.log(JSON.stringify({n, ciclos,
            elegiveis: S.elegiveis(D).map(f => f.slug)}));
    """, FILMES_REAIS)
    for vistos in out["ciclos"]:
        assert len(vistos) == out["n"] == len(set(vistos))
        assert set(vistos) == set(out["elegiveis"])


@precisa_node
def test_o_dia_e_o_de_sao_paulo():
    """23h30 em São Paulo do dia 19 já é dia 20 em UTC — e o filme ainda é
    o do dia 19. O contrário também: 00h30 do dia 20 em SP."""
    out = _node("""
        const f = i => S.filmeDoDiaEm(D, new Date(i)).slug;
        console.log(JSON.stringify({
            dia19_manha: f("2026-10-19T12:00:00Z"),
            dia19_2330_sp: f("2026-10-20T02:30:00Z"),
            dia20_0030_sp: f("2026-10-20T03:30:00Z"),
            dia20_manha: f("2026-10-20T12:00:00Z"),
            dia_sp: S.diaEmSaoPaulo(new Date("2026-10-20T02:30:00Z")),
        }));
    """, FILMES_REAIS)
    assert out["dia_sp"] == "2026-10-19"
    assert out["dia19_manha"] == out["dia19_2330_sp"]
    assert out["dia20_0030_sp"] == out["dia20_manha"]
    assert out["dia19_manha"] != out["dia20_manha"]


@precisa_node
def test_excluido_nunca_e_filme_do_dia_mas_continua_na_busca():
    excluido = "obsession-2025"
    filmes = [_filme(f"f{i:02d}", f"Filme {i:02d}") for i in range(7)]
    filmes.append(_filme(excluido, "Obsessão Curta",
                         eixos_acima=[{"eixo": "ritmo", "lift_pp": 30}]))
    out = _node("""
        const dias = [];
        for (let i = 0; i < 60; i++) dias.push(S.filmeDoDia(D,
            new Date(Date.UTC(2026, 0, 1) + i * 86400000).toISOString().slice(0, 10)).slug);
        console.log(JSON.stringify({
            excluidos: Object.keys(S.EXCLUIDOS), dias,
            busca: B.criar(D).buscar("obsessao").map(r => r.slug),
            prateleiras: S.prateleirasBase(D).map(p => p.filmes.map(f => f.slug)),
            recem: S.recemChegados(D).filmes.map(f => f.slug),
        }));
    """, filmes)
    assert excluido in out["excluidos"]
    assert excluido not in out["dias"]
    assert out["busca"] == [excluido]
    assert all(excluido not in p for p in out["prateleiras"])
    assert excluido not in out["recem"]


@precisa_node
def test_obsession_2025_fora_da_selecao_no_catalogo_real():
    """Decisão do dono (2026-10-19): fora do filme do dia, das prateleiras
    e dos recém-chegados; acessível pela busca."""
    out = _node("""
        const n = S.elegiveis(D).length, dias = [];
        for (let i = 0; i < n; i++) dias.push(S.filmeDoDia(D,
            new Date(Date.UTC(2026, 9, 19) + i * 86400000).toISOString().slice(0, 10)).slug);
        console.log(JSON.stringify({n, total: D.length, dias,
            prat: S.prateleirasBase(D).flatMap(p => p.filmes.map(f => f.slug)),
            recem: S.recemChegados(D).filmes.map(f => f.slug),
            busca: B.criar(D).buscar("obsessao").map(r => r.slug)}));
    """, FILMES_REAIS)
    assert out["n"] == out["total"] - 1
    assert "obsession-2025" not in out["dias"] + out["prat"] + out["recem"]
    assert out["busca"] == ["obsession-2025"]


@precisa_node
def test_filme_novo_nao_reordena_os_que_ja_estavam():
    """A regra escrita em selecao.js para lista que muda: a ordem RELATIVA
    dos elegíveis antigos sobrevive à entrada de um filme novo."""
    novo = _filme("filme-novissimo", "Filme Novíssimo")
    out = _node("""
        const antes = S.permutacao(D.velha).map(f => f.slug);
        const depois = S.permutacao(D.velha.concat([D.novo])).map(f => f.slug)
            .filter(s => s !== D.novo.slug);
        console.log(JSON.stringify({antes, depois}));
    """, {"velha": FILMES_REAIS, "novo": novo})
    assert out["antes"] == out["depois"]


# ===========================================================================
# 2. BUSCA
# ===========================================================================

@precisa_node
@pytest.mark.parametrize("entrada,esperado", [
    ("O Poderoso Chefão", "poderoso chefao"),
    ("A CURA", "cura"),
    ("The Wailing", "wailing"),
    ("Os Bons Companheiros", "bons companheiros"),
    ("(500) Dias com Ela", "500 dias com ela"),
    ("Pearl: Uma História de Origem 'X'", "pearl uma historia de origem x"),
    ("mãe!", "mae"),
    ("  Ação   e   reação ", "acao e reacao"),
    ("a", "a"),          # artigo sozinho NÃO some — é a consulta inteira
    ("the", "the"),
    ("Theodora", "theodora"),   # só artigo como PALAVRA inteira
    ("Amnésia", "amnesia"),
])
def test_normalizacao(entrada, esperado):
    assert _node("console.log(JSON.stringify(B.normalizar(D)));", entrada) == esperado


@precisa_node
def test_ordem_prefixo_antes_de_substring_e_alfabetica_no_empate():
    filmes = [
        _filme("z", "Zumbis de Duna"),          # substring
        _filme("b", "Duna: Parte Dois"),         # prefixo
        _filme("a", "A Duna"),                   # prefixo (artigo ignorado)
        _filme("c", "Areias de Duna"),           # substring
        _filme("d", "Dunkirk Azul"),             # prefixo
        _filme("e", "Outro Filme"),              # não casa
    ]
    out = _node("console.log(JSON.stringify(B.criar(D).buscar('dun').map(r => r.titulo)));",
                filmes)
    assert out == ["A Duna", "Duna: Parte Dois", "Dunkirk Azul",
                   "Areias de Duna", "Zumbis de Duna"]


@precisa_node
def test_ordem_nao_depende_de_distribuicao_nem_da_ordem_do_indice():
    filmes = [_filme(s, t, distribuicao=d) for s, t, d in [
        ("x", "Duna Vermelha", {"negativas": 90, "medianas": 5, "positivas": 5}),
        ("y", "Duna Azul", {"negativas": 1, "medianas": 1, "positivas": 98}),
    ]]
    out = _node("""console.log(JSON.stringify([
        B.criar(D).buscar('duna').map(r => r.slug),
        B.criar(D.slice().reverse()).buscar('duna').map(r => r.slug)]));""", filmes)
    assert out == [["y", "x"], ["y", "x"]]


@precisa_node
def test_busca_no_indice_real():
    out = _node("""
        const m = B.criar(D);
        const q = s => m.buscar(s).map(r => r.slug);
        console.log(JSON.stringify({
            chefao: q("poderoso chefao"),
            godfather: q("THE GODFATHER"),
            letterboxd: q("memories of murder"),
            ano: q("1957"),
            titulo_ano: q("coringa 2019"),
            nada: q("xyzzy"),
            vazio: q("   "),
        }));
    """, FILMES_REAIS)
    assert out["chefao"] == ["the-godfather"]
    assert out["godfather"] == ["the-godfather"]        # pela chave do slug
    assert out["letterboxd"] == ["memories-of-murder"]  # pelo título do Letterboxd
    assert out["ano"] == ["12-angry-men"]
    assert out["titulo_ano"] == ["joker-2019"]
    assert out["nada"] == [] and out["vazio"] == []


@precisa_node
def test_ano_vem_depois_de_titulo():
    filmes = [_filme("p", "Filme 1999", ano=2005), _filme("q", "Outro", ano=1999)]
    out = _node("console.log(JSON.stringify(B.criar(D).buscar('1999').map(r => r.slug)));",
                filmes)
    assert out == ["p", "q"]


# ===========================================================================
# 3. PRATELEIRAS
# ===========================================================================

@precisa_node
def test_piso_de_tres_e_exclusao_conta_contra_o_piso():
    def com(eixo, slug):
        return _filme(slug, slug.upper(), contraste="tematico",
                      eixos_acima=[{"eixo": eixo, "lift_pp": 25}])
    filmes = ([com("ritmo", s) for s in ("r1", "r2", "r3")]
              + [com("atuacao", s) for s in ("a1", "a2")]
              + [com("atuacao", "obsession-2025")]          # excluído: não conta
              + [_filme(f"v{i}", f"V{i}") for i in range(2)])  # 2 valorativos
    out = _node("console.log(JSON.stringify(S.prateleirasBase(D).map(p => [p.chave, p.filmes.map(f => f.slug)])));",
                filmes)
    assert out == [["ritmo", ["r1", "r2", "r3"]]]


@precisa_node
def test_prateleiras_reais_ordem_alfabetica_e_rotacao():
    out = _node("""
        const base = S.prateleirasBase(D);
        const rot = [0, 1, 2, 3, 4, 5].map(i => S.prateleiras(D,
            new Date(Date.UTC(2026, 9, 19) + i * 86400000).toISOString().slice(0, 10))
            .map(p => p.chave));
        console.log(JSON.stringify({
            base: base.map(p => [p.chave, p.filmes.map(f => f.slug)]),
            ordenadas: base.every(p => JSON.stringify(p.filmes.map(f => f.slug))
                === JSON.stringify(B.ordenarAlfabetico(p.filmes).map(f => f.slug))),
            rot, piso: S.PISO_PRATELEIRA,
        }));
    """, FILMES_REAIS)
    assert out["ordenadas"]
    assert all(len(f) >= out["piso"] for _, f in out["base"])
    chaves = [c for c, _ in out["base"]]
    for dia in out["rot"]:                       # mesma lista, só girada
        assert sorted(dia) == sorted(chaves)
        k = chaves.index(dia[0])
        assert dia == chaves[k:] + chaves[:k]
    assert len({tuple(d) for d in out["rot"][:len(chaves)]}) == len(chaves)


@precisa_node
def test_recem_chegados_estende_leva_pequena_ate_o_piso():
    filmes = [_filme("n1", "N1", entrada="2026-09-30"),
              _filme("m1", "M1", entrada="2026-09-20"),
              _filme("m2", "M2", entrada="2026-09-20"),
              _filme("v1", "V1", entrada="2026-08-01")]
    out = _node("console.log(JSON.stringify(S.recemChegados(D)));", filmes)
    assert [f["slug"] for f in out["filmes"]] == ["m1", "m2", "n1"]
    assert (out["desde"], out["ate"]) == ("2026-09-20", "2026-09-30")


# ===========================================================================
# 4. INVARIANTE: nenhuma nota, estrela, média ou escore na home
# ===========================================================================

def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if not unicodedata.combining(c)).lower()


# Proibidos em qualquer texto da home. "nota" só aparece NEGADA ("sem nota",
# "sem nota média"), que é a tese do produto, não uma nota.
PROIBIDO_NA_HOME = [
    (r"[★☆⭐✩✪✫✬✭✮✯]", "símbolo de estrela"),
    (r"\bestrelas?\b", "estrela"),
    (r"(?<!sem )\bnotas?\b", "nota"),
    (r"(?<!sem nota )\bmedias?\b", "média"),
    (r"\b(score|rating|ranking|avaliacao|avaliacoes|pontuacao)\b", "escore"),
    (r"\b\d+([.,]\d+)?\s*/\s*(5|10|100)\b", "x/5, x/10"),
]


def _violacoes_de_nota(texto: str) -> list[str]:
    t = _sem_acento(texto)
    return [nome for padrao, nome in PROIBIDO_NA_HOME if re.search(padrao, t)]


def _sem_comentarios_html(html: str) -> str:
    return re.sub(r"<!--.*?-->", "", html, flags=re.S)


def test_html_da_home_sem_nota():
    html = _sem_comentarios_html((FRONT / "index.html").read_text(encoding="utf-8"))
    assert _violacoes_de_nota(html) == []


def test_indice_gerado_sem_nota_e_sem_texto_de_review():
    """O índice é o ÚNICO dado que a home carrega. Ele não pode ter nota
    (nem o histograma por nível de estrela) e não pode ter texto derivado
    de review — é a garantia estrutural do anti-spoiler da justificativa."""
    bruto = (JS / "indice.js").read_text(encoding="utf-8")
    chaves = set(re.findall(r'"([a-z_]+)":', bruto))
    proibidas = {"por_nivel", "nota", "notas", "media", "score", "rating",
                 "n_notas_total", "tema", "temas", "exemplo_parafraseado",
                 "narrativa", "veredito", "condicoes", "observacao_geral",
                 "sinopse_oficial", "buckets", "linhas"}
    assert chaves & proibidas == set()
    assert chaves == {"versao", "fonte", "filmes", "slug", "titulo",
                      "titulo_letterboxd", "chave_slug", "ano", "imagens",
                      "distribuicao", "negativas", "medianas", "positivas",
                      "contraste", "eixos_acima", "eixo", "lift_pp", "entrada",
                      *_modulo_build_indice().CAMPOS_IMAGEM}
    # Os TÍTULOS não passam pelo detector: são dado, e "Estrela Encoberta de
    # Nuvens" é título, não nota. Os outros textos que o índice leva:
    assert all(_violacoes_de_nota(f["contraste"] or "") == []
               for f in FILMES_REAIS)


def test_js_da_home_sem_simbolo_de_estrela():
    for nome in ("inicio.js", "busca.js", "selecao.js", "textos_home.js",
                 "indice.js"):
        fonte = (JS / nome).read_text(encoding="utf-8")
        assert not re.search(r"[★☆⭐]", fonte), nome


@precisa_node
def test_todo_texto_que_a_home_renderiza_sem_nota():
    out = _node("""
        const textos = [T.PREMISSA, T.AVISO_CATALOGO, T.AVISO_LINK,
            T.BUSCA_PLACEHOLDER, T.BUSCA_VAZIA, T.BUSCA_VAZIA_LINK,
            T.ROTULO_FILME_DO_DIA, T.ROTULO_ABRIR, T.ROTULO_RECEM]
            .concat(Object.values(T.TITULO_PRATELEIRA))
            // a justificativa SEM o título do filme, que é dado ("Estrela
            // Encoberta de Nuvens" é título, não nota)
            .concat(D.map(f => T.justificar(f).texto.split(f.titulo).join(" ")));
        console.log(JSON.stringify(textos));
    """, FILMES_REAIS)
    ruins = {t: _violacoes_de_nota(t) for t in out if _violacoes_de_nota(t)}
    assert ruins == {}


def test_o_detector_de_nota_detecta():
    """O guarda não é decorativo: estes PRECISAM ser pegos."""
    for ruim in ("★★★★", "nota 8", "Média 3,5", "4.5/5", "8/10", "3 estrelas",
                 "score alto", "a nota média é 3"):
        assert _violacoes_de_nota(ruim), ruim
    for ok in ("sem nota e sem spoiler", "sem nota média"):
        assert not _violacoes_de_nota(ok), ok


# ===========================================================================
# 5. JUSTIFICATIVAS (templates do filme do dia)
# ===========================================================================

# Vocabulário de VEREDITO e de PROPORÇÃO proibido na justificativa (sem
# acento, palavra inteira; `*` = prefixo). Documentado também no cabeçalho
# de textos_home.js.
VOCABULARIO_PROIBIDO = [
    "amou", "amaram", "adorou", "adoraram", "odiou", "odiaram", "detestou",
    "detestaram", "gostou", "gostaram", "maioria", "minoria", "unanime*",
    "unanimidade", "consenso", "aclamad*", "obra-prima", "imperdivel",
    "melhor", "melhores", "pior", "piores", "excelente", "otimo", "bom",
    "boa", "ruim", "genial", "fracasso", "sucesso", "decepcion*",
    "recomend*", "vale a pena", "nota", "notas", "estrela*", "media",
    "score", "rating", "ranking", "metade", "todos", "quase", "poucos",
    "muitos",
]


def _proibidos_em(texto: str) -> list[str]:
    t = _sem_acento(texto)
    achados = []
    for termo in VOCABULARIO_PROIBIDO:
        padrao = (r"\b" + re.escape(termo[:-1]) + r"\w*" if termo.endswith("*")
                  else r"\b" + re.escape(termo) + r"\b")
        if re.search(padrao, t):
            achados.append(termo)
    return achados


@pytest.fixture(scope="module")
def justificativas():
    if shutil.which("node") is None:
        pytest.skip("node não encontrado")
    return _node("""
        console.log(JSON.stringify(S.elegiveis(D).map(f =>
            Object.assign({slug: f.slug, titulo: f.titulo}, T.justificar(f)))));
    """, FILMES_REAIS)


def test_justificativa_sem_numero_nem_veredito(justificativas):
    assert ({j["slug"] for j in justificativas}
            == {f["slug"] for f in FILMES_REAIS} - {"obsession-2025"})
    for j in justificativas:
        resto = j["texto"].replace(j["titulo"], " ")
        assert not re.search(r"\d", resto), (j["slug"], j["texto"])
        assert "%" not in resto, j["slug"]
        assert _proibidos_em(resto) == [], (j["slug"], _proibidos_em(resto))


def test_justificativa_nomeia_os_tres_grupos_por_igual(justificativas):
    for j in justificativas:
        contagem = [len(re.findall(rf"\b{g}\b", j["texto"]))
                    for g in ("HATERS", "MIXED", "FANS")]
        assert contagem in ([1, 1, 1], [0, 0, 0]), (j["slug"], contagem)
        for gloss in ("quem gostou", "quem não gostou", "quem ficou no meio"):
            assert gloss not in j["texto"]


def test_justificativa_tem_duas_ou_tres_frases(justificativas):
    for j in justificativas:
        resto = j["texto"].replace(j["titulo"], "T")
        frases = [f for f in re.split(r"[.!?](?:\s|$)", resto) if f.strip()]
        assert 2 <= len(frases) <= 3, (j["slug"], frases)


def test_gancho_segue_a_prioridade(justificativas):
    por_slug = {f["slug"]: f for f in FILMES_REAIS}
    for j in justificativas:
        f = por_slug[j["slug"]]
        if f["eixos_acima"]:
            maior = max(f["eixos_acima"], key=lambda e: e["lift_pp"])["lift_pp"]
            assert j["gancho"] == "eixo"
            assert j["eixo"] in {e["eixo"] for e in f["eixos_acima"]
                                 if e["lift_pp"] == maior}
        elif f["contraste"] == "valorativo":
            assert j["gancho"] == "valorativo"
        else:
            assert j["gancho"] == "generico"


@precisa_node
def test_justificativa_so_le_titulo_e_eixo():
    """Mesmo com texto de review plantado no objeto, nada dele chega ao
    texto: o template só lê `titulo`, `slug`, `eixos_acima` e `contraste`."""
    isca = "REVIEWPLANTADA"
    f = _filme("x", "Filme X", contraste="tematico",
               eixos_acima=[{"eixo": "ritmo", "lift_pp": 30}],
               tema=isca, exemplo_parafraseado=isca, narrativa=isca,
               veredito={"texto": isca}, sinopse_oficial=isca)
    out = _node("console.log(JSON.stringify(T.justificar(D).texto));", f)
    assert isca not in out and "ritmo" in out


@precisa_node
def test_todo_eixo_e_toda_prateleira_tem_nome():
    out = _node("""console.log(JSON.stringify({
        ordem: S.ORDEM_PRATELEIRAS,
        nomes: Object.keys(T.EIXO_NOME), titulos: Object.keys(T.TITULO_PRATELEIRA)}));""")
    assert set(out["titulos"]) == set(out["ordem"])
    assert set(out["nomes"]) == set(out["ordem"]) - {"valorativo"}


# ===========================================================================
# 6. NADA DEPENDE DA DISTRIBUIÇÃO DOS GRUPOS
# ===========================================================================

@precisa_node
def test_selecao_identica_com_distribuicao_embaralhada():
    trocado = [dict(f, distribuicao={"negativas": 97, "medianas": 2,
                                     "positivas": 1} if i % 2 else None)
               for i, f in enumerate(FILMES_REAIS)]
    corpo = """
        const resumo = L => {
            const out = [];
            for (let i = 0; i < 40; i++) {
                const dia = new Date(Date.UTC(2026, 9, 1) + i * 86400000).toISOString().slice(0, 10);
                out.push([S.filmeDoDia(L, dia).slug,
                          S.prateleiras(L, dia).map(p => p.chave + ":" + p.filmes.map(f => f.slug).join(","))]);
            }
            out.push(S.recemChegados(L).filmes.map(f => f.slug));
            out.push(B.criar(L).buscar("o").map(r => r.slug));
            return out;
        };
        console.log(JSON.stringify([resumo(D.a), resumo(D.b)]));
    """
    a, b = _node(corpo, {"a": FILMES_REAIS, "b": trocado})
    assert a == b


# ===========================================================================
# 7. O ÍNDICE ESTÁ EM DIA COM OS DADOS PUBLICADOS
# ===========================================================================

def test_indice_js_em_dia_com_data_js():
    bi = _modulo_build_indice()
    esperado = bi.serializar(bi.montar_indice(bi.ler_data_js(), bi.ler_registro()))
    assert (JS / "indice.js").read_text(encoding="utf-8") == esperado, (
        "js/indice.js defasado — rode `python3 frontend/build_indice.py`")


def test_todo_filme_do_catalogo_tem_data_de_entrada():
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", f["entrada"] or "")
               for f in FILMES_REAIS)


def test_chave_do_slug():
    ch = _modulo_build_indice().chave_do_slug
    assert ch("parasite-2019") == "parasite"
    assert ch("happy-hour-2015-1") == "happy hour"
    assert ch("district-9") == "district 9"
    assert ch("friday-the-13th-2009") == "friday the 13th"
    assert ch("2001-a-space-odyssey") == "2001 a space odyssey"
