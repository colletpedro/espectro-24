"""[i18n] Infraestrutura de idioma (frontend/js/i18n.js).

Trava: i18n.js existe e é o PRIMEIRO script de cada página; todo
`I18N.registrar` tem as mesmas chaves em `pt` e `en`; a detecção de idioma
(URL > localStorage > navigator > en) e `t()` (fallback, placeholders,
funções) são EXECUTADAS sob node.
"""
import json
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FRONT = RAIZ / "frontend"
JS = FRONT / "js"
precisa_node = pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")

PAGINAS = ["index.html", "filme.html", "filmes/index.html", "creditos.html"]


def test_i18n_existe():
    assert (JS / "i18n.js").is_file()


@pytest.mark.parametrize("pagina", PAGINAS)
def test_i18n_e_o_primeiro_script(pagina):
    html = (FRONT / pagina).read_text(encoding="utf-8")
    # ignora scripts dentro de comentários HTML
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    primeiro = re.search(r"<script\b[^>]*>", html)
    assert primeiro, pagina
    assert re.search(r'src="(\.\./)?js/i18n\.js"', primeiro.group(0)), \
        f"{pagina}: o primeiro <script> deve ser js/i18n.js"


@pytest.mark.parametrize("pagina,arquivos", [
    ("index.html", ["data_en_home.js"]),
    ("filmes/index.html", ["data_en_home.js"]),
    ("filme.html", ["data_en_home.js", "data_en.js"]),
])
def test_data_en_so_carrega_em_ingles_e_logo_apos_o_i18n(pagina, arquivos):
    html = (FRONT / pagina).read_text(encoding="utf-8")
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    i = html.index("js/i18n.js")
    cond = re.search(r'<script>if \(window\.I18N && I18N\.idioma === "en"\)[^\n]*</script>', html)
    assert cond and cond.start() > i, pagina
    assert cond.start() < html.index("indice.js") if "indice.js" in html else True
    for a in arquivos:
        assert a in cond.group(0), (pagina, a)
    # nunca como <script src> incondicional
    assert not re.search(r'(?<![\'"])<script src="[^"]*data_en[^"]*"', html), pagina


def test_home_em_ingles_traduz_titulo_e_genero_e_a_busca_acha_pelos_dois():
    script = r"""
      const fs=require("fs"),vm=require("vm"),path=require("path");
      const J=path.join(%r,"frontend","js");
      const sb={console,Intl,URLSearchParams,location:{search:"?lang=en"}};sb.window=sb;
      vm.createContext(sb);
      for (const a of ["i18n.js","data_en_home.js","indice.js","busca.js"])
        vm.runInContext(fs.readFileSync(path.join(J,a),"utf8"),sb,{filename:a});
      const B=sb.ESPECTRO_BUSCA, I=sb.ESPECTRO_INDICE.filmes;
      const f=I.find(x=>x.slug==="cidade-de-deus");
      const motor=B.criar(I);
      console.log(JSON.stringify({titulo:f.titulo,pt:f.titulo_pt,generos:f.generos,
        gen:B.generoExibido("Ficção científica"),
        porEn:motor.buscar("city of god").map(x=>x.slug),
        porPt:motor.buscar("cidade de deus").map(x=>x.slug)}));
    """ % str(RAIZ)
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-1500:]
    d = json.loads(r.stdout)
    assert d["titulo"] == "City of God" and d["pt"] == "Cidade de Deus"
    assert "cidade-de-deus" in d["porEn"] and "cidade-de-deus" in d["porPt"]
    # o valor PT do gênero não muda (filtros comparam por ele); só o nome exibido
    assert d["generos"] == ["Drama", "Crime"] and d["gen"] == "Science Fiction"


def test_em_ingles_o_indice_usa_o_logo_en_ou_nenhum_nunca_o_logo_pt():
    script = r"""
      const fs=require("fs"),vm=require("vm"),path=require("path");
      const J=path.join(%r,"frontend","js");
      function carregar(search){
        const sb={console,Intl,URLSearchParams,location:{search}};sb.window=sb;
        vm.createContext(sb);
        const arqs=["i18n.js"].concat(search.includes("en")?["data_en_home.js"]:[],["indice.js","busca.js"]);
        for (const a of arqs) vm.runInContext(fs.readFileSync(path.join(J,a),"utf8"),sb,{filename:a});
        return sb.ESPECTRO_INDICE.filmes;
      }
      const en=carregar("?lang=en"), pt=carregar("?lang=pt");
      const g=(L,s)=>L.find(x=>x.slug===s);
      console.log(JSON.stringify({
        ptGetOut:g(pt,"get-out-2017").logo.path,
        enGetOut:g(en,"get-out-2017").logo,
        enDifere:g(en,"get-out-2017").titulo_difere_do_logo,
        enMulher:g(en,"woman-of-fire").logo,
        enMulherDifere:g(en,"woman-of-fire").titulo_difere_do_logo,
        ptLogosIntactos:pt.every(f=>f.logo_pt===undefined),
        enNenhumLogoPt:en.every(f=>!f.logo || f.logo.idioma==="en"||f.logo.idioma==="sem_idioma"),
        enGuardaPt:g(en,"get-out-2017").logo_pt.path}));
    """ % str(RAIZ)
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-1500:]
    d = json.loads(r.stdout)
    assert d["enGetOut"]["idioma"] == "en" and d["enGetOut"]["titulo"] == "Get Out"
    assert d["enGetOut"]["path"] != d["ptGetOut"] == d["enGuardaPt"]
    assert d["enDifere"] is False
    assert d["enMulher"] is None and d["enMulherDifere"] is False   # sem logo EN: texto
    assert d["ptLogosIntactos"] and d["enNenhumLogoPt"]


def _chaves_por_registro(fonte):
    """Pares (chaves_pt, chaves_en) na ordem em que aparecem."""
    marcas = [(m.start(), m.group(1)) for m in re.finditer(r"\b(pt|en):\s*\{", fonte)]
    blocos = []
    for i, (ini, lang) in enumerate(marcas):
        fim = marcas[i + 1][0] if i + 1 < len(marcas) else len(fonte)
        trecho = fonte[ini:fim]
        trecho = trecho.split("\n  });")[0] if "\n  });" in trecho else trecho
        trecho = trecho.split("});")[0]
        chaves = set(re.findall(r'(?:^|[{,\s])"([\w.:\-]+)"\s*:', trecho))
        blocos.append((lang, chaves))
    pares, i = [], 0
    while i < len(blocos):
        if blocos[i][0] == "pt" and i + 1 < len(blocos) and blocos[i + 1][0] == "en":
            pares.append((blocos[i][1], blocos[i + 1][1])); i += 2
        else:
            pytest.fail(f"bloco {blocos[i][0]} sem par pt/en")
    return pares


def test_todo_registrar_tem_as_mesmas_chaves_em_pt_e_en():
    achou = 0
    for arq in sorted(JS.glob("*.js")):
        if arq.name in ("data.js", "indice.js", "i18n.js"):
            continue
        fonte = arq.read_text(encoding="utf-8")
        if "I18N.registrar(" not in fonte and "I.registrar(" not in fonte:
            continue
        for pt, en in _chaves_por_registro(fonte):
            achou += 1
            assert pt, f"{arq.name}: registro sem chaves pt"
            assert pt == en, (f"{arq.name}: só em pt {sorted(pt - en)}; "
                              f"só em en {sorted(en - pt)}")
    assert achou >= 2  # textos_home.js e cabecalho.js, no mínimo


def _node(corpo, **env_js):
    script = textwrap.dedent(f"""
        const caminho = {json.dumps(str(JS / "i18n.js"))};
        function novo(amb) {{
          // um global novo por cenário: executa i18n.js num `this` próprio
          const vm = require("vm");
          const ctx = {{ console: {{ warn() {{ ctx.__avisos++; }} }}, __avisos: 0 }};
          Object.defineProperties(ctx, Object.getOwnPropertyDescriptors(amb));
          vm.createContext(ctx);
          vm.runInContext(require("fs").readFileSync(caminho, "utf8"), ctx);
          return ctx;
        }}
        const loja = (v) => ({{ getItem: () => v, setItem(k, x) {{ this.gravado = x; }} }});
        {textwrap.dedent(corpo)}
    """)
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@precisa_node
def test_deteccao_ordem_url_storage_navegador_padrao():
    out = _node("""
        const amb = (search, guardado, langs) => ({
          location: { search }, navigator: { languages: langs, language: langs[0] },
          localStorage: loja(guardado), document: { documentElement: {}, readyState: "complete",
            addEventListener() {}, querySelectorAll: () => [] } });
        const r = {};
        r.url_vence = novo(amb("?lang=en", "pt", ["pt-BR"])).I18N.idioma;
        r.storage_vence = novo(amb("", "en", ["pt-BR"])).I18N.idioma;
        r.navegador_pt = novo(amb("", null, ["pt-PT", "en"])).I18N.idioma;
        r.navegador_en = novo(amb("", null, ["en-GB", "pt"])).I18N.idioma;
        r.pula_outros = novo(amb("", null, ["fr-FR", "pt-BR"])).I18N.idioma;
        r.estrangeiro = novo(amb("", null, ["ja-JP", "fr"])).I18N.idioma;
        r.invalido = novo(amb("?lang=xx", null, ["fr"])).I18N.idioma;
        const c = novo(amb("?lang=en", null, ["pt-BR"]));
        r.grava = c.localStorage.gravado;
        r.html_lang = [novo(amb("?lang=en", null, ["pt"])).document.documentElement.lang,
                       novo(amb("?lang=pt", null, ["en"])).document.documentElement.lang];
        const quebra = novo({ location: { search: "" }, navigator: { languages: ["en"] },
          get localStorage() { throw new Error("bloqueado"); } });
        r.storage_quebrado = quebra.I18N.idioma;
        r.node_puro = novo({}).I18N.idioma;
        console.log(JSON.stringify(r));
    """)
    assert out == {
        "url_vence": "en", "storage_vence": "en", "navegador_pt": "pt",
        "navegador_en": "en", "pula_outros": "pt", "estrangeiro": "en",
        "invalido": "en", "grava": "en", "html_lang": ["en", "pt-BR"],
        "storage_quebrado": "en", "node_puro": "pt"}


@precisa_node
def test_t_fallback_placeholders_e_funcoes():
    out = _node("""
        const c = novo({ location: { search: "?lang=en" }, navigator: { languages: ["pt"] },
          localStorage: loja(null) });
        const I = c.I18N;
        I.registrar({ pt: { a: "só pt", b: "pt {x}", f: (v) => "fn " + v.n },
                      en: { b: "en {x}", f: (v) => "fn-en " + v.n } });
        const r = { a: I.t("a"), b: I.t("b", { x: 3 }), f: I.t("f", { n: 2 }),
                    falta: I.t("nao.existe"), falta2: I.t("nao.existe"), avisos: c.__avisos,
                    sem_var: I.t("b"), num: I.numero(1234.5) };
        console.log(JSON.stringify(r));
    """)
    assert out == {"a": "só pt", "b": "en 3", "f": "fn-en 2", "falta": "nao.existe",
                   "falta2": "nao.existe", "avisos": 1, "sem_var": "en {x}",
                   "num": "1,234.5"}


@precisa_node
def test_aplicar_traduz_data_attrs():
    out = _node("""
        const mk = (attrs) => { const a = { ...attrs }; return { _t: "", _h: "", attrs: a,
          getAttribute: (k) => a[k] ?? null, setAttribute: (k, v) => { a[k] = v; },
          set textContent(v) { this._t = v; }, set innerHTML(v) { this._h = v; } }; };
        const n1 = mk({ "data-i18n": "k" }), n2 = mk({ "data-i18n-html": "h" }),
              n3 = mk({ "data-i18n-attr": "aria-label:k;title:h" });
        const raiz = { querySelectorAll: (s) => s === "[data-i18n]" ? [n1]
          : s === "[data-i18n-html]" ? [n2] : [n3] };
        const c = novo({ location: { search: "?lang=en" }, localStorage: loja(null),
          navigator: { languages: ["pt"] }, document: { documentElement: {}, readyState: "complete",
            addEventListener() {}, querySelectorAll: () => [] } });
        c.I18N.registrar({ pt: { k: "chave", h: "<b>h</b>" }, en: { k: "key", h: "<b>H</b>" } });
        c.I18N.aplicar(raiz);
        console.log(JSON.stringify([n1._t, n2._h, n3.attrs["aria-label"], n3.attrs.title]));
    """)
    assert out == ["key", "<b>H</b>", "key", "<b>H</b>"]


@precisa_node
def test_sob_node_o_idioma_e_pt_e_o_texto_da_home_nao_muda():
    r = subprocess.run(["node", "-e", f"""
        const T = require({json.dumps(str(JS / 'textos_home.js'))});
        console.log(JSON.stringify([T.LINK_METODO, T.tituloDaDecada(1990),
          T.TITULO_PRATELEIRA['valorativo:ritmo'], T.chipDesde('2026-11-08')]));
    """], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == [
        "Método", "Seleção anos 90", "Todos falam do ritmo, ninguém concorda",
        "Recém-chegados desde 08/11/2026"]


@precisa_node
def test_textos_da_home_em_ingles():
    r = subprocess.run(["node", "-e", f"""
        globalThis.window = {{ location: {{ search: '?lang=en' }}, navigator: {{ languages: ['en'] }} }};
        globalThis.location = window.location; globalThis.navigator = window.navigator;
        const T = require({json.dumps(str(JS / 'textos_home.js'))});
        console.log(JSON.stringify([T.LINK_METODO, T.tituloDaDecada(1990),
          T.chipDesde('2026-11-08'), T.justificar({{titulo: 'Alien', slug: 'a'}}).texto]));
    """], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out[:3] == ["Method", "The 1990s selection", "New arrivals since Nov 8, 2026"]
    assert out[3].startswith("Alien is in the catalog with what HATERS, MIXED and FANS say")


def test_cabecalho_tem_o_seletor_acessivel():
    js = (JS / "cabecalho.js").read_text(encoding="utf-8")
    assert 'role", "group"' in js and "aria-pressed" in js and "definirIdioma" in js
    css = (FRONT / "css" / "styles.css").read_text(encoding="utf-8")
    assert ".idioma__botao:focus-visible" in css
