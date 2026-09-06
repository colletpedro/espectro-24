"""[v1.9.40] Hash perceptual dos STILLS — o dado que falta para a galeria
saber que duas candidatas são a MESMA imagem.

Por que existe: `_stills` (`ficha.py`) só via METADADO (`vote_average`,
`file_path`, dimensões), e metadado não distingue dois crops do mesmo
quadro de dois quadros diferentes. O defeito que isso produziu está
MEDIDO (ETAPA 0, 2026-09-05, os 5 filmes do estudo, 316 candidatas): nas
5 janelas de top-8 publicadas há 6 posições redundantes (34 imagens
distintas em 40 posições), contra 1 em 40 nas janelas equivalentes do
MEIO do pool. Em `wonka` o top-8 mostrava 5 imagens distintas em 8
posições — 3 crops do mesmo plano da loja (#1/#6/#7) e 2 crops da mesma
arte de campanha (#2/#4).

pHash E NÃO dHash — escolha MEDIDA, não preferência.
--------------------------------------------------
Num conjunto rotulado à mão de 155 pares tirados desses 5 filmes (censo
completo dos pares com pHash<=18, N=72, mais amostra estratificada por
faixa de dHash), com o rótulo "as duas leem como a MESMA imagem numa
galeria" (mesmo enquadramento variando crop, gradação ou fração de
segundo):

    critério        TP  FP  FN   precisão  recall
    pHash <= 10     27   0  25     1.000    0.574
    pHash <= 12     31   0  16     1.000    0.660
    pHash <= 14     39   2   8     0.951    0.830   <- ESCOLHIDO
    pHash <= 16     44   6   3     0.880    0.936
    dHash <= 10     26   0  21     1.000    0.553
    dHash <= 12     30   1  17     0.968    0.638
    dHash <= 14     36   2  11     0.947    0.766
    (matriz sobre o censo pHash<=18, N=72, S=47)

pHash domina dHash em TODO ponto de precisão comparável: com precisão
1.000, pHash chega a recall 0.660 e dHash a 0.553. A razão é o acervo:
as duplicatas do TMDB são o mesmo quadro RE-GRADADO e RE-CORTADO, e o
dHash (gradiente horizontal entre pixels vizinhos) reage ao contraste
local que a gradação muda, enquanto o pHash (DCT de baixa frequência)
reage à estrutura, que o corte preserva.

LIMIAR = 14 pela regra declarada antes de olhar a tabela: o MAIOR limiar
cuja precisão fica >= 0.95 (no máximo 1 descarte errado a cada 20). O
custo é assimétrico e é isso que a regra codifica — um falso positivo
joga fora UMA candidata distinta de um pool de 17 a 119 (barato); um
falso negativo devolve à página o defeito que este módulo existe para
consertar.

O QUE O LIMIAR NÃO PEGA — e não vai pegar subindo o número.
-----------------------------------------------------------
Recall 0.830 não é 1.0, e a fatia que escapa tem nome: "mesmo plano,
escala e gradação muito diferentes". Casos reais medidos: `wonka` #1 vs
#6 (mesma cena da loja, plano aberto vs fechado) dá pHash=34 e dHash=45
— distância de par ALEATÓRIO; `anatomy-of-a-fall` #1 vs #2 (mesmo plano,
gradação diferente) dá pHash=38. Nenhum limiar utilizável separa esses
casos sem colapsar imagens não relacionadas. **A dedup perceptual é um
piso, não uma garantia**, e é por isso que ela vem acompanhada da
amostragem espalhada (`_amostra_espalhada`, `ficha.py`): a segunda
defesa não depende de reconhecer a duplicata, só de não escolher duas
vizinhas do ranking.

Cache: as imagens são baixadas UMA vez em `w300` (largura suficiente
para o pHash de 8x8 e ~20 kB por arquivo) em `dados/cache/_stills_w300/`
— mesmo estatuto do cache do TMDB (`.gitignore`, §3[B]: artefato de rede
reconstruível, nunca fonte). Reexecutar o backfill não rebaixa nada.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

# Limiar de distância de Hamming entre pHashes — MEDIDO, ver a docstring
# do módulo. Não é palpite e não deve ser mexido sem refazer a matriz.
LIMIAR_PHASH = 14

# w300 é o menor tamanho servido pelo TMDB que ainda é folgado para um
# pHash 8x8 (a imagem é reduzida a 32x32 antes da DCT de qualquer forma):
# baixar w780 ou o original só gastaria banda e disco sem mudar um bit do
# hash.
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"

# Uma `Session` de módulo, e não `requests.get` solto: são milhares de
# arquivos de ~20 kB, e sem conexão reaproveitada o custo de abrir TCP+TLS
# a cada imagem domina o download inteiro (medido no backfill dos 35: ~17
# imagens/min sem sessão, contra ~140/min com ela). Só é usada quando o
# chamador não passa a sua própria `session`.
_SESSAO = requests.Session()


class HashIndisponivel(RuntimeError):
    """Pillow/imagehash ausentes, ou a imagem não pôde ser lida.

    Existe para que a galeria DEGRADE em vez de quebrar: sem hash, a
    dedup é pulada e a lista sai como saía antes da v1.9.40 — pior, mas
    publicada. O pipeline nunca cai por causa de uma imagem.
    """


def _dir_cache(raiz: Path | None = None) -> Path:
    raiz = raiz or Path(__file__).resolve().parents[2]
    return raiz / "dados" / "cache" / "_stills_w300"


def caminho_local(file_path: str, *, raiz: Path | None = None) -> Path:
    """Onde a `file_path` do TMDB (`/abc.jpg`) mora no cache local."""
    return _dir_cache(raiz) / file_path.lstrip("/")


def baixar(file_path: str, *, session=None, raiz: Path | None = None) -> Path:
    """Baixa `file_path` em w300 se ainda não estiver em cache. Idempotente."""
    destino = caminho_local(file_path, raiz=raiz)
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    sess = session or _SESSAO
    resp = sess.get(f"{TMDB_IMAGE_BASE}{file_path}", timeout=30)
    if resp.status_code != 200:
        raise HashIndisponivel(f"{file_path}: HTTP {resp.status_code}")
    destino.write_bytes(resp.content)
    return destino


def phash(file_path: str, *, session=None, raiz: Path | None = None) -> str:
    """pHash hexadecimal da imagem, baixando-a se preciso."""
    try:
        import imagehash
        from PIL import Image
    except ImportError as e:  # pragma: no cover - ambiente sem as libs
        raise HashIndisponivel(f"dependência ausente: {e}") from e
    p = baixar(file_path, session=session, raiz=raiz)
    try:
        with Image.open(p) as im:
            return str(imagehash.phash(im.convert("RGB")))
    except Exception as e:  # imagem truncada/corrompida no cache
        raise HashIndisponivel(f"{file_path}: {e}") from e


def hashes_de(file_paths, *, session=None, raiz: Path | None = None,
              memo: Path | None = None) -> dict[str, str]:
    """`{file_path: phash_hex}` para as que derem — as que falharem ficam
    DE FORA do dicionário, e `_deduplicar` trata ausência como "não sei
    comparar" (a candidata sobrevive), nunca como "é duplicata".

    `memo` é um JSON opcional com hashes já calculados; é lido e reescrito
    para que o backfill dos 35 não recalcule 2.000 pHashes a cada rodada.
    """
    cache: dict[str, str] = {}
    if memo and memo.exists():
        cache = json.loads(memo.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    novos = False
    for fp in file_paths:
        if fp in cache:
            out[fp] = cache[fp]
            continue
        try:
            h = phash(fp, session=session, raiz=raiz)
        except HashIndisponivel:
            continue
        out[fp] = cache[fp] = h
        novos = True
    if memo and novos:
        memo.parent.mkdir(parents=True, exist_ok=True)
        memo.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
    return out


def distancia(a: str, b: str) -> int:
    """Distância de Hamming entre dois pHashes hexadecimais.

    Implementada em cima de `int(.., 16)` e não de `imagehash.hex_to_hash`
    para que a comparação (e portanto a dedup e os testes dela) não
    dependa das libs de imagem estarem instaladas — só a GERAÇÃO do hash
    depende.
    """
    return bin(int(a, 16) ^ int(b, 16)).count("1")
