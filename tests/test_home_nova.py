"""Home nova — busca, filme do dia, coleções (eram as prateleiras),
recém-chegados. A home editorial (rodada editorial) tem testes próprios em
`test_home_editorial.py`; os de prateleira que deixaram de valer foram
SUBSTITUÍDOS aqui pelos da regra nova, cada um marcado "[rodada editorial]".

Como em `test_faixa_stills.py`, a lógica da home foi escrita em funções
PURAS (`busca.js`, `selecao.js`, `textos_home.js`, sem DOM) e é EXECUTADA
aqui sob `node`, não só lida como texto. Sem `node`, os testes que dependem
dele são pulados com motivo visível; os que leem só arquivos continuam.

O que cada bloco trava:
  1. filme do dia: determinismo, ciclo sem repetição, fuso de São Paulo,
     lista de exclusão, e a regra escrita para quando a lista muda;
  2. busca: normalização (acentos, caixa, pontuação, artigos) e ordem;
  3. coleções: piso, exclusão, ordem alfabética e intercalação;
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
from fractions import Fraction
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
         "contraste": "valorativo", "eixos_acima": [], "entrada": "2026-01-01",
         "titulo_nativo": None, "assunto_comum": None, "estreia": None}
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
    exatamente uma vez NA PERMUTAÇÃO — começando em qualquer dia, inclusive
    antes da época (dias negativos).

    [rodada 4] Lê `filmeDaPermutacao`: desde que o aniversário passou a
    definir o filme do dia (decisão do dono), `filmeDoDia` pode repetir um
    filme no ciclo. A asserção é a mesma, sobre o mesmo mecanismo; o
    desvio do aniversário tem testes próprios abaixo."""
    out = _node("""
        const n = S.elegiveis(D).length;
        const base = Date.UTC(2026, 9, 19);
        const ciclos = [0, -400, 1234].map(desloc => {
            const vistos = [];
            for (let i = 0; i < n; i++) {
                const dia = new Date(base + (desloc + i) * 86400000)
                    .toISOString().slice(0, 10);
                vistos.push(S.filmeDaPermutacao(D, dia).slug);
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
def test_colecoes_reais_ordem_alfabetica_piso_e_intercalacao():
    """[rodada editorial] Substitui o teste da ordem das prateleiras por dia
    (rodada 2): as prateleiras saíram da home. Cada coleção em ordem
    alfabética e acima do piso; a ORDEM FIXA das coleções intercala divisão
    e valorativa PROPORCIONALMENTE, começando por divisão, sem sequência de
    um tipo maior que ceil(maior/menor), cada tipo na ordem da taxonomia."""
    out = _node("""
        const base = S.prateleirasBase(D);
        console.log(JSON.stringify({
            base: base.map(p => [p.chave, p.tipo, p.filmes.map(f => f.slug)]),
            ordenadas: base.every(p => JSON.stringify(p.filmes.map(f => f.slug))
                === JSON.stringify(B.ordenarAlfabetico(p.filmes).map(f => f.slug))),
            ordem: S.ordemDasColecoes(D).map(p => [p.chave, p.tipo]),
            piso: S.PISO_PRATELEIRA,
        }));
    """, FILMES_REAIS)
    assert out["ordenadas"]
    assert all(len(f) >= out["piso"] for _, _, f in out["base"])
    assert "valorativo" not in [c for c, _, _ in out["base"]]   # a única saiu
    D = [c for c, t, _ in out["base"] if t == "divisao"]
    V = [c for c, t, _ in out["base"] if t == "valorativa"]
    assert D and V
    chaves = [c for c, _ in out["ordem"]]
    tipos = [t for _, t in out["ordem"]]
    assert sorted(chaves) == sorted(D + V)
    assert tipos[0] == "divisao" and tipos[1] == "valorativa"
    maior, menor = max(len(D), len(V)), min(len(D), len(V))
    teto = -(-maior // menor)
    corrida, maxima = 1, 1
    for a, b in zip(tipos, tipos[1:]):
        corrida = corrida + 1 if a == b else 1
        maxima = max(maxima, corrida)
    assert maxima <= teto, tipos
    for lista in (D, V):                          # cada tipo na ordem da taxonomia
        assert [c for c in chaves if c in lista] == lista


@precisa_node
def test_intercalacao_e_piso_sinteticos():
    """[rodada editorial] Substitui o da rodada 2 (`prateleiras` por dia):
    a mesma intercalação e o mesmo piso, agora na ordem FIXA das coleções."""
    def div(eixo, slug):
        return _filme(slug, slug.upper(), contraste="tematico",
                      eixos_acima=[{"eixo": eixo, "lift_pp": 25}])
    def val(eixo, slug):
        return _filme(slug, slug.upper(), assunto_comum=eixo)
    filmes = ([div("ritmo", f"r{i}") for i in range(3)]
              + [div("atuacao", f"a{i}") for i in range(3)]
              + [val("roteiro_estrutura", f"v{i}") for i in range(4)]
              + [val("comparacoes", f"c{i}") for i in range(2)]   # abaixo do piso
              + [_filme("sem-assunto", "SEM")])                    # valorativo sem eixo
    out = _node("""console.log(JSON.stringify(
        S.ordemDasColecoes(D).map(p => p.chave + "=" + p.filmes.map(f => f.slug).join(","))));""",
                filmes)
    assert out == ["ritmo=r0,r1,r2", "valorativo:roteiro_estrutura=v0,v1,v2,v3",
                   "atuacao=a0,a1,a2"]


@precisa_node
def test_recem_chegados_tres_por_dia_em_ordem_alfabetica():
    """[rodada editorial] Substitui "limite de doze": a leva inteira fica em
    `recemChegados` (alfabética), e a home mostra 3 por dia (`recemDoDia`),
    uma janela circular que gira um filme por dia."""
    filmes = ([_filme(f"n{i:02d}", f"Novo {i:02d}", entrada="2026-09-30")
               for i in range(20, 0, -1)]
              + [_filme("velho", "Aaa Velho", entrada="2026-08-01")])
    out = _node("""console.log(JSON.stringify({leva: S.recemChegados(D),
        dias: ["2026-01-01", "2026-01-02", "2026-01-20"].map(d =>
            S.recemDoDia(D, d).filmes.map(f => f.slug))}));""", filmes)
    leva = out["leva"]
    assert leva["total"] == 20 and leva["desde"] == leva["ate"] == "2026-09-30"
    assert [f["slug"] for f in leva["filmes"]] == [f"n{i:02d}" for i in range(1, 21)]
    assert out["dias"] == [["n01", "n02", "n03"], ["n02", "n03", "n04"],
                           ["n01", "n02", "n20"]]     # dia 19: n20, n01, n02


@precisa_node
def test_recem_chegados_reais_e_link_para_filmes_filtrado():
    """[rodada editorial] Era "12 da leva"; agora 3 por dia, mesmo link."""
    out = _node("""console.log(JSON.stringify({r: S.recemChegados(D),
        hoje: S.recemDoDia(D, "2026-10-21")}));""", FILMES_REAIS)
    assert out["r"]["total"] == 44 and len(out["r"]["filmes"]) == 44
    assert out["r"]["desde"] == "2026-09-17"
    assert len(out["hoje"]["filmes"]) == 3
    assert {f["slug"] for f in out["hoje"]["filmes"]} <= {f["slug"] for f in out["r"]["filmes"]}
    fonte = (JS / "inicio.js").read_text(encoding="utf-8")
    assert '"?desde=" + r.desde' in fonte
    cat = (JS / "catalogo.js").read_text(encoding="utf-8")
    assert 'get("desde")' in cat and "foraDaLeva" in cat


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
                      "titulo_nativo", "assunto_comum", "estreia",
                      # [rodada editorial] metadados TMDB da manchete
                      "paises", "logo", "path", "idioma", "classe",
                      "titulo_difere_do_logo", "diretor", "stills",
                      # [rodada Explorar] gêneros da ficha (TMDB, pt-BR)
                      "generos",
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
    # Cada filme duas vezes: o texto de hoje e o texto FORÇADO de
    # aniversário (estreia no mesmo dia e mês, 36 anos antes) — o
    # vocabulário proibido vale para o template de aniversário também.
    return _node("""
        const dia = "2026-10-19";
        console.log(JSON.stringify(S.elegiveis(D).flatMap(f => [
            Object.assign({slug: f.slug, titulo: f.titulo, forcado: false},
                          T.justificar(f, dia)),
            Object.assign({slug: f.slug, titulo: f.titulo, forcado: true},
                          T.justificar(Object.assign({}, f, {estreia: "1990-10-19"}), dia)),
        ])));
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
        if j["forcado"]:
            assert j["gancho"] == "aniversario"
            assert j["texto"].startswith(f["titulo"] + " faz aniversário de estreia hoje. ")
            continue
        # [rodada 3] com a estreia real no índice, o dia fixo do fixture
        # (19/10) é aniversário de algum filme: o gancho é "aniversario"
        # exatamente quando dia e mês batem, e o de conteúdo segue a regra.
        aniv = bool(f["estreia"]) and f["estreia"][5:] == "10-19" and f["estreia"][:4] < "2026"
        assert (j["gancho"] == "aniversario") is aniv, (j["slug"], f["estreia"])
        j = dict(j, gancho=j["gancho_conteudo"])
        if f["eixos_acima"]:
            maior = max(f["eixos_acima"], key=lambda e: e["lift_pp"])["lift_pp"]
            assert j["gancho"] == "eixo"
            assert j["eixo"] in {e["eixo"] for e in f["eixos_acima"]
                                 if e["lift_pp"] == maior}
        elif f["contraste"] == "valorativo" and f["assunto_comum"]:
            assert j["gancho"] == "valorativo"
            assert j["eixo"] == f["assunto_comum"]
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
        ordem: S.ORDEM_EIXOS, prefixo: S.PREFIXO_VALORATIVA,
        nomes: Object.keys(T.EIXO_NOME), titulos: Object.keys(T.TITULO_PRATELEIRA)}));""")
    assert set(out["nomes"]) == set(out["ordem"])
    assert set(out["titulos"]) == (set(out["ordem"])
                                   | {out["prefixo"] + e for e in out["ordem"]})


@precisa_node
@pytest.mark.parametrize("estreia,dia,esperado", [
    ("1990-03-14", "2026-03-14", True),
    ("1990-03-14", "2026-03-15", False),
    ("2026-03-14", "2026-03-14", False),     # o dia da estreia não é aniversário
    ("2000-02-29", "2028-02-29", True),
    ("2000-02-29", "2027-02-28", False),     # sem aniversário adiado
    ("2000-02-29", "2027-03-01", False),
    (None, "2026-03-14", False),
    ("1990", "2026-03-14", False),           # só o ano: não dispara
])
def test_aniversario_dia_e_mes(estreia, dia, esperado):
    assert _node("console.log(JSON.stringify(T.fazAniversario(D[0], D[1])));",
                 [estreia, dia]) is esperado


@precisa_node
def test_prioridade_dos_quatro_ganchos():
    dia = "2026-03-14"
    filmes = {
        "eixo": _filme("e", "Filme E", contraste="tematico", assunto_comum="ritmo",
                       eixos_acima=[{"eixo": "atuacao", "lift_pp": 25}]),
        "valorativo": _filme("v", "Filme V", assunto_comum="comparacoes"),
        "generico": _filme("g", "Filme G", contraste=None, assunto_comum="ritmo"),
        "sem_assunto": _filme("s", "Filme S", assunto_comum=None),
    }
    out = _node("""
        const r = {};
        for (const [k, f] of Object.entries(D.filmes)) {
            r[k] = T.justificar(f, D.dia);
            r[k + "+aniv"] = T.justificar(Object.assign({}, f, {estreia: "1980-03-14"}), D.dia);
        }
        console.log(JSON.stringify(r));
    """, {"filmes": filmes, "dia": dia})
    assert [out[k]["gancho"] for k in filmes] == ["eixo", "valorativo", "generico", "generico"]
    assert out["eixo"]["eixo"] == "atuacao"           # divisão vence o assunto comum
    assert out["valorativo"]["eixo"] == "comparacoes"
    assert "comparações com outros filmes" in out["valorativo"]["texto"]
    for k in filmes:
        a = out[k + "+aniv"]
        assert a["gancho"] == "aniversario"
        assert a["gancho_conteudo"] == out[k]["gancho"]
        # [rodada 4] a segunda frase NÃO repete o título: "Em X," → "Nele,"
        # e "X está" → "Está"; o resto do texto de conteúdo é idêntico.
        t = filmes[k]["titulo"]
        sem_titulo = (out[k]["texto"].replace("Em " + t + ",", "Nele,", 1)
                      .replace(t + " está", "Está", 1))
        assert sem_titulo != out[k]["texto"]
        assert a["texto"] == t + " faz aniversário de estreia hoje. " + sem_titulo
        assert a["texto"].count(t) == 1


@precisa_node
def test_aniversario_define_o_filme_do_dia_e_a_home_usa_o_dia_da_url():
    """[rodada 4] Inverte a regra da rodada 2 (decisão do dono): o
    aniversariante É o filme do dia. A ORDEM DAS COLEÇÕES não depende da
    estreia ([rodada editorial]: era "as prateleiras"; a coleção DO DIA
    depende da manchete por regra — evita a coleção dela — e tem teste
    próprio). E a home passa o `?dia=` (ou o dia de hoje em São Paulo)
    para a seleção e para a justificativa."""
    out = _node("""
        const dia = "2026-10-19";
        // [4b] um alvo FORA da janela de carência (±14 dias da permutação)
        const alvo = S.filmeDaPermutacao(D, "2026-11-28");
        const com = D.map(f => Object.assign({}, f,
            {estreia: f.slug === alvo.slug ? "1999-10-19" : null}));
        console.log(JSON.stringify({
            sem: S.filmeDaPermutacao(D, dia).slug, alvo: alvo.slug,
            com: S.escolhaDoDia(com, dia),
            prat: [S.ordemDasColecoes(D).map(p => p.chave), S.ordemDasColecoes(com).map(p => p.chave)]}));
    """, FILMES_REAIS)
    assert out["sem"] != out["alvo"]
    assert out["com"]["filme"]["slug"] == out["alvo"]
    assert out["com"]["motivo"] == "aniversario"
    assert out["prat"][0] == out["prat"][1]
    fonte = (JS / "inicio.js").read_text(encoding="utf-8")
    assert 'get("dia")' in fonte and "T.justificar(f, DIA)" in fonte
    assert "S.escolhaDoDia(FILMES, DIA)" in fonte


# [4b] Os testes sintéticos de aniversário usam 60 filmes: com a carência de
# ±14 dias (janela de 29), numa lista menor que 30 TODO filme cai na janela
# e o aniversário nunca vence. `longe(k)` é o filme que a permutação dá k
# dias depois do dia testado — fora da carência para 15 <= |k| <= 45.
_SESSENTA = [_filme(f"f{i:02d}", f"Filme {i:02d}") for i in range(60)]
_LONGE = """
    const lista = S.permutacao(S.elegiveis(D.filmes));
    const N = lista.length, d0 = S.diasDesdeEpoca(D.dia);
    const longe = k => lista[((d0 + k) % N + N) % N].slug;
    const com = (slugs, estreia) => D.filmes.map(f =>
        Object.assign({}, f, {estreia: slugs.includes(f.slug) ? estreia : null}));
"""


@precisa_node
def test_aniversarios_simultaneos_vence_o_primeiro_da_permutacao():
    out = _node(_LONGE + """
        const marcados = [longe(20), longe(30), longe(40)];
        console.log(JSON.stringify({perm: lista.map(f => f.slug), marcados,
                                    e: S.escolhaDoDia(com(marcados, "1990-05-05"), D.dia)}));
    """, {"filmes": _SESSENTA, "dia": "2027-05-05"})
    primeiro = [s for s in out["perm"] if s in out["marcados"]][0]
    assert out["e"]["filme"]["slug"] == primeiro
    assert out["e"]["motivo"] == "aniversario"


@precisa_node
@pytest.mark.parametrize("perto", [-14, -3, 0, 3, 14])
def test_carencia_desempate_depois_da_carencia(perto):
    """Um aniversariante EM carência nunca vence, venha antes ou depois na
    permutação: o desempate é só entre os que passam."""
    out = _node(_LONGE + """
        const emJanela = longe(D.perto), fora = [longe(25), longe(35)];
        console.log(JSON.stringify({ordem: lista.map(f => f.slug), emJanela, fora,
            e: S.escolhaDoDia(com([emJanela].concat(fora), "1990-05-05"), D.dia),
            carencia: S.emCarencia(emJanela, lista, D.dia),
            limiteFora: [S.emCarencia(longe(15), lista, D.dia), S.emCarencia(longe(-15), lista, D.dia)]}));
    """, {"filmes": _SESSENTA, "dia": "2027-05-05", "perto": perto})
    assert out["carencia"] is True and out["limiteFora"] == [False, False]
    passam = [s for s in out["ordem"] if s in out["fora"]]
    assert out["e"]["filme"]["slug"] == passam[0] != out["emJanela"]
    assert out["e"]["motivo"] == "aniversario"


@precisa_node
def test_carencia_nenhum_aniversariante_passa_vale_a_permutacao():
    out = _node(_LONGE + """
        const L = com([longe(-14), longe(0), longe(14)], "1990-05-05");
        console.log(JSON.stringify({e: S.escolhaDoDia(L, D.dia),
                                    p: S.filmeDaPermutacao(L, D.dia).slug}));
    """, {"filmes": _SESSENTA, "dia": "2027-05-05"})
    assert out["e"]["motivo"] == "permutacao"
    assert out["e"]["filme"]["slug"] == out["p"]


@precisa_node
def test_carencia_caso_napoleao():
    """Real: Napoleão sai pela permutação em 20/11/2026; o aniversário de
    22/11 cai na carência e NÃO vence — vale a permutação."""
    out = _node("""
        console.log(JSON.stringify({p20: S.filmeDaPermutacao(D, "2026-11-20").slug,
            aniv: S.fazAniversario(D.find(f => f.slug === "napoleon-2023").estreia, "2026-11-22"),
            e22: S.escolhaDoDia(D, "2026-11-22"), C: S.CARENCIA_ANIVERSARIO_DIAS}));
    """, FILMES_REAIS)
    assert out["C"] == 14
    assert out["p20"] == "napoleon-2023" and out["aniv"] is True
    assert out["e22"]["filme"]["slug"] != "napoleon-2023"
    assert out["e22"]["motivo"] == "permutacao"


@precisa_node
def test_permutacao_segue_intacta_em_volta_do_aniversario():
    """O dia do aniversário não desloca o ciclo: em TODOS os outros dias o
    filme é exatamente o da permutação — inclusive o dia seguinte."""
    out = _node(_LONGE + """
        const alvo = longe(30);
        const L = com([alvo], "1990-03-10");
        const r = [];
        for (let i = -20; i < 20; i++) {
            const dia = new Date(Date.UTC(2027, 2, 10) + i * 86400000).toISOString().slice(0, 10);
            const e = S.escolhaDoDia(L, dia);
            r.push([dia, e.filme.slug, e.motivo, S.filmeDaPermutacao(L, dia).slug]);
        }
        console.log(JSON.stringify({alvo, r}));
    """, {"filmes": _SESSENTA, "dia": "2027-03-10"})
    for dia, slug, motivo, perm in out["r"]:
        if dia == "2027-03-10":
            assert (slug, motivo) == (out["alvo"], "aniversario")
        else:
            assert (slug, motivo) == (perm, "permutacao"), dia


@precisa_node
@pytest.mark.parametrize("estreia,dia,esperado", [
    ("2020-01-01", "2027-01-01", False),     # 01/01: data genérica do TMDB
    ("2020-01-02", "2027-01-02", True),
    ("2019-12-31", "2026-12-31", True),
])
def test_primeiro_de_janeiro_nao_e_aniversario(estreia, dia, esperado):
    out = _node(_LONGE + """
        const L = com([longe(30)], D.estreia);
        const f = L.find(x => x.estreia);
        console.log(JSON.stringify({s: S.fazAniversario(D.estreia, D.dia),
            t: T.fazAniversario(D.estreia, D.dia), g: T.justificar(f, D.dia).gancho,
            e: S.escolhaDoDia(L, D.dia).motivo}));
    """, {"estreia": estreia, "dia": dia, "filmes": _SESSENTA})
    assert out["s"] is out["t"] is esperado
    assert (out["g"] == "aniversario") is esperado
    assert (out["e"] == "aniversario") is esperado


@precisa_node
def test_excluido_nunca_e_escolhido_pelo_aniversario():
    """obsession-2025 no catálogo real, no dia do aniversário dele."""
    out = _node("""
        const o = D.find(f => f.slug === "obsession-2025");
        const dia = (Number(o.estreia.slice(0, 4)) + 1) + o.estreia.slice(4);
        console.log(JSON.stringify({estreia: o.estreia, dia, e: S.escolhaDoDia(D, dia).filme.slug,
            vencedores: D.filter(f => S.fazAniversario(f.estreia, dia)).map(f => f.slug)}));
    """, FILMES_REAIS)
    assert "obsession-2025" in out["vencedores"]       # o dia É aniversário dele
    assert out["e"] != "obsession-2025"


@precisa_node
def test_texto_de_aniversario_nao_repete_o_titulo_em_nenhum_filme_real():
    out = _node("""
        console.log(JSON.stringify(S.elegiveis(D).map(f => {
            const g = Object.assign({}, f, {estreia: "1990-10-19"});
            return [f.titulo, T.justificar(g, "2026-10-19").texto];
        })));
    """, FILMES_REAIS)
    for titulo, texto in out:
        assert texto.startswith(titulo + " faz aniversário de estreia hoje. ")
        resto = texto[len(titulo):]
        assert titulo not in resto, (titulo, texto)
        assert resto.split(". ", 1)[1].startswith(("Nele, ", "Está no catálogo")), texto


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
                // [rodada editorial] era `S.prateleiras(L, dia)`: a home agora
                // mostra a coleção do dia e os recém-chegados do dia
                const c = S.colecaoDoDia(L, dia);
                out.push([S.filmeDoDia(L, dia).slug,
                          c.colecao.chave + ":" + c.filmes.map(f => f.slug).join(","),
                          S.ordemDasColecoes(L).map(p => p.chave + ":" + p.filmes.map(f => f.slug).join(",")),
                          S.recemDoDia(L, dia).filmes.map(f => f.slug)]);
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


# ===========================================================================
# 8. [rodada 2] ASSUNTO COMUM DOMINANTE e TÍTULO NÃO LATINO (build_indice.py)
# ===========================================================================

def _linha(eixo, *mencoes_e_n):
    return {"eixo": eixo, "por_bucket": {
        b: {"mencoes": m, "de_n": n}
        for b, (m, n) in zip(("negativas", "medianas", "positivas"), mencoes_e_n)}}


def test_assunto_comum_soma_de_frequencias_nao_de_mencoes():
    """Com média zero, o excesso é a própria soma — isola a regra da SOMA."""
    f = _modulo_build_indice().assunto_comum_dominante
    # ritmo: 20/40 + 20/40 + 20/40 = 1,5 (60 menções); atuacao: 39/80 +
    # 1/40 + 39/40 = 1,4875 com 79 menções. Vence a FREQUÊNCIA, não a contagem.
    eixos = {"linhas": [_linha("ritmo", (20, 40), (20, 40), (20, 40)),
                        _linha("atuacao", (39, 80), (1, 40), (39, 40))]}
    assert f(eixos, {}) == "ritmo"


def test_assunto_comum_desempate_pela_menor_frequencia_e_depois_taxonomia():
    f = _modulo_build_indice().assunto_comum_dominante
    # mesma soma (1,5): vence o mais igualmente compartilhado (min maior)
    eixos = {"linhas": [_linha("ritmo", (40, 40), (10, 40), (10, 40)),
                        _linha("atuacao", (20, 40), (20, 40), (20, 40))]}
    assert f(eixos, {}) == "atuacao"
    # soma E mínimo iguais: vence a ordem da taxonomia (a primeira linha)
    eixos = {"linhas": [_linha("ritmo", (20, 40), (20, 40), (20, 40)),
                        _linha("atuacao", (20, 40), (20, 40), (20, 40))]}
    assert f(eixos, {}) == "ritmo"
    # empate exato com n diferentes (Fraction, não float): 1/3 == 9/27
    eixos = {"linhas": [_linha("ritmo", (9, 27), (10, 40), (10, 40)),
                        _linha("atuacao", (10, 30), (10, 40), (10, 40))]}
    assert f(eixos, {}) == "ritmo"


def test_assunto_comum_ignora_livre_e_zero():
    f = _modulo_build_indice().assunto_comum_dominante
    assert f({"linhas": [_linha("livre", (40, 40), (40, 40), (40, 40)),
                         _linha("ritmo", (1, 40), (0, 40), (0, 40))]}, {}) == "ritmo"
    assert f({"linhas": [_linha("ritmo", (0, 40), (0, 40), (0, 40))]}, {}) is None
    assert f({}, {}) is None


def test_assunto_comum_e_o_que_mais_excede_a_media_do_catalogo():
    """[rodada 2, decisão do dono] Vence o EXCESSO sobre a média, não a soma
    absoluta: roteiro tem a maior soma (2,0), mas é o habitual; ritmo, com
    1,2, está 0,6 acima da média dele."""
    f = _modulo_build_indice().assunto_comum_dominante
    eixos = {"linhas": [_linha("ritmo", (16, 40), (16, 40), (16, 40)),
                        _linha("roteiro_estrutura", (30, 40), (20, 40), (30, 40))]}
    media = {"ritmo": Fraction(3, 5), "roteiro_estrutura": Fraction(19, 10)}
    assert f(eixos, media) == "ritmo"
    assert f(eixos, {}) == "roteiro_estrutura"      # a regra antiga escolheria roteiro
    # nenhum eixo acima da média: não há assunto a nomear
    assert f(eixos, {"ritmo": Fraction(2), "roteiro_estrutura": Fraction(3)}) is None


def test_media_do_catalogo_conta_eixo_ausente_como_zero():
    bi = _modulo_build_indice()
    dados = {"catalogo": ["a", "b", "fora"], "filmes": {
        "a": {"eixos": {"linhas": [_linha("ritmo", (40, 40), (40, 40), (40, 40))]}},
        "b": {"eixos": {"linhas": [_linha("ritmo", (0, 40), (0, 40), (20, 40)),
                                   _linha("atuacao", (40, 40), (0, 40), (0, 40))]}}}}
    assert bi.media_do_catalogo(dados) == {"ritmo": Fraction(7, 4),
                                           "atuacao": Fraction(1, 2)}


def test_assunto_comum_real_espalhado_e_presente_em_todo_valorativo():
    """O defeito medido da definição absoluta: 66 de 79 em roteiro. Com a
    média do catálogo, nenhum eixo concentra metade dos valorativos e todo
    valorativo tem assunto."""
    val = [f for f in FILMES_REAIS if f["contraste"] == "valorativo"]
    assert all(f["assunto_comum"] for f in val)
    contagem = {}
    for f in val:
        contagem[f["assunto_comum"]] = contagem.get(f["assunto_comum"], 0) + 1
    assert max(contagem.values()) < len(val) / 2
    assert len(contagem) >= 5


def test_titulo_nao_latino_cai_no_letterboxd_e_depois_no_tmdb():
    f = _modulo_build_indice().titulos_de_exibicao
    assert f({"titulo": "A Cura"}, "cure") == ("A Cura", None)
    assert f({"titulo": "화녀", "identidade": {
        "titulo_letterboxd": "Woman of Fire",
        "titulo_tmdb_correspondente": "Hanyo"}}, "w") == ("Woman of Fire", "화녀")
    assert f({"titulo": "화녀", "identidade": {
        "titulo_letterboxd": None,
        "titulo_tmdb_correspondente": "Woman of Fire"}}, "w") == ("Woman of Fire", "화녀")
    # nenhuma alternativa latina: o original fica, sem linha secundária
    assert f({"titulo": "화녀", "identidade": {
        "titulo_letterboxd": "화녀"}}, "w") == ("화녀", None)
    assert f({"titulo": "화녀"}, "w") == ("화녀", None)


@precisa_node
def test_woman_of_fire_na_home_e_na_busca():
    wof = next(f for f in FILMES_REAIS if f["slug"] == "woman-of-fire")
    assert (wof["titulo"], wof["titulo_nativo"]) == ("Woman of Fire", "화녀")
    assert [f["slug"] for f in FILMES_REAIS if f["titulo_nativo"]] == ["woman-of-fire"]
    out = _node("""const m = B.criar(D);
        console.log(JSON.stringify([m.buscar("화녀"), m.buscar("woman of fire")]));""",
                FILMES_REAIS)
    for res in out:
        assert [r["slug"] for r in res] == ["woman-of-fire"]
        assert res[0]["titulo_nativo"] == "화녀"


# ===========================================================================
# 9. [rodada 3] LIMITE DE PRATELEIRAS, MÉDIA SEM EXCLUÍDOS, ESTREIA
# ===========================================================================

@precisa_node
def test_colecao_do_dia_percorre_todas_as_colecoes():
    """[rodada editorial] Substitui "limite de seis e retorno de toda
    prateleira" (a home não tem mais prateleiras): sem manchete a evitar,
    em N dias seguidos (N = nº de coleções) cada coleção é a do dia
    exatamente uma vez; com a manchete real, toda coleção aparece em
    qualquer janela de 2N dias."""
    out = _node("""
        const dia = i => new Date(Date.UTC(2026, 9, 19) + i * 86400000).toISOString().slice(0, 10);
        const n = S.ordemDasColecoes(D).length;
        const sem = [], com = [];
        for (let i = 0; i < 4 * n; i++) {
            sem.push(S.colecaoDoDia(D, dia(i), null).colecao.chave);
            com.push(S.colecaoDoDia(D, dia(i)).colecao.chave);
        }
        console.log(JSON.stringify({n, sem, com, chaves: S.ordemDasColecoes(D).map(c => c.chave)}));
    """, FILMES_REAIS)
    n, chaves = out["n"], set(out["chaves"])
    assert n > 4
    for i in range(0, len(out["sem"]) - n + 1):
        assert set(out["sem"][i:i + n]) == chaves
        assert len(out["sem"][i:i + n]) == len(set(out["sem"][i:i + n]))
    for i in range(0, len(out["com"]) - 2 * n + 1):
        assert set(out["com"][i:i + 2 * n]) == chaves, i


@precisa_node
def test_lista_de_exclusao_lida_pelo_build_e_a_mesma_do_node():
    out = _node("console.log(JSON.stringify(Object.keys(S.EXCLUIDOS)));")
    assert _modulo_build_indice().excluidos_da_home() == set(out) == {"obsession-2025"}


def test_media_do_catalogo_ignora_excluidos():
    bi = _modulo_build_indice()
    base = {"a": {"eixos": {"linhas": [_linha("ritmo", (10, 40), (10, 40), (10, 40))]}},
            "b": {"eixos": {"linhas": [_linha("ritmo", (30, 40), (30, 40), (30, 40))]}}}
    dados = {"catalogo": ["a", "b", "x"], "filmes": {
        **base, "x": {"eixos": {"linhas": [_linha("ritmo", (40, 40), (40, 40), (40, 40))]}}}}
    assert bi.media_do_catalogo(dados, {"x"}) == {"ritmo": Fraction(3, 2)}
    assert bi.media_do_catalogo(dados) == {"ritmo": Fraction(2)}


def test_media_real_e_a_dos_publicados_menos_os_excluidos():
    bi = _modulo_build_indice()
    dados = bi.ler_data_js()
    excl = bi.excluidos_da_home()
    sem = {"catalogo": [s for s in dados["catalogo"] if s not in excl],
           "filmes": dados["filmes"]}
    assert bi.media_do_catalogo(dados, excl) == bi.media_do_catalogo(sem)
    assert bi.media_do_catalogo(dados, excl) != bi.media_do_catalogo(dados)


def test_estreia_completa_em_todo_o_catalogo():
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", f["estreia"] or "")
               for f in FILMES_REAIS)
