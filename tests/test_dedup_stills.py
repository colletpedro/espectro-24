"""[v1.9.40] Dedup perceptual + amostragem espalhada da galeria de stills
(§3[F]). Nenhum teste aqui toca rede ou Pillow: os pHashes são INJETADOS,
que é exatamente o motivo de `_deduplicar` receber `hashes` em vez de
calculá-los."""
import pytest

from espectro24.ficha import (
    LIMIAR_PHASH,
    PISO_STILLS,
    TETO_STILLS,
    _amostra_espalhada,
    _deduplicar,
    _stills,
)
from espectro24.still_hash import distancia


def _b(path, va=1.0, w=1920, h=1080):
    return {"file_path": path, "vote_average": va, "vote_count": 1,
            "width": w, "height": h, "iso_639_1": None}


# hashes de 16 dígitos hex (64 bits, o formato do pHash 8x8)
H_A = "0000000000000000"
H_A_PERTO = "0000000000000007"       # 3 bits de distância de H_A
H_B = "ffffffffffffffff"             # 64 bits de H_A


def test_distancia_e_hamming_de_verdade():
    assert distancia(H_A, H_A) == 0
    assert distancia(H_A, H_A_PERTO) == 3
    assert distancia(H_A, H_B) == 64


# --- _deduplicar ---

def test_duas_candidatas_com_hash_proximo_viram_uma():
    c = [_b("/a.jpg", va=5.0), _b("/b.jpg", va=4.0)]
    fora = _deduplicar(c, {"/a.jpg": H_A, "/b.jpg": H_A_PERTO})
    assert [x["file_path"] for x in fora] == ["/a.jpg"]


def test_candidatas_distantes_sobrevivem_as_duas():
    c = [_b("/a.jpg", va=5.0), _b("/b.jpg", va=4.0)]
    fora = _deduplicar(c, {"/a.jpg": H_A, "/b.jpg": H_B})
    assert [x["file_path"] for x in fora] == ["/a.jpg", "/b.jpg"]


def test_no_limiar_exato_ainda_e_duplicata_um_acima_nao_e():
    """O limiar é `<=`, e o teste fixa isso: 14 colapsa, 15 não."""
    quase = f"{(1 << LIMIAR_PHASH) - 1:016x}"          # exatamente 14 bits
    passou = f"{(1 << (LIMIAR_PHASH + 1)) - 1:016x}"   # 15 bits
    assert distancia(H_A, quase) == LIMIAR_PHASH
    assert distancia(H_A, passou) == LIMIAR_PHASH + 1
    c = [_b("/a.jpg", va=5.0), _b("/b.jpg", va=4.0)]
    assert len(_deduplicar(c, {"/a.jpg": H_A, "/b.jpg": quase})) == 1
    assert len(_deduplicar(c, {"/a.jpg": H_A, "/b.jpg": passou})) == 2


def test_o_representante_do_grupo_e_o_de_MAIOR_RESOLUCAO():
    """Regra explícita (§3[F] v1.9.40): em empate de hash fica a de maior
    resolução — não a mais votada, não a primeira da lista."""
    c = [_b("/pequena.jpg", va=9.0, w=1280, h=720),
         _b("/grande.jpg", va=1.0, w=3840, h=2160)]
    fora = _deduplicar(c, {"/pequena.jpg": H_A, "/grande.jpg": H_A_PERTO})
    assert [x["file_path"] for x in fora] == ["/grande.jpg"]


def test_empate_de_resolucao_desempata_por_file_path_crescente():
    c = [_b("/z.jpg", va=9.0), _b("/a.jpg", va=1.0)]
    fora = _deduplicar(c, {"/z.jpg": H_A, "/a.jpg": H_A})
    assert [x["file_path"] for x in fora] == ["/a.jpg"]


def test_o_grupo_herda_a_POSICAO_do_seu_membro_melhor_colocado():
    """Colapsar não pode promover: o representante entra no lugar da
    candidata mais votada do grupo, não no seu próprio lugar."""
    c = [_b("/topo.jpg", va=9.0, w=1280, h=720),      # 1º, baixa resolução
         _b("/meio.jpg", va=5.0, w=1920, h=1080),     # distinta
         _b("/fim.jpg", va=1.0, w=3840, h=2160)]      # dup de /topo.jpg
    fora = _deduplicar(c, {"/topo.jpg": H_A, "/fim.jpg": H_A_PERTO,
                           "/meio.jpg": H_B})
    # /fim.jpg representa o grupo (maior resolução) MAS na posição de /topo
    assert [x["file_path"] for x in fora] == ["/fim.jpg", "/meio.jpg"]


def test_fecho_transitivo_colapsa_a_corrente_inteira():
    """A~B e B~C sem A~C: os três viram um só. Custo conhecido e aceito —
    ver a docstring de `_deduplicar`."""
    a, b, c_ = "0000000000000000", "00000000000000ff", "000000000000ffff"
    assert distancia(a, b) <= LIMIAR_PHASH and distancia(b, c_) <= LIMIAR_PHASH
    assert distancia(a, c_) > LIMIAR_PHASH
    itens = [_b("/a.jpg", va=3.0), _b("/b.jpg", va=2.0), _b("/c.jpg", va=1.0)]
    fora = _deduplicar(itens, {"/a.jpg": a, "/b.jpg": b, "/c.jpg": c_})
    assert len(fora) == 1


def test_sem_hashes_a_dedup_e_pulada_e_nada_e_perdido():
    c = [_b("/a.jpg", va=5.0), _b("/b.jpg", va=4.0)]
    assert _deduplicar(c, None) == c
    assert _deduplicar(c, {}) == c


def test_candidata_SEM_hash_nunca_e_descartada():
    """Ausência de hash é 'não sei comparar', nunca 'é duplicata'."""
    c = [_b("/a.jpg", va=5.0), _b("/sem_hash.jpg", va=4.0)]
    fora = _deduplicar(c, {"/a.jpg": H_A})
    assert [x["file_path"] for x in fora] == ["/a.jpg", "/sem_hash.jpg"]


def test_dedup_e_deterministica_independente_da_ordem_de_uniao():
    """Mesma entrada -> mesma saída, byte a byte, em 20 execuções."""
    itens = [_b(f"/{i:02d}.jpg", va=float(20 - i)) for i in range(20)]
    hashes = {f"/{i:02d}.jpg": f"{(i % 3) * 0x0f0f0f0f0f0f0f0f:016x}"
              for i in range(20)}
    primeira = [x["file_path"] for x in _deduplicar(itens, hashes)]
    for _ in range(20):
        assert [x["file_path"] for x in _deduplicar(itens, hashes)] == primeira


# --- _amostra_espalhada ---

def test_amostra_devolve_a_lista_inteira_quando_cabe_no_teto():
    itens = [_b(f"/{i}.jpg") for i in range(TETO_STILLS)]
    assert _amostra_espalhada(itens, TETO_STILLS) == itens
    assert _amostra_espalhada(itens[:3], TETO_STILLS) == itens[:3]


def test_amostra_espalha_em_vez_de_cortar_o_topo():
    itens = [_b(f"/{i:03d}.jpg") for i in range(60)]
    fora = [x["file_path"] for x in _amostra_espalhada(itens, 8)]
    assert fora == ["/000.jpg", "/007.jpg", "/015.jpg", "/022.jpg",
                    "/030.jpg", "/037.jpg", "/045.jpg", "/052.jpg"]
    assert len(fora) == 8


def test_o_primeiro_item_continua_sendo_o_mais_votado():
    """A amostragem espalha as OUTRAS posições; a primeira é a curadoria
    do TMDB, e é a que mais gente vê."""
    itens = [_b(f"/{i:03d}.jpg") for i in range(119)]
    assert _amostra_espalhada(itens, 8)[0] is itens[0]


def test_vizinhas_no_ranking_nunca_caem_na_mesma_faixa():
    """A garantia que a amostragem dá contra a duplicata que o pHash NÃO
    reconhece: com n >= 2*teto, dois itens adjacentes nunca são ambos
    escolhidos.

    [v1.9.41] A garantia em si não mudou — o que mudou foi quantos filmes
    a alcançam, porque o teto subiu de 8 para 16 e o alvo virou n >= 32:
    30 dos 34 longas, contra 33 antes. Os quatro de fora estão nomeados na
    docstring de `_amostra_espalhada`. Este teste continua provando a
    propriedade matemática, com o mesmo rigor, no teto vigente."""
    for n in range(2 * TETO_STILLS, 130):
        idx = [(k * n) // TETO_STILLS for k in range(TETO_STILLS)]
        assert all(b - a >= 2 for a, b in zip(idx, idx[1:])), n


def test_amostra_e_deterministica():
    itens = [_b(f"/{i:03d}.jpg") for i in range(97)]
    esperado = _amostra_espalhada(itens, 8)
    for _ in range(10):
        assert _amostra_espalhada(itens, 8) == esperado


# --- integração em _stills ---

def test_stills_aplica_dedup_ANTES_do_teto_e_do_piso():
    """A ordem importa: deduplicar depois do teto deixaria a galeria com
    menos de 8 itens sem que o pool tivesse acabado."""
    backdrops = [_b("/hero.jpg", va=100.0)]
    # 4 crops do mesmo quadro (hash igual) + 3 distintas
    backdrops += [_b(f"/dup{i}.jpg", va=9.0 - i) for i in range(4)]
    backdrops += [_b(f"/ok{i}.jpg", va=1.0 - i / 10) for i in range(3)]
    hashes = {f"/dup{i}.jpg": H_A for i in range(4)}
    # hashes bem separados entre si (>= 21 bits de distância par a par)
    hashes.update(dict(zip(["/ok0.jpg", "/ok1.jpg", "/ok2.jpg"],
                           ["ffffffffffffffff", "ffffffff00000000",
                            "ffff0000ffff0000"])))
    fora = _stills({"backdrops": backdrops}, "/hero.jpg", hashes=hashes)
    caminhos = [x["still_path"] for x in fora]
    assert len([c for c in caminhos if c.startswith("/dup")]) == 1
    # [v1.9.42] o hero entra na lista (pinado em 1º) e conta no total: 4 → 5
    assert caminhos[0] == "/hero.jpg"
    assert len(caminhos) == 5


def test_stills_cai_no_piso_quando_a_dedup_derruba_abaixo_dele():
    """Consequência aceita: se o filme só tinha variações do mesmo quadro,
    a galeria some inteira (PISO_STILLS) em vez de mostrar 1 imagem."""
    backdrops = [_b("/hero.jpg", va=100.0)]
    backdrops += [_b(f"/dup{i}.jpg", va=float(9 - i)) for i in range(6)]
    hashes = {f"/dup{i}.jpg": H_A for i in range(6)}
    assert _stills({"backdrops": backdrops}, "/hero.jpg", hashes=hashes) == []
    # sem dedup, os mesmos 6 passariam do piso — é a dedup que zera
    assert len(_stills({"backdrops": backdrops}, "/hero.jpg")) >= PISO_STILLS


def test_stills_sem_hashes_se_comporta_como_antes_da_v1_9_40():
    """Compatibilidade: sem hash, mesma lista de sempre (top-N por
    vote_average) — a ausência de dado nunca muda o resultado em silêncio
    para pior nem para melhor."""
    backdrops = [_b("/hero.jpg", va=100.0)]
    backdrops += [_b(f"/p{i:02d}.jpg", va=float(i)) for i in range(5)]
    fora = [x["still_path"] for x in _stills({"backdrops": backdrops}, "/hero.jpg")]
    # [v1.9.42] com o hero pinado em 1º; o resto na ordem de sempre
    assert fora == ["/hero.jpg", "/p04.jpg", "/p03.jpg", "/p02.jpg",
                    "/p01.jpg", "/p00.jpg"]


# --- a rede da dedup passa pela sessão INJETADA ---

class _SessaoDuble:
    """Registra as URLs pedidas e devolve 404 em tudo — o suficiente para
    provar por onde a requisição passou."""

    def __init__(self):
        self.urls = []

    def get(self, url, **kw):
        self.urls.append(url)
        return type("R", (), {"status_code": 404, "content": b""})()


def test_hash_das_candidatas_usa_a_sessao_injetada(tmp_path, monkeypatch):
    """Regressão de um defeito REAL: `_hashes_dos_candidatos` abria conexão
    própria, e com isso a suíte de `test_ficha.py` passou a baixar imagens
    do TMDB de verdade (58 testes de 0,1 s viraram 67 s). A ficha inteira é
    testável offline; a dedup não pode ser a exceção."""
    from espectro24 import ficha as F

    # cache redirecionado para o tmp_path: nada deste teste toca
    # `dados/cache/` do repositório (a sessão dublê devolve 404, mas a
    # garantia não pode depender disso)
    monkeypatch.setattr("espectro24.still_hash._dir_cache",
                        lambda raiz=None: tmp_path / "cache")
    sess = _SessaoDuble()
    detalhes = {"images": {"backdrops": [
        {"file_path": "/a.jpg", "iso_639_1": None, "width": 1920, "height": 1080},
        {"file_path": "/b.jpg", "iso_639_1": None, "width": 1920, "height": 1080},
    ]}}
    assert F._hashes_dos_candidatos(detalhes, session=sess) == {}
    assert sess.urls == ["https://image.tmdb.org/t/p/w300/a.jpg",
                         "https://image.tmdb.org/t/p/w300/b.jpg"]


def test_hash_so_pede_o_que_ja_passou_nos_filtros_baratos(tmp_path, monkeypatch):
    """Não baixa o que `_stills` descartaria de graça — arte com idioma
    declarado e recorte fora de 16:9."""
    from espectro24 import ficha as F

    monkeypatch.setattr("espectro24.still_hash._dir_cache",
                        lambda raiz=None: tmp_path / "cache")
    sess = _SessaoDuble()
    detalhes = {"images": {"backdrops": [
        {"file_path": "/ok.jpg", "iso_639_1": None, "width": 1920, "height": 1080},
        {"file_path": "/com_texto.jpg", "iso_639_1": "pt", "width": 1920, "height": 1080},
        {"file_path": "/quadrada.jpg", "iso_639_1": None, "width": 1440, "height": 1080},
    ]}}
    F._hashes_dos_candidatos(detalhes, session=sess)
    assert sess.urls == ["https://image.tmdb.org/t/p/w300/ok.jpg"]
