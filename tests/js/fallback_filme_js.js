// Roda o fallback REAL de filme.js (o arquivo, não um port) contra os 35.
const fs = require('fs');
const src = fs.readFileSync('frontend/js/filme.js', 'utf8');

// Matcher que pula string, comentário de linha e comentário de bloco — sem
// isso, uma chave dentro de "{...}" num comentário desalinha a contagem.
function recorta(inicio, abre, fecha) {
  let j = inicio, depth = 0, started = false;
  while (j < src.length) {
    const c = src[j], d = src[j + 1];
    if (c === '/' && d === '/') { while (j < src.length && src[j] !== '\n') j++; continue; }
    if (c === '/' && d === '*') { j = src.indexOf('*/', j) + 2; continue; }
    if (c === '"' || c === "'") {
      const q = c; j++;
      while (j < src.length && src[j] !== q) { if (src[j] === '\\') j++; j++; }
      j++; continue;
    }
    if (c === abre) { depth++; started = true; }
    else if (c === fecha) { depth--; if (started && depth === 0) return src.slice(inicio, j + 1); }
    j++;
  }
  throw new Error('não fechou');
}

function fn(nome) {
  const i = src.indexOf(`function ${nome}(`);
  if (i < 0) throw new Error('não achei function ' + nome);
  return recorta(i, '{', '}');
}
function v(nome, abre, fecha) {
  const i = src.indexOf(`var ${nome} = `);
  if (i < 0) throw new Error('não achei var ' + nome);
  return `var ${nome} = ` + recorta(src.indexOf(abre, i), abre, fecha) + ';';
}

const partes = [
  v('EIXO_LABEL', '{', '}'),
  v('BANDAS_QUANTIFICADOR', '[', ']'),
  v('PLURAL', '{', '}'),
  fn('veredito'), fn('bucketDominante'), fn('eixoDeMaiorLift'),
  fn('eixoDeMaiorFrequencia'), fn('rotuloQuantificador'),
  fn('amostraReduzida'), fn('eixoEmFrase'),
];
eval(partes.join('\n'));

const raw = fs.readFileSync('frontend/js/data.js', 'utf8');
const data = JSON.parse(raw.split('window.ESPECTRO_DATA = ')[1].replace(/;\s*$/, ''));
const out = {};
for (const slug of data.catalogo) out[slug] = veredito(data.filmes[slug]);
process.stdout.write(JSON.stringify(out, null, 1));
