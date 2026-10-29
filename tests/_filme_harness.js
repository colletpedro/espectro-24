/* Harness do teste da REGRA DE PRODUTO da página do filme
   (tests/test_filme_regra_de_produto.py).

   Roda o `filme.js` REAL contra um DOM mínimo, uma vez por filme do
   `data.js`, e imprime em JSON o que a regra decide: a ordem das colunas
   de bullets, o layout (2 ou 3), o estado aberto/fechado do Mixed, a
   quantidade de bullets por grupo, a ordem das condições e o peso do meio.
   O projeto não tem runner de JS com DOM; este é o menor DOM que o
   `filme.js` precisa, e ele serve igual ao `filme.js` de antes e de depois
   de uma mudança de forma.

   uso: node tests/_filme_harness.js <caminho do filme.js> [slug ...]

   variáveis de ambiente:
     HARNESS_TOPO=estatico   roda com `?topo=estatico`
     HARNESS_PCT=frase|barra roda com `?pct=`
     HARNESS_COLECOES=1      imprime só a ordem das coleções e os recém-chegados
     HARNESS_PATCH='{"slug":..., "lado":..., "bucket":..., "ordem":[...]}'
                             troca o `bucket_origem` das condições de um lado
                             e a `ordem_colunas` de UM filme (caso sintético)
*/
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const RAIZ = path.resolve(__dirname, "..");
const JS = path.join(RAIZ, "frontend", "js");
const arquivoFilme = process.argv[2];
const filtro = process.argv.slice(3);

class El {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.parentNode = null;
    this.attrs = {};
    this.dataset = {};
    this.className = "";
    this._text = "";
    this._html = "";
    this.hidden = false;
    this.style = { setProperty() {} };
  }
  get classList() {
    const self = this;
    const lista = () => self.className.split(/\s+/).filter(Boolean);
    return {
      add(c) { if (!lista().includes(c)) self.className = lista().concat(c).join(" "); },
      remove(c) { self.className = lista().filter((x) => x !== c).join(" "); },
      contains(c) { return lista().includes(c); },
      toggle(c, on) {
        const tem = lista().includes(c);
        const quer = on === undefined ? !tem : !!on;
        if (quer && !tem) this.add(c); else if (!quer && tem) this.remove(c);
      },
    };
  }
  get firstChild() { return this.children[0] || null; }
  get firstElementChild() { return this.children[0] || null; }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(""); }
  set textContent(v) { this.children = []; this._text = String(v); }
  get innerHTML() { return this._html; }
  set innerHTML(v) { this.children = []; this._text = ""; this._html = String(v); }
  appendChild(c) {
    if (c.parentNode) c.parentNode.removeChild(c);
    c.parentNode = this; this.children.push(c); return c;
  }
  insertBefore(c, ref) {
    if (c.parentNode) c.parentNode.removeChild(c);
    c.parentNode = this;
    const i = ref ? this.children.indexOf(ref) : -1;
    if (i < 0) this.children.push(c); else this.children.splice(i, 0, c);
    return c;
  }
  removeChild(c) { this.children = this.children.filter((x) => x !== c); c.parentNode = null; return c; }
  replaceChild(novo, velho) { this.insertBefore(novo, velho); this.removeChild(velho); return velho; }
  remove() { if (this.parentNode) this.parentNode.removeChild(this); }
  setAttribute(k, v) {
    this.attrs[k] = String(v);
    if (k.startsWith("data-")) this.dataset[k.slice(5).replace(/-(\w)/g, (_, c) => c.toUpperCase())] = String(v);
  }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  removeAttribute(k) { delete this.attrs[k]; }
  addEventListener() {}
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
  querySelectorAll(sel) {
    // só seletores simples: tag ou .classe
    const saida = [];
    const casa = (e) => sel.startsWith(".")
      ? e.classList.contains(sel.slice(1)) : e.tagName === sel.toUpperCase();
    (function varrer(n) { n.children.forEach((c) => { if (casa(c)) saida.push(c); varrer(c); }); })(this);
    return saida;
  }
  get offsetWidth() { return 0; }
  scrollIntoView() {}
}

const tem = (e, c) => e.classList.contains(c);
function achar(raiz, classe) {
  const saida = [];
  (function varrer(n) { n.children.forEach((c) => { if (tem(c, classe)) saida.push(c); varrer(c); }); })(raiz);
  return saida;
}
const norm = (s) => String(s || "").replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();

function novoContexto() {
  const elementos = {};
  const doc = {
    createElement: (t) => new El(t),
    createTextNode: (t) => { const e = new El("#text"); e._text = String(t); return e; },
    getElementById: (id) => elementos[id] || null,
    documentElement: new El("html"),
    body: new El("body"),
    title: "",
    activeElement: null,
    addEventListener() {},
  };
  const location = { search: "" };
  const matchMedia = (q) => ({ matches: true, media: q, addEventListener() {}, addListener() {} });
  // `window` É o global do contexto: os módulos UMD penduram em `this`
  const sandbox = {
    document: doc, console, Intl, URLSearchParams, location, matchMedia,
    setTimeout: () => 0, clearTimeout() {}, setInterval: () => 0, clearInterval() {},
    requestAnimationFrame: () => 0, Image: function () {},
    addEventListener() {},
  };
  sandbox.window = sandbox;
  const ctx = vm.createContext(sandbox);
  return { ctx, janela: sandbox, doc, elementos, location };
}

function carregar(ctx, arquivo) {
  vm.runInContext(fs.readFileSync(path.join(JS, arquivo), "utf8"), ctx, { filename: arquivo });
}

const base = novoContexto();
["data.js", "indice.js", "poster.js", "busca.js", "selecao.js", "textos_home.js", "cartoes.js"]
  .forEach((a) => carregar(base.ctx, a));
const DATA = base.janela.ESPECTRO_DATA;
const codigo = fs.readFileSync(arquivoFilme, "utf8");

function extrair(app, topo) {
  const s = {};
  const sg = achar(app, "sentiment-groups")[0];
  s.colunas = sg ? sg.children.filter((c) => tem(c, "group")).map((c) => c.dataset.group) : null;
  s.layout = sg ? (tem(sg, "sentiment-groups--3") ? "3" : "2") : null;
  const meio = achar(app, "disclosure--meio")[0];
  s.meio = meio ? { aberto: !!meio.open, resumo: norm(meio.children[0] && meio.children[0].innerHTML) } : null;
  s.bullets = {};
  achar(app, "group").forEach((g) => { s.bullets[g.dataset.group] = achar(g, "theme").length; });
  s.condicoes = achar(app, "decide__col").map((c) => ({
    lado: tem(c, "decide__col--pos") ? "pos" : "neg",
    n: achar(c, "decide__text").length,
  }));
  const pm = achar(app, "decide__meio")[0];
  s.peso_meio = pm ? pm.textContent : null;

  // --- o resto da página (testes da forma nova) ---
  s.secoes = app.children.map((c) => c.className.split(" ")[0]);
  s.topo = topo && topo.dataset.chave || null;
  const v = app.children.find((c) => tem(c, "verdict") || tem(c, "verdict-absent"));
  s.veredito = v ? { classe: v.className, origem: v.dataset.origem || null, texto: v.textContent } : null;
  s.rotulos = achar(app, "decide__col").map((c) => {
    const p = achar(c, "decide__peso")[0];
    return { lado: tem(c, "decide__col--pos") ? "pos" : "neg", grupo: p ? p.dataset.grupo || null : null,
             texto: p ? p.textContent : null,
             itens: achar(c, "decide__text").map((t) => t.textContent) };
  });
  s.faixas_de_notas = achar(app, "group__notas").map((n) => n.textContent)
    .concat(achar(app, "proportion__legend-notas").map((n) => n.textContent));
  const gal = achar(app, "fp-galeria")[0];
  s.galeria = gal ? achar(gal, "fp-galeria__item").length : 0;
  const col = achar(app, "fp-colecao")[0];
  s.colecao = col ? { origem: col.dataset.origem, chave: col.dataset.chave || null,
                      titulo: achar(col, "section-label")[0].textContent,
                      slugs: achar(col, "ed-cartao").map((a) => a.dataset.slug),
                      href: achar(col, "ed-link")[0].href } : null;
  // o peso de cada grupo (cabeçalho) e de cada coluna (para decidir)
  const pesoDe = (el) => {
    const extra = achar(el, "peso-extra")[0];
    const barra = achar(el, "peso-barra")[0];
    const fill = barra && achar(barra, "peso-barra__fill")[0];
    return { texto: el.textContent, extra: extra ? extra.textContent : null,
             barra: barra ? { largura: fill.style.width, aria: barra.getAttribute("aria-label"), g: barra.attrs["data-g"] || null } : null };
  };
  s.pesos_grupo = achar(app, "group").map((g) => Object.assign({ g: g.dataset.group }, achar(g, "group__share")[0] ? pesoDe(achar(g, "group__share")[0]) : { texto: null }));
  s.pesos_coluna = achar(app, "decide__col").map((c) => {
    const p = achar(c, "decide__peso")[0];
    return p ? pesoDe(p) : null;
  });
  s.texto_da_pagina = app.children.map((c) => c.textContent).join("\n");
  return s;
}

if (process.env.HARNESS_COLECOES) {
  const S = base.janela.ESPECTRO_SELECAO;
  const filmes = base.janela.ESPECTRO_INDICE.filmes;
  const rec = S.recemChegados(filmes);
  process.stdout.write(JSON.stringify({
    ordem: S.ordemDasColecoes(filmes).map((c) => ({ chave: c.chave, slugs: c.filmes.map((f) => f.slug) })),
    recem: rec ? rec.filmes.map((f) => f.slug) : [],
    excluidos: Object.keys(S.EXCLUIDOS),
  }));
  process.exit(0);
}
if (process.env.HARNESS_PATCH) {
  const pt = JSON.parse(process.env.HARNESS_PATCH);
  const f = DATA.filmes[pt.slug];
  if (pt.lado) f.condicoes[pt.lado].forEach((c) => { c.bucket_origem = pt.bucket; });
  if (pt.ordem) f.condicoes.ordem_colunas = pt.ordem;
  // `share`: {bucket: share_real}; `peso_pct`: {lado: peso_pct} (e o texto)
  Object.entries(pt.share || {}).forEach(([b, v]) => {
    f.buckets.forEach((x) => { if (x.bucket === b) x.share_real = v; });
  });
  Object.entries(pt.peso_pct || {}).forEach(([lado, v]) => {
    f.condicoes.peso[lado].peso_pct = v; f.condicoes.peso[lado].peso_texto = "~" + v + "% das notas";
  });
}

const saida = {};
Object.keys(DATA.filmes).sort().filter((k) => !filtro.length || filtro.includes(k)).forEach((slug) => {
  const { ctx, janela, elementos, location } = novoContexto();
  Object.assign(janela, {
    ESPECTRO_DATA: DATA, ESPECTRO_INDICE: base.janela.ESPECTRO_INDICE,
    ESPECTRO_POSTER: base.janela.ESPECTRO_POSTER, ESPECTRO_CARTOES: base.janela.ESPECTRO_CARTOES,
    ESPECTRO_SELECAO: base.janela.ESPECTRO_SELECAO, ESPECTRO_TEXTOS: base.janela.ESPECTRO_TEXTOS,
  });
  ["app", "topo", "footerReviews"].forEach((id) => { elementos[id] = new El("div"); });
  location.search = "?slug=" + slug + (process.env.HARNESS_TOPO ? "&topo=" + process.env.HARNESS_TOPO : "")
    + (process.env.HARNESS_PCT ? "&pct=" + process.env.HARNESS_PCT : "");
  // as entradas da entrada: dados de entrada da regra, para o teste saber
  // quando um republish mudou o INPUT (e não a regra)
  const f = DATA.filmes[slug];
  const entrada = {
    share: Object.fromEntries((f.buckets || []).map((b) => [b.bucket, b.share_real])),
    ordem_colunas: f.condicoes ? f.condicoes.ordem_colunas : null,
    n_temas: Object.fromEntries((f.buckets || []).map((b) => [b.bucket, (b.temas || []).length])),
    n_cond: f.condicoes ? [(f.condicoes.vale_a_pena || []).length, (f.condicoes.talvez_evite || []).length] : null,
  };
  try {
    vm.runInContext(codigo, ctx, { filename: "filme.js" });
    saida[slug] = { entrada, ...extrair(elementos.app, elementos.topo) };
  } catch (e) {
    saida[slug] = { entrada, erro: String(e && e.stack || e) };
  }
});
process.stdout.write(JSON.stringify(saida));
