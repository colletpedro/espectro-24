"""[v1.9.35, §0 terceira exceção] Testes do estágio de CONDIÇÕES DE DECISÃO.

**Todo validador entra em PAR**: um caso que reprova e um que passa limpo.
A razão está registrada no estudo (`DESENHO_CONDICOES_DE_DECISAO.md`):
validador sem o par é armadilha — ele elimina candidatos bons e empurra o
filme para o fallback, que é o custo caro e medido do §3[V].

Os casos que reprovam são REAIS: saíram da auditoria manual do mockup do
`napoleon-2023` e das rodadas 1 e 2 do estudo.
"""
import json
from pathlib import Path

import pytest

from espectro24 import condicoes as C

RAIZ = Path(__file__).resolve().parent.parent
RESULTADO = RAIZ / "resultado"


def _idx(slug):
    return C.indexar(json.loads((RESULTADO / f"{slug}.json").read_text(
        encoding="utf-8")))


def _idx_de_piso():
    """Fixture mínimo para a regra de piso, agora sem caso real no catálogo."""
    def bucket(nome, share):
        return {
            "bucket": nome, "modo": "reduzido", "estado_piso": "sem_numero",
            "share_real": share,
            "temas": [{
                "tema": "Tema de teste", "exemplo_parafraseado": "Exemplo.",
                "mencoes_aproximadas": 2, "n_reviews_analisadas": 5,
            }],
        }
    return C.indexar({"buckets": [
        bucket("negativas", 10), bucket("medianas", 20),
        bucket("positivas", 70),
    ]})


@pytest.fixture(scope="module")
def nap():
    return _idx("napoleon-2023")


@pytest.fixture(scope="module")
def pdays():
    return _idx("perfect-days-2023")


@pytest.fixture(scope="module")
def godfather():
    return _idx("the-godfather")


def _cond(lado, texto, tema):
    return {"lado": lado, "texto": texto, "tema_origem": tema}


# ===========================================================================
# VALIDADOR 1 — ÂNCORA, em par
# ===========================================================================

def test_ancora_reprova_a_condicao_fabricada_do_mockup(nap):
    """A condição FABRICADA da auditoria manual: "não se incomoda com licença
    histórica" atribuída ao tema FANS "Incentivo à pesquisa histórica", cujo
    exemplo descreve um EFEITO (despertou curiosidade), não tolerância a
    imprecisão. Ela cai porque não consegue nomear o tema que diz citar."""
    alvo = next(t for t in nap.values()
                if t["tema"] == "Incentivo à pesquisa histórica")
    flags = C.validar(
        _cond("vale_a_pena", "não se incomoda com licença histórica",
              alvo["id"]), nap)
    assert "ancora_nao_verificavel" in flags


def test_ancora_deixa_passar_limpa_a_condicao_correta_do_mockup(nap):
    """A metade obrigatória do par: a condição CORRETA do mesmo mockup, sobre
    o mesmo filme, sai sem nenhuma flag."""
    alvo = next(t for t in nap.values()
                if t["tema"] == "Abordagem pessoal e íntima do personagem")
    assert C.validar(
        _cond("vale_a_pena", "quer um Napoleão íntimo, não o estadista",
              alvo["id"]), nap) == []


def test_ancora_inexistente_e_erro_de_pertinencia(nap):
    assert C.validar(_cond("vale_a_pena", "quer qualquer coisa", "POS-Z"),
                     nap) == ["ancora_inexistente"]


def test_ancora_de_outro_bucket_reprova(nap):
    """[v1.9.35] Substitui o validador de corroboração por valência, removido
    por precisão medida de 7,7%. Este é exato: cada lado só usa os temas do
    seu bucket."""
    neg = next(t for t in nap.values() if t["bucket"] == "negativas")
    flags = C.validar(_cond("vale_a_pena", "quer o retrato do líder",
                            neg["id"]), nap)
    assert "ancora_de_outro_bucket" in flags


# ===========================================================================
# VALIDADOR 2 — DISCRIMINAÇÃO, em par ISOLADO
# ===========================================================================

def test_discriminacao_reprova_condicao_que_so_usa_palavra_compartilhada(pdays):
    """"gosta de um ritmo lento" não serve: as HATERS chamam o MESMO ritmo
    lento de tédio. Par isolado — nenhuma outra flag dispara."""
    alvo = next(t for t in pdays.values()
                if t["tema"] == "Ritmo lento e contemplativo")
    assert C.validar(_cond("vale_a_pena", "gosta de um ritmo lento",
                           alvo["id"]), pdays) == ["sem_discriminacao"]


def test_discriminacao_deixa_passar_a_palavra_que_separa(pdays):
    """Mesmo tema, mesma ideia, com a palavra que decide qual leitura o
    leitor está comprando."""
    alvo = next(t for t in pdays.values()
                if t["tema"] == "Ritmo lento e contemplativo")
    assert C.validar(
        _cond("vale_a_pena", "quer um ritmo contemplativo, quase meditativo",
              alvo["id"]), pdays) == []


# ===========================================================================
# `exemplo_verbatim` — em par, com o CONTROLE que fixa o teto em 4
# ===========================================================================

def test_exemplo_verbatim_reprova_copia_real_da_rodada_1(nap):
    """Cópia real medida no estudo: quatro palavras de conteúdo seguidas do
    `exemplo_parafraseado`."""
    alvo = next(t for t in nap.values()
                if t["tema"] == "Abordagem pessoal e íntima do personagem")
    flags = C.validar(
        _cond("vale_a_pena",
              "prefere ver as inseguranças e a vida pessoal de Napoleão",
              alvo["id"]), nap)
    assert "exemplo_verbatim" in flags


def test_exemplo_verbatim_deixa_passar_parafrase_propria(nap):
    """MESMO tema, mesmas ideias, palavras reordenadas."""
    alvo = next(t for t in nap.values()
                if t["tema"] == "Abordagem pessoal e íntima do personagem")
    assert C.validar(
        _cond("vale_a_pena", "quer o Napoleão pessoal e inseguro, não o herói",
              alvo["id"]), nap) == []


def test_exemplo_verbatim_nao_reprova_enumeracao_de_tres(nap):
    """O CONTROLE que fixa o teto em 4 e não em 3. "fotografia, figurinos e
    cenários" é uma enumeração sem sinônimo disponível — reprová-la é o falso
    positivo caro que o §3[V] mediu três vezes. Em 3, este teste falha."""
    alvo = next(t for t in nap.values()
                if t["tema"] == "Impacto visual e direção de arte")
    assert C.validar(
        _cond("vale_a_pena",
              "valoriza fotografia, figurinos e cenários deslumbrantes",
              alvo["id"]), nap) == []


# ===========================================================================
# `tema_verbatim` e a exceção de NOME PRÓPRIO
# ===========================================================================

def test_tema_verbatim_reprova_copia_do_rotulo():
    assert C.palavras_copiaveis("Ritmo lento e contemplativo") == [
        "ritmo", "lento", "contemplativo"]


def test_nome_proprio_nao_conta_como_palavra_copiavel():
    """[v1.9.35] MEDIDO: 3 dos 5 disparos de `tema_verbatim` na rodada 2 eram
    "Descaracterização do Arthur Fleck" — nomear a personagem exige o nome
    dela. Sem a exceção, a regra reprova quem faz a única coisa possível."""
    assert C.palavras_copiaveis("Descaracterização do Arthur Fleck") == [
        "descaracterizacao"]
    assert C.palavras_copiaveis("Transformação de Michael Corleone") == [
        "transformacao"]
    assert C.palavras_copiaveis("Atuação de Timothée Chalamet") == ["atuacao"]


def test_tema_verbatim_desligado_para_tema_que_e_nome_proprio(godfather):
    alvo = next(t for t in godfather.values()
                if t["tema"] == "Transformação de Michael Corleone")
    flags = C.validar(
        _cond("vale_a_pena", "quer ver a transformação de Michael Corleone",
              alvo["id"]), godfather)
    assert "tema_verbatim" not in flags


# ===========================================================================
# `quantidade_escrita` — o rótulo é do CÓDIGO
# ===========================================================================

def test_quantidade_escrita_reprova(nap):
    alvo = next(t for t in nap.values() if t["tema"] == "Retrato de Napoleão")
    flags = C.validar(
        _cond("talvez_evite",
              "é como a maioria, que reprova o retrato infantilizado",
              alvo["id"]), nap)
    assert "quantidade_escrita" in flags


def test_digito_reprova(nap):
    alvo = next(t for t in nap.values() if t["tema"] == "Retrato de Napoleão")
    assert "digito" in C.validar(
        _cond("talvez_evite", "rejeita 2 horas de retrato infantilizado",
              alvo["id"]), nap)


# ===========================================================================
# SELEÇÃO — do CÓDIGO
# ===========================================================================

def test_selecao_base_e_a_ordem_publicada(nap):
    sel = C.selecionar(nap, par_obrigatorio=False)
    assert [t["id"] for t in sel["vale_a_pena"]] == ["POS-A", "POS-B", "POS-C"]
    assert [t["id"] for t in sel["talvez_evite"]] == ["NEG-A", "NEG-B", "NEG-C"]


def test_ordem_publicada_e_mencoes_decrescente_nos_35():
    """MEDIDO em 105 de 105 buckets. Se algum filme novo quebrar isso, a
    justificativa registrada da regra de seleção deixa de valer e este teste
    é onde isso aparece."""
    for caminho in sorted(RESULTADO.glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        for b in d.get("buckets") or []:
            ms = [t["mencoes_aproximadas"] for t in (b.get("temas") or [])]
            assert ms == sorted(ms, reverse=True), (d["slug"], b["bucket"])


def test_par_obrigatorio_traz_o_contra_tema_do_napoleon(nap):
    """O caso nomeado do estudo: os três grupos acham as batalhas bonitas, e
    só as HATERS dizem que elas carecem de tática. Sem o par obrigatório,
    `Batalhas decepcionantes` (6/40, ordem 5) nunca entra."""
    sem = {t["id"] for t in C.selecionar(nap, par_obrigatorio=False)["talvez_evite"]}
    com = {t["id"] for t in C.selecionar(nap)["talvez_evite"]}
    alvo = next(t for t in nap.values()
                if t["tema"] == "Batalhas decepcionantes")
    assert alvo["id"] not in sem
    assert alvo["id"] in com


def test_par_obrigatorio_acrescenta_e_nunca_substitui(nap):
    base = C.selecionar(nap, par_obrigatorio=False)
    com = C.selecionar(nap)
    for lado in C.LADOS:
        assert {t["id"] for t in base[lado]} <= {t["id"] for t in com[lado]}


def test_par_obrigatorio_e_estavel_e_nao_cascateia(nap):
    """Calculado uma vez sobre a seleção base: duas chamadas dão o mesmo
    resultado, e ele não depende da ordem de varredura dos lados."""
    a = {l: [t["id"] for t in C.selecionar(nap)[l]] for l in C.LADOS}
    b = {l: [t["id"] for t in C.selecionar(nap)[l]] for l in C.LADOS}
    assert a == b


def test_teto_por_lado_respeitado():
    for caminho in sorted(RESULTADO.glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        sel = C.selecionar(C.indexar(d))
        for lado in C.LADOS:
            assert len(sel[lado]) <= C.MAX_POR_LADO


# ===========================================================================
# ORDEM DAS COLUNAS e PESO — a correção 1b
# ===========================================================================

def test_coluna_do_grupo_maior_vem_primeiro(godfather, nap):
    """`the-godfather` é 2/5/93: abre por quem recomenda."""
    assert C.ordem_das_colunas(godfather)[0] == "vale_a_pena"
    cats = _idx("cats-2019")           # 86/7/7
    assert C.ordem_das_colunas(cats)[0] == "talvez_evite"


def test_peso_do_lado_carrega_o_share_e_a_nota_de_amostra(godfather):
    """O conserto da razão nº 1: o leitor precisa sair sabendo que um lado é
    2% e o outro 93%. `rotulo_forca` foi medido como incapaz disso."""
    vale = C.peso_do_lado(godfather, "vale_a_pena")
    evite = C.peso_do_lado(godfather, "talvez_evite")
    assert vale["peso_texto"] == "~93% das notas"
    assert evite["peso_texto"] == "~2% das notas"
    # n=30, modo reduzido -> a ressalva que o veredito carrega e as condições
    # não carregavam
    assert evite["nota_de_amostra"] == "amostra pequena"
    assert vale["nota_de_amostra"] is None


def test_peso_e_publicado_mesmo_em_bucket_de_piso():
    """§3[C3]: o peso vem do histograma de NOTAS e não depende de haver
    review com texto. O piso suprime o QUANTIFICADOR, nunca o peso."""
    obs = _idx_de_piso()
    for lado in C.LADOS:
        assert C.peso_do_lado(obs, lado)["peso_pct"] is not None
    assert all(t["rotulo_forca"] is None for t in obs.values())


def test_rotulo_forca_suprimido_nos_estados_de_piso():
    obs = _idx_de_piso()
    assert all(t["rotulo_forca"] is None for t in obs.values())
    normal = _idx("interstellar")
    assert all(t["rotulo_forca"] is not None for t in normal.values())


# ===========================================================================
# BRIEFING — as garantias por construção
# ===========================================================================

def test_briefing_nao_tem_algarismo_proibido_em_nenhum_filme():
    """A garantia "zero dígitos" do §3[V] é mais fraca aqui do que lá — o
    briefing precisa carregar a paráfrase (P4 REVISADO) e a paráfrase não é
    limpa. MEDIDO: 1 tema do catálogo tem algarismo, e ele está fora do
    top-3. Este teste é onde um filme novo que reabra o buraco aparece.

    [piloto de expansão] Era `..._em_nenhum_dos_35` e afirmava
    `not any(ch.isdigit() ...)` sobre o texto inteiro. O piloto trouxe o
    primeiro caso real no top-3 — `pinocchio-2022` NEG-F, "Comparação com o
    clássico de 1940" — e o dono aprovou a exceção de ano em nome de tema.
    A asserção agora é `algarismos_proibidos_no_briefing == []`: o ano na
    forma estreita passa; qualquer outro algarismo, em qualquer linha, falha
    como antes."""
    for caminho in sorted(RESULTADO.glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        b = C.montar_briefing(d)
        if b is None:
            continue
        assert C.algarismos_proibidos_no_briefing(b) == [], d["slug"]


def _output_com_tema(tema, exemplo="o grupo comenta isso com frequência"):
    """Um filme mínimo cujo tema de topo nas positivas é `tema`."""
    def bucket(nome, t, ex):
        return {"bucket": nome, "estado_piso": "completa", "modo": "completo",
                "share_real": 40,
                "temas": [{"tema": t, "mencoes_aproximadas": 12,
                           "n_reviews_analisadas": 40,
                           "exemplo_parafraseado": ex}]}
    return {"slug": "x", "buckets": [
        bucket("positivas", tema, exemplo),
        bucket("negativas", "Ritmo lento", "acharam o andamento arrastado")]}


def test_briefing_nao_tem_algarismo_ano_em_nome_de_tema_PASSA():
    """O caso real, e o único lado que a exceção abre."""
    d = json.loads((RESULTADO / "pinocchio-2022.json").read_text(
        encoding="utf-8"))
    b = C.montar_briefing(d)
    texto = C.serializar_briefing(b)
    assert "Comparação com o clássico de 1940" in texto   # o ano CHEGA ao modelo
    assert C.algarismos_proibidos_no_briefing(b) == []


@pytest.mark.parametrize("tema", [
    "Comparação com o clássico de 1940",
    "Versão de 2022",
    "Diferenças para o original de 1940, da Disney",
    "Remake do filme lançado em 1978",
    # [2026-09-16, ABERTO.md B5] `para` — caso real `2001-a-space-odyssey`.
    "Efeitos visuais impressionantes para 1968",
])
def test_briefing_nao_tem_algarismo_formas_de_ano_admitidas(tema):
    b = C.montar_briefing(_output_com_tema(tema))
    assert C.algarismos_proibidos_no_briefing(b) == []
    assert C.anos_em_nome_de_tema(tema)


@pytest.mark.parametrize("tema", [
    # [2026-09-16, ABERTO.md B5] Década — casos reais `chinatown` (4 dígitos,
    # fecha a frase) e `a-brighter-summer-day` (2 dígitos, NÃO fecha — "nos
    # anos 60 e os reflexos..." — é o caso que exigiu o sufixo mais solto).
    "Recriação de Los Angeles nos anos 1930",
    "O peso histórico de Taiwan nos anos 60 e os reflexos na juventude",
])
def test_briefing_nao_tem_algarismo_decada_em_anos_admitida(tema):
    b = C.montar_briefing(_output_com_tema(tema))
    assert C.algarismos_proibidos_no_briefing(b) == []


@pytest.mark.parametrize("tema", [
    # [2026-09-16, ABERTO.md B5] Formato de tela — caso real
    # `the-spongebob-movie-search-for-squarepants`.
    "Animação em 3D bem executada",
    "Comparação entre as versões 2D e 3D",
])
def test_briefing_nao_tem_algarismo_formato_de_tela_admitido(tema):
    b = C.montar_briefing(_output_com_tema(tema))
    assert C.algarismos_proibidos_no_briefing(b) == []


@pytest.mark.parametrize("tema", [
    # quantidade, percentual, contagem, denominador — o que a regra protege
    "Os primeiros 30 minutos",
    "34% das notas",
    "Clássico de 1940%",
    "3 de 40 reviews",
    "Nota 4,5 de 5",
    "Mais de 2000 figurantes",
    "Elenco de 2000 figurantes",
    "Cerca de 1990",
    "Em torno de 2000",
    "Por volta de 1990",
    "Duração de 1940 minutos",
    # algarismo que não é ano de quatro dígitos
    "Parte 2 da franquia",
    "Sexta-Feira 13",
    "Versão de 19400",
    "Versão de 1940.5",
    # ano legítimo FORA da forma — a estreiteza é deliberada: o destino é
    # reescrever o tema sem o ano
    "O remake de 2022 e o original",
    "1940 contra 2022",
])
def test_briefing_nao_tem_algarismo_de_quantidade_FALHA(tema):
    b = C.montar_briefing(_output_com_tema(tema))
    assert C.algarismos_proibidos_no_briefing(b), tema


def test_briefing_decada_como_locucao_de_quantidade_continua_falhando():
    """A exclusão de locução (`_LOCUCAO_DE_QUANTIDADE`, a mesma do ano) vale
    igual para década — sem isto, ficaria furada só para esta forma nova.
    A palavra que precede `anos` diretamente é o que a guarda olha; "mais"
    está no conjunto."""
    b = C.montar_briefing(_output_com_tema("Queria mais anos 2000 de trama"))
    assert C.algarismos_proibidos_no_briefing(b) == ["2000"]


def test_briefing_nao_tem_algarismo_ano_na_forma_admitida_na_parafrase_PASSA():
    """[2026-09-16, ABERTO.md B5] Substitui
    `..._na_parafrase_nao_tem_excecao`: aquele teste travava uma decisão que
    não sobreviveu ao achado 1 da revisão de 100% do lote
    `expansao-44-2026-09-16` — o validador de PRODUÇÃO (`validar`/`digito`)
    nunca checou a paráfrase, só a condição publicada, então "a exceção é só
    do nome do tema" descrevia um alcance que a paráfrase nunca teve sob a
    R4 real. Casos reais que motivaram a correção:
    `all-quiet-on-the-western-front-2022`/NEG-A ("da versão de 1930") e
    `woman-of-fire`/NEG-? ("a versão original de 1960") — ambos citam o ano
    de uma adaptação anterior, na MESMA forma admitida no tema, só que na
    paráfrase. A máscara agora cobre os dois campos."""
    b = C.montar_briefing(_output_com_tema(
        "Comparação com o clássico",
        exemplo="muitos compararam com o clássico de 1940"))
    assert C.algarismos_proibidos_no_briefing(b) == []


def test_briefing_nao_tem_algarismo_decada_na_parafrase_agora_admitida():
    """[2026-09-16, ABERTO.md B5] Substitui
    `..._decada_na_parafrase_continua_reprovada` — aquele teste travava
    "década não é a exceção", decisão que o dono reverteu no mesmo dia
    (`"passa todos menos o porco rosso"`, sobre os 5 casos genuínos
    restantes da revisão de 100%). Caso real: `chinatown`/POS-C, "recriação
    detalhada de Los Angeles nos anos 1930" — descreve a ÉPOCA do enredo, e
    agora é tratado como o mesmo tipo de referência temporal que o ano de
    obra já admitia."""
    b = C.montar_briefing(_output_com_tema(
        "Fotografia e estética",
        exemplo="elogiam a recriação de Los Angeles nos anos 1930"))
    assert C.algarismos_proibidos_no_briefing(b) == []


def test_a_excecao_de_ano_nao_chega_ao_texto_da_condicao():
    """A exceção é do INSUMO. A condição que o leitor lê continua com zero
    algarismo — mesmo quando repete o ano que o tema admitiu."""
    d = json.loads((RESULTADO / "pinocchio-2022.json").read_text(
        encoding="utf-8"))
    idx = C.indexar(d)
    cond = {"lado": "talvez_evite", "tema_origem": "NEG-F",
            "texto": "espera a mesma ousadia do clássico de 1940"}
    assert idx["NEG-F"]["tema"] == "Comparação com o clássico de 1940"
    assert "digito" in C.validar(cond, idx)


def test_briefing_nao_nomeia_o_filme():
    d = json.loads((RESULTADO / "napoleon-2023.json").read_text(
        encoding="utf-8"))
    texto = C.serializar_briefing(C.montar_briefing(d))
    assert "Napoleon" not in texto


def test_briefing_e_deterministico():
    d = json.loads((RESULTADO / "hereditary.json").read_text(encoding="utf-8"))
    a = C.serializar_briefing(C.montar_briefing(d))
    b = C.serializar_briefing(C.montar_briefing(d))
    assert a == b


def test_sem_temas_devolve_none():
    """Mesma política aditiva de ficha e distribuição: sem insumo, a chave
    não é emitida — nunca um bloco montado sobre buraco."""
    vazio = {"slug": "x", "buckets": [
        {"bucket": "negativas", "temas": [], "estado_piso": "sem_analise"},
        {"bucket": "positivas", "temas": [], "estado_piso": "sem_analise"}]}
    assert C.montar_briefing(vazio) is None
    assert C.gerar(vazio) is None


# ===========================================================================
# ORQUESTRAÇÃO — com LLM injetado, zero rede
# ===========================================================================

def _fake(respostas):
    it = iter(respostas)

    def gerar(system, user):
        return next(it), {"prompt_tokens": 1, "completion_tokens": 1,
                          "cache_hit_tokens": 0, "cache_miss_tokens": 0}, 0.01
    return gerar


def test_gerar_publica_so_condicao_limpa_e_registra_a_descartada():
    d = json.loads((RESULTADO / "napoleon-2023.json").read_text(
        encoding="utf-8"))
    ruim = json.dumps({"vale_a_pena": [
        {"texto": "gosta de 3 batalhas", "tema_origem": "POS-C"}],
        "talvez_evite": []})
    out = C.gerar(d, n=1, gerar=_fake([ruim, ruim]))
    assert out["vale_a_pena"] == []
    assert out["descartadas"][0]["flags"]
    assert out["origem"] == "abstencao"


def test_gerar_ordena_a_coluna_pela_ordem_publicada():
    d = json.loads((RESULTADO / "napoleon-2023.json").read_text(
        encoding="utf-8"))
    fora_de_ordem = json.dumps({
        "vale_a_pena": [
            {"texto": "aprecia sequências de combate brutais e autênticas",
             "tema_origem": "POS-C"},
            {"texto": "busca interpretações com dualidade e vulnerabilidade",
             "tema_origem": "POS-A"}],
        "talvez_evite": []})
    out = C.gerar(d, n=1, gerar=_fake([fora_de_ordem]))
    ids = [c["tema_origem"] for c in out["vale_a_pena"]]
    assert ids == sorted(ids)


def test_selecao_entre_candidatos_prefere_cobertura_e_nao_silencio():
    """A chave primária é COBERTURA, não limpeza: a saída perfeitamente limpa
    é a lista vazia, e premiar isso otimizaria na direção do defeito. A
    abstenção precisa ser possível sem ser premiada."""
    d = json.loads((RESULTADO / "napoleon-2023.json").read_text(
        encoding="utf-8"))
    b = C.montar_briefing(d)
    vazio = C.extrair(json.dumps({"vale_a_pena": [], "talvez_evite": []}))
    cheio = C.extrair(json.dumps({"vale_a_pena": [
        {"texto": "busca interpretações com dualidade e vulnerabilidade",
         "tema_origem": "POS-A"}], "talvez_evite": []}))
    assert C.selecionar_candidato([vazio, cheio], b)["indice"] == 1


def test_extrair_tolera_prosa_em_volta_do_json():
    bruto = ('Claro! {"vale_a_pena": [{"texto": "a", "tema_origem": "POS-A"}],'
             ' "talvez_evite": []} pronto.')
    assert C.extrair(bruto)["vale_a_pena"][0]["tema_origem"] == "POS-A"


def test_extrair_devolve_estrutura_vazia_em_lixo():
    """[piloto de expansão] A estrutura vazia ganhou `sem_condicao: []` — a
    mesma forma que `extrair` devolve para JSON bom, para o consumidor nunca
    distinguir "lixo" de "nada declarado" por chave ausente."""
    vazio = {"vale_a_pena": [], "talvez_evite": [], "sem_condicao": []}
    assert C.extrair("não é json") == vazio
    assert C.extrair("") == vazio


def test_estagio_registrado_em_config():
    from espectro24.config import MODELO_POR_ESTAGIO, PROVIDER_POR_ESTAGIO
    assert PROVIDER_POR_ESTAGIO[C.ESTAGIO]
    assert MODELO_POR_ESTAGIO[C.ESTAGIO]


# ===========================================================================
# [v1.9.36] ANTI-SPOILER — a marca de briefing, e o que ela NÃO é
# ===========================================================================

def test_marca_de_spoiler_aparece_nos_temas_de_desfecho():
    """A marca é sinalização de BRIEFING, não validador. Ela existe porque o
    filtro de §3[D] roda sobre os TEMAS e a condição muda a força
    ilocucionária: o bullet relata, a condição instrui."""
    d = json.loads((RESULTADO / "pearl-2022.json").read_text(encoding="utf-8"))
    texto = C.serializar_briefing(C.montar_briefing(d))
    assert "ATENÇÃO" in texto


def test_marca_de_spoiler_nao_reprova_condicao(nap):
    """**Ela NUNCA vira flag.** Medida sobre as 266 condições da rodada 3, a
    detecção lexical tem precisão de 15,8% — pior que o léxico de valência
    que a rodada 3 removeu por 7,7%. Como validador descartaria condição boa,
    que é o custo caro do §3[V]; como marca de briefing, um falso positivo só
    deixa o modelo mais cuidadoso. Assimetria de custo, não descuido."""
    alvo = next(t for t in nap.values() if t["tema"] == "Retrato de Napoleão")
    cond = _cond("talvez_evite",
                 "rejeita ver o líder retratado como figura fraca", alvo["id"])
    assert "spoiler" not in " ".join(C.validar(cond, nap))


def test_briefing_do_retry_tambem_nao_tem_algarismo():
    """O retry é concatenado à mensagem do USUÁRIO, então a garantia de zero
    algarismo vale sobre ele também. Citar "a regra 9c" a quebrava."""
    medida = {"condicoes": [{"lado": "vale_a_pena", "texto": "x",
                             "tema_origem": "POS-A", "flags": ["digito"]}]}
    assert not any(ch.isdigit() for ch in C.prompt_retry(medida))


# ===========================================================================
# [v1.9.36] PERFIL DE LEITOR — a marca estreita
# ===========================================================================

def test_perfil_de_leitor_reprova_a_segunda_pessoa_explicita(nap):
    alvo = next(t for t in nap.values() if t["tema"] == "Retrato de Napoleão")
    flags = C.validar(
        _cond("talvez_evite",
              "você é o tipo de pessoa que rejeita o retrato infantilizado",
              alvo["id"]), nap)
    assert "perfil_de_leitor" in flags


def test_perfil_de_leitor_nao_reprova_a_qualidade_concreta(nap):
    """A metade obrigatória do par. A condição certa nomeia a qualidade da
    obra e deixa o leitor se reconhecer — ela não pode ser confundida com
    perfil."""
    alvo = next(t for t in nap.values()
                if t["tema"] == "Impacto visual e direção de arte")
    assert C.validar(
        _cond("vale_a_pena",
              "valoriza fotografia, figurinos e cenários deslumbrantes",
              alvo["id"]), nap) == []


# ===========================================================================
# [v1.9.36] NÃO-REGRESSÃO NOMINAL — as três frases citadas como boas
# ===========================================================================
# **O teste que protege o que funciona.** O refinamento da rodada 4 mudou o
# enquadramento do prompt, e o risco declarado da mudança é converter frase
# boa em preferência abstrata ("prioriza X em vez de Y"), que PERDE a
# qualidade concreta e inventa uma oposição que a paráfrase talvez não tenha.
#
# Estas três existem no catálogo e são o registro-alvo. O teste trava o que
# elas têm em comum: âncora limpa, nenhuma flag, e nenhum molde de
# preferência abstrata.

FRASES_DE_REFERENCIA = [
    ("cidade-de-deus", "Cinematografia e direção", "vale_a_pena",
     "aprecia uma direção marcante com fotografia dinâmica e forte apelo visual"),
    ("im-still-here-2024", "Atuações excepcionais", "vale_a_pena",
     "valoriza atuações comoventes guiadas por expressões sutis e silêncios "
     "expressivos"),
    ("perfect-days-2023", "Ritmo lento e contemplativo", "vale_a_pena",
     "busca uma experiência meditativa e aceita um ritmo vagaroso para "
     "mergulhar no personagem"),
]


def test_as_tres_frases_de_referencia_continuam_limpas():
    for slug, tema, lado, texto in FRASES_DE_REFERENCIA:
        idx = _idx(slug)
        alvo = next(t for t in idx.values() if t["tema"] == tema)
        flags = C.validar(_cond(lado, texto, alvo["id"]), idx)
        assert flags == [], (slug, texto, flags)


def test_o_molde_de_preferencia_abstrata_e_o_anti_padrao():
    """A regressão que o refinamento existe para impedir, escrita como teste:
    trocar a qualidade concreta por uma oposição inventada PERDE informação.
    A versão abstrata não consegue ancorar — ela não nomeia mais o assunto do
    tema —, e é o validador de âncora que a barra."""
    idx = _idx("cidade-de-deus")
    alvo = next(t for t in idx.values() if t["tema"] == "Cinematografia e direção")
    concreta = _cond("vale_a_pena",
                     "aprecia uma direção marcante com fotografia dinâmica e "
                     "forte apelo visual", alvo["id"])
    abstrata = _cond("vale_a_pena",
                     "prioriza impacto visual em vez de uma abordagem discreta",
                     alvo["id"])
    assert C.validar(concreta, idx) == []
    assert "ancora_nao_verificavel" in C.validar(abstrata, idx)


def test_prompt_carrega_o_enquadramento_de_janela_e_os_anti_padroes():
    """As invariantes do refinamento vivem no prompt, e o prompt é documentado
    por extenso (política do projeto). Este teste trava que elas não sumam
    numa edição futura."""
    p = C.PROMPT_CONDICOES
    assert "você é o tipo de pessoa que" in p        # anti-padrão de perfil
    assert "em vez de" in p                          # anti-padrão de oposição
    assert "MAIOR abstração" in p                    # controle de especificidade
    assert "SALTAR O TEMA" in p                      # precedência
    assert "CONDIÇÃO PUBLICADA" in p                 # unidade do anti-spoiler


# ===========================================================================
# [v1.9.37] `peso_meio` — o terceiro elemento de peso, escrito em CÓDIGO
# ===========================================================================

def test_peso_meio_aparece_quando_as_colunas_nao_somam_o_filme(nap):
    """`napoleon-2023` é o pior caso: as colunas mostram ~33% e ~22% e 45%
    das notas ficam invisíveis. Os dois números são verdadeiros e o conjunto
    sugere que somam o filme inteiro — a infidelidade por omissão da v1.4.0
    numa terceira forma."""
    pm = C.peso_do_meio(nap)
    assert pm is not None
    assert pm["pct"] == 45
    assert pm["texto"] == "~45% das notas ficaram no meio-termo"


def test_peso_meio_nao_aparece_quando_as_colunas_ja_somam_o_filme(godfather):
    """`the-godfather` é 2/5/93: uma terceira linha dizendo "~5% ficaram no
    meio" acrescenta ruído sem informar."""
    assert C.peso_do_meio(godfather) is None


def test_peso_meio_usa_a_regua_do_DEFEITO_e_nao_uma_proxy():
    """O critério é "as duas colunas somam menos de 80%", que é como o defeito
    foi medido — não `share_meio >= 20`, que é quase a mesma coisa e pega
    `pearl-2022`, cujas colunas somam 81% e que o defeito não inclui.

    [piloto de expansão, 2026-09] **`com_linha == alvos` virou
    `alvos <= com_linha`.** `alvos` são os 8 filmes que motivaram a régua —
    a prova de que ela NÃO é a proxy continua sendo `pearl-2022` ficar de
    fora (linha acima), e essa prova não muda com o catálogo. A igualdade
    exigia também que NENHUM outro filme jamais satisfizesse o critério —
    mas um catálogo maior tem mais chance de ter outro filme cujas colunas
    também somem menos de 80%, e isso não é regressão nenhuma da régua, é
    aritmética: mais filmes, mais candidatos. Manter só o subconjunto prova
    exatamente o que o nome do teste promete (a régua certa, não a proxy)
    sem fingir que a lista de 8 é definitiva."""
    pearl = _idx("pearl-2022")
    assert C.peso_do_meio(pearl) is None
    alvos = {"napoleon-2023", "friday-the-13th-2009", "wonka",
             "joker-folie-a-deux", "longlegs",
             "talk-to-me-2022", "barbie", "mother-2017"}
    com_linha = set()
    for caminho in sorted(RESULTADO.glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        idx = C.indexar(d)
        if idx and C.peso_do_meio(idx):
            com_linha.add(d["slug"])
    assert alvos <= com_linha, f"algum dos 8 conhecidos sumiu: {alvos - com_linha}"


def test_peso_meio_viaja_no_bloco_publicado():
    d = json.loads((RESULTADO / "napoleon-2023.json").read_text(
        encoding="utf-8"))
    limpo = json.dumps({"vale_a_pena": [], "talvez_evite": []})
    out = C.gerar(d, n=1, gerar=_fake([limpo]))
    assert out["peso_meio"]["pct"] == 45


def test_peso_meio_nunca_passa_pelo_modelo():
    """Mesmo estatuto de `peso_texto` e `nota_de_amostra`: é do código, e o
    briefing continua sem algarismo."""
    d = json.loads((RESULTADO / "napoleon-2023.json").read_text(
        encoding="utf-8"))
    texto = C.serializar_briefing(C.montar_briefing(d))
    assert "45" not in texto
    assert not any(ch.isdigit() for ch in texto)


# ===========================================================================
# [v1.9.37] As quatro decisões do dono, travadas no prompt
# ===========================================================================

def test_a_estrutura_do_final_e_permitida_e_o_conteudo_nao():
    """Decisão 1. A rodada 4 marcou 4 condições do tipo "não oferece resolução
    definitiva" como spoiler; elas passam a ser legítimas, porque a ESTRUTURA
    do final não revela nada da trama."""
    p = C.PROMPT_CONDICOES
    assert "ESTRUTURA DO FINAL É PERMITIDA" in p
    assert "não oferecem uma resolução" in p          # o exemplo PERMITIDO


def test_reviravolta_pode_ser_nomeada_mas_nao_o_efeito():
    """Decisão 2. `plot_twist` já é exceção deliberada noutra frente do
    projeto: nomear é permitido. O que estraga o filme é descrever o EFEITO —
    é ele que manda o leitor assistir procurando."""
    p = C.PROMPT_CONDICOES
    assert "NOMEAR é permitido, descrever o EFEITO não" in p
    assert "mudança memorável de perspectiva na trama" in p   # exemplo PROIBIDO
    assert "QUE TIPO DE EXPERIÊNCIA" in p                     # teste operacional


def test_o_exemplo_contraditorio_da_rodada_4_foi_removido():
    """**A contradição que a Decisão 2 expôs.** A regra 9b da rodada 4 dava
    como PREFERÍVEL exatamente o que a Decisão 2 proíbe — "busca histórias que
    recontextualizam o que veio antes". O modelo seguiu o exemplo que o prompt
    lhe deu, e é parte da explicação de `shutter-island` ter persistido."""
    assert "recontextualizam o que veio antes" not in C.PROMPT_CONDICOES


def test_expectativa_e_reputacao_sao_assunto_legitimo():
    """Decisão 3. A rodada 4 engoliu a categoria em 6 filmes por efeito
    colateral do enquadramento anti-perfil. `expectativa` é eixo da taxonomia
    justamente porque as pessoas falam disso."""
    p = C.PROMPT_CONDICOES
    assert "EXPECTATIVA E REPUTAÇÃO SÃO ASSUNTO LEGÍTIMO" in p
    assert "grande reputação não correspondem a altas expectativas" in p


# ===========================================================================
# [piloto de expansão] TRAVA × TEXTO DE AUTORIA HUMANA — opção (a)
# ===========================================================================

HUMANO = C.ORIGEM_HUMANA

# As sete correções do dono ao lote `0ec05ad3e326` que a trava reprovava —
# texto EXATO de `correcoes-piloto-18.json`, recortado só da abertura. São
# aprovadas por definição; `lexicas` é o que cada uma dispara, MEDIDO.
SETE_DO_DONO = [
    ("C010", "drive-my-car", "POS-B",
     "se interessa por vínculos entre personagens marcados por perdas, culpa "
     "e solidão", ["ancora_nao_verificavel", "sem_discriminacao"]),
    ("C020", "force-majeure-2014", "POS-F",
     "aceita lentidão e escolhas narrativas controversas quando coerentes "
     "com a proposta", ["ancora_nao_verificavel", "sem_discriminacao"]),
    # só `exemplo_verbatim`, pelos nomes — a exceção (c) o resolve na régua
    ("C026", "get-out-2017", "POS-B",
     "valoriza a intensidade e a credibilidade de Daniel Kaluuya e Allison "
     "Williams", []),
    ("C058", "memories-of-murder", "POS-A",
     "aprecia interpretações fortes de figuras complexas e de conduta "
     "ambivalente", ["ancora_nao_verificavel"]),
    ("C103", "the-second-mother", "POS-A",
     "se interessa pelas divisões de classe presentes nas relações dentro de "
     "casa", ["ancora_nao_verificavel", "sem_discriminacao"]),
    ("C127", "whiplash-2014", "POS-A",
     "valoriza a força e a naturalidade de J.K. Simmons e Miles Teller",
     ["sem_discriminacao"]),
    # cópia REAL de quatro palavras da paráfrase, sem nome nenhum
    ("C138", "zama", "POS-E",
     "valoriza aspectos técnicos e temáticos apesar de possível "
     "distanciamento e desorientação", ["exemplo_verbatim"]),
]


@pytest.mark.parametrize("numero,slug,tid,texto,lexicas", SETE_DO_DONO,
                         ids=[s[0] for s in SETE_DO_DONO])
def test_texto_humano_passa_pelos_exatos_e_recebe_aviso_nos_lexicos(
        numero, slug, tid, texto, lexicas):
    idx = _idx(slug)
    humano = {**_cond("vale_a_pena", texto, tid), "origem": HUMANO}
    assert C.validar_com_avisos(humano, idx) == ([], lexicas)
    assert C.validar(humano, idx) == []


@pytest.mark.parametrize("numero,slug,tid,texto,lexicas", SETE_DO_DONO,
                         ids=[s[0] for s in SETE_DO_DONO])
def test_o_mesmo_texto_como_saida_do_modelo_fica_sob_a_trava_completa(
        numero, slug, tid, texto, lexicas):
    """A metade obrigatória do par: SEM a marca de autoria, cada flag léxica
    continua travando e nada vira aviso."""
    idx = _idx(slug)
    assert C.validar_com_avisos(_cond("vale_a_pena", texto, tid), idx) == (
        lexicas, [])


def test_flags_lexicas_sao_exatamente_1c_1d_e_a_discriminacao():
    """A partição aprovada pelo dono. Qualquer flag a mais aqui é afrouxar a
    trava do texto humano por inferência."""
    assert C.FLAGS_LEXICAS == {"ancora_nao_verificavel", "tema_verbatim",
                               "exemplo_verbatim", "sem_discriminacao"}


@pytest.mark.parametrize("lado,texto,tema,flag", [
    ("vale_a_pena", "aprecia interpretações fortes de 2 figuras complexas",
     "POS-A", "digito"),
    ("vale_a_pena", 'aprecia "interpretações fortes" de figuras complexas',
     "POS-A", "aspas"),
    ("vale_a_pena", "aprecia interpretações fortes de figuras complexas e de "
     "conduta ambivalente num filme longo e muito escuro", "POS-A",
     "comprimento"),
    ("vale_a_pena", "aprecia, como a maioria, interpretações fortes de "
     "figuras complexas", "POS-A", "quantidade_escrita"),
    ("vale_a_pena", "aprecia interpretações fortes que o público elogia em "
     "figuras complexas", "POS-A", "escopo_generalizado"),
    ("vale_a_pena", "se você é do tipo que aprecia interpretações fortes de "
     "figuras complexas", "POS-A", "perfil_de_leitor"),
    ("vale_a_pena", "aprecia interpretações fortes de figuras complexas",
     "POS-Z", "ancora_inexistente"),
    ("talvez_evite", "aprecia interpretações fortes de figuras complexas",
     "POS-A", "ancora_de_outro_bucket"),
    ("vale_a_pena", '{"texto": "aprecia interpretações fortes de figuras '
     'complexas"}', "POS-A", "formato_invalido"),
])
def test_texto_humano_continua_travado_pelos_validadores_exatos(
        lado, texto, tema, flag):
    humano = {**_cond(lado, texto, tema), "origem": HUMANO}
    trava, _ = C.validar_com_avisos(humano, _idx("memories-of-murder"))
    assert flag in trava
    assert flag not in C.FLAGS_LEXICAS


def test_a_saida_do_modelo_nao_tem_como_se_declarar_humana():
    """A trava do texto do modelo é ESTRUTURAL: `extrair` monta a condição
    campo a campo, e uma `origem` escrita pelo modelo não chega adiante."""
    texto = SETE_DO_DONO[3][3]
    bruto = json.dumps({"vale_a_pena": [
        {"texto": texto, "tema_origem": "POS-A", "origem": HUMANO}],
        "talvez_evite": []})
    c = C.extrair(bruto)["vale_a_pena"][0]
    assert "origem" not in c
    assert C.validar(c, _idx("memories-of-murder")) == ["ancora_nao_verificavel"]

    d = json.loads((RESULTADO / "memories-of-murder.json").read_text(
        encoding="utf-8"))
    out = C.gerar(d, n=1, gerar=_fake([bruto, bruto]))
    assert out["vale_a_pena"] == []
    assert out["descartadas"][0]["flags"] == ["ancora_nao_verificavel"]


# ===========================================================================
# [piloto de expansão] A exceção de NOME PRÓPRIO nos dois verbatim — opção (c)
# ===========================================================================

def test_excecao_de_nome_proprio_vale_nos_dois_verbatim(godfather):
    """`tema_verbatim` tem a exceção desde a v1.9.35; `exemplo_verbatim`
    passa a ter. C026, como texto do MODELO (sem marca de autoria): a
    sequência copiada é "Daniel Kaluuya e Allison Williams" — só nomes."""
    alvo = next(t for t in godfather.values()
                if t["tema"] == "Transformação de Michael Corleone")
    assert "tema_verbatim" not in C.validar(
        _cond("vale_a_pena", "quer ver a transformação de Michael Corleone",
              alvo["id"]), godfather)
    c026 = SETE_DO_DONO[2][3]
    assert C.validar(_cond("vale_a_pena", c026, "POS-B"),
                     _idx("get-out-2017")) == []


def test_excecao_de_nome_proprio_nao_libera_copia_de_frase(nap):
    """A exceção é para a sequência feita SÓ de nomes. Nome colado à frase de
    outra pessoa continua cópia ("…a vida pessoal de Napoleão", o par da
    rodada 1, que "tirar os nomes e recontar" teria liberado); e cópia sem
    nome nenhum (C138) continua cópia."""
    alvo = next(t for t in nap.values()
                if t["tema"] == "Abordagem pessoal e íntima do personagem")
    assert "napoleao" in C.nomes_proprios(alvo["exemplo"])
    assert "exemplo_verbatim" in C.validar(
        _cond("vale_a_pena",
              "prefere ver as inseguranças e a vida pessoal de Napoleão",
              alvo["id"]), nap)
    assert C.validar(_cond("vale_a_pena", SETE_DO_DONO[6][3], "POS-E"),
                     _idx("zama")) == ["exemplo_verbatim"]


# ===========================================================================
# [piloto de expansão] SEM CONDIÇÃO PUBLICÁVEL — a recusa declarada
# ===========================================================================

def test_validar_recusa_conjunto_fechado_tema_pedido_e_motivo_curto():
    lado_de = {"POS-A": "vale_a_pena"}
    ok = {"tema_origem": "POS-A", "regra": "R6",
          "motivo": "o tema usa só o desfecho"}
    assert C.validar_recusa(ok, lado_de) == []
    assert C.validar_recusa({**ok, "regra": "R6/R12"}, lado_de) == []
    assert C.validar_recusa({**ok, "regra": "R9"}, lado_de) == [
        "recusa_regra_invalida"]
    assert C.validar_recusa({**ok, "regra": "R6/R9"}, lado_de) == [
        "recusa_regra_invalida"]
    assert C.validar_recusa({**ok, "regra": ""}, lado_de) == [
        "recusa_regra_invalida"]
    assert C.validar_recusa({**ok, "tema_origem": "POS-B"}, lado_de) == [
        "recusa_tema_nao_pedido"]
    assert C.validar_recusa({**ok, "lado": "talvez_evite"}, lado_de) == [
        "recusa_de_outro_lado"]
    assert C.validar_recusa({**ok, "motivo": ""}, lado_de) == [
        "recusa_sem_motivo"]
    assert C.validar_recusa({**ok, "motivo": " ".join(["x"] * 20)},
                            lado_de) == []
    assert C.validar_recusa({**ok, "motivo": " ".join(["x"] * 21)},
                            lado_de) == ["recusa_motivo_longo"]
    assert C.validar_recusa({**ok, "origem": "outra"}, lado_de) == [
        "recusa_origem_invalida"]


def test_as_tres_recusas_do_dono_sao_validas():
    """C024, C051, C089 — texto do dono, verbatim."""
    for regra, motivo in [
            ("R6", "o tema usa exclusivamente características do desfecho "
                   "como critério de decisão"),
            ("R2", "o tema relata dificuldade e incompreensão, mas não "
                   "sustenta aprovação desse desafio"),
            ("R6/R12", "retirar o desfecho transformaria um detalhe final em "
                       "característica da experiência inteira")]:
        assert C.validar_recusa(
            {"tema_origem": "X", "regra": regra, "motivo": motivo,
             "origem": HUMANO}, {"X": "vale_a_pena"}) == []


def test_extrair_le_e_normaliza_sem_condicao():
    bruto = json.dumps({"vale_a_pena": [], "talvez_evite": [],
                        "sem_condicao": [{"tema_origem": " pos-c ",
                                          "regra": "r6 / r12",
                                          "motivo": " sem lastro ",
                                          "origem": HUMANO}]})
    assert C.extrair(bruto)["sem_condicao"] == [
        {"tema_origem": "POS-C", "regra": "R6/R12", "motivo": "sem lastro"}]


LIMPAS_NAP = {
    "Abordagem pessoal e íntima do personagem":
        "quer um Napoleão íntimo, não o estadista",
    "Impacto visual e direção de arte":
        "valoriza fotografia, figurinos e cenários deslumbrantes",
}


def _nap_briefing():
    d = json.loads((RESULTADO / "napoleon-2023.json").read_text(
        encoding="utf-8"))
    b = C.montar_briefing(d)
    limpas = [(t["id"], LIMPAS_NAP[t["tema"]]) for t in b["selecao"]["vale_a_pena"]
              if t["tema"] in LIMPAS_NAP]
    assert len(limpas) == 2, "os dois temas de texto limpo têm de estar pedidos"
    return d, b, limpas


def _resp(conds=(), recusas=()):
    return json.dumps({"vale_a_pena": [{"texto": t, "tema_origem": i}
                                       for i, t in conds],
                       "talvez_evite": [],
                       "sem_condicao": [{"tema_origem": i, "regra": r,
                                         "motivo": "a paráfrase não sustenta "
                                                   "frase honesta"}
                                        for i, r in recusas]})


def test_recusa_declarada_conta_como_resolvida_e_o_silencio_nao():
    """O defeito que o canal fecha: a amostra que RECUSA um tema perdia
    para a que o escrevia. Agora recusa válida conta; silêncio, não."""
    _, b, [(a, ta), (x, _)] = _nap_briefing()
    silencio = C.extrair(_resp([(a, ta)]))
    declara = C.extrair(_resp([(a, ta)], [(x, "R1")]))
    assert C.selecionar_candidato([silencio, declara], b)["indice"] == 1
    # recusa com regra fora do conjunto não conta — e custa flag
    invalida = C.extrair(_resp([(a, ta)], [(x, "R9")]))
    assert C.selecionar_candidato([invalida, silencio], b)["indice"] == 1


def test_desempate_vence_quem_escreveu_mais():
    """Cobertura e flags iguais: vence quem ESCREVEU. Sem isto, recusar é o
    caminho de menor atrito — recusa válida não tem flag."""
    _, b, [(a, ta), (x, tx)] = _nap_briefing()
    declara = C.extrair(_resp([(a, ta)], [(x, "R1")]))
    escreve = C.extrair(_resp([(a, ta), (x, tx)]))
    esc = C.selecionar_candidato([declara, escreve], b)
    assert esc["indice"] == 1
    assert [c["n_temas_resolvidos"] for c in esc["candidatos"]] == [2, 2]
    assert [c["n_flags"] for c in esc["candidatos"]] == [0, 0]


def test_tema_nas_duas_listas_vira_tema_repetido_nas_duas_pontas():
    _, b, [(a, ta), _] = _nap_briefing()
    m = C._medir(C.extrair(_resp([(a, ta)], [(a, "R1")])), b)
    assert "tema_repetido" in m["condicoes"][0]["flags"]
    assert "tema_repetido" in m["recusas"][0]["flags"]
    assert m["n_temas_recusados"] == 0


def test_gerar_publica_a_recusa_e_NAO_puxa_o_proximo_tema():
    d, b, [(a, ta), (x, _)] = _nap_briefing()
    out = C.gerar(d, n=1, gerar=_fake([_resp([(a, ta)], [(x, "R6")])]))
    assert out["sem_condicao_publicavel"] == [{
        "tema_origem": x, "lado": "vale_a_pena", "regra": "R6",
        "motivo": "a paráfrase não sustenta frase honesta",
        "origem": "modelo"}]
    assert x not in out["temas_saltados"]["vale_a_pena"]
    assert x not in {c["tema_origem"] for c in out["vale_a_pena"]}
    # a seleção é a do código, antes e depois da recusa
    assert out["temas_pedidos"] == {l: [t["id"] for t in b["selecao"][l]]
                                    for l in C.LADOS}
    publicados = {c["tema_origem"] for l in C.LADOS for c in out[l]}
    assert publicados <= set(sum(out["temas_pedidos"].values(), []))


def test_recusa_no_retry_vale_e_a_frase_reprovada_fica_registrada():
    d, _, [(a, _), _] = _nap_briefing()
    ruim = _resp([(a, "gosta de 3 batalhas")])
    retry = _resp([], [(a, "R1")])
    out = C.gerar(d, n=1, gerar=_fake([ruim, retry]))
    assert [c["tema_origem"] for c in out["descartadas"]] == [a]
    assert [r["tema_origem"] for r in out["sem_condicao_publicavel"]] == [a]
    assert out["retry"]["n_recusadas_pelo_modelo"] == 1


def test_recusa_invalida_fica_registrada_e_nao_publica():
    d, _, [(a, ta), (x, _)] = _nap_briefing()
    out = C.gerar(d, n=1, gerar=_fake([_resp([(a, ta)], [(x, "R9")])]))
    assert out["sem_condicao_publicavel"] == []
    assert [(r["tema_origem"], r["flags"]) for r in out["recusas_invalidas"]
            ] == [(x, ["recusa_regra_invalida"])]
    assert x in out["temas_saltados"]["vale_a_pena"]      # silêncio


def test_prompt_carrega_o_canal_de_recusa_com_o_conjunto_fechado():
    import re
    p = C.PROMPT_CONDICOES
    assert '"sem_condicao"' in p
    assert set(re.findall(r"\bR\d+\b", p)) == set(C.REGRAS_DE_RECUSA)
    assert "declarar não é saída fácil" in p
    assert "NÃO põe outro tema no lugar" in p


# ===========================================================================
# [piloto de expansão] O PAR diante da recusa
# ===========================================================================

def test_pares_obrigatorios_sao_a_mesma_computacao_da_selecao():
    for caminho in sorted(RESULTADO.glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        idx = C.indexar(d)
        if not idx:
            continue
        base = C.selecionar(idx, par_obrigatorio=False)
        sel = C.selecionar(idx)
        pares = C.pares_obrigatorios(idx)
        for lado in C.LADOS:
            forcados = {p["forcado"] for p in pares if p["lado_forcado"] == lado}
            assert forcados == ({t["id"] for t in sel[lado]}
                                - {t["id"] for t in base[lado]}), (d["slug"], lado)


def _par_das_batalhas(nap):
    return next(p for p in C.pares_obrigatorios(nap)
                if nap[p["forcado"]]["tema"] == "Batalhas decepcionantes")


def _bloco_do_par(p, recusado):
    lado_rec = p["lado_base"] if recusado == p["base"] else p["lado_forcado"]
    b = {p["lado_base"]: [{"texto": "base", "tema_origem": p["base"]}],
         p["lado_forcado"]: [{"texto": "forçado", "tema_origem": p["forcado"]}],
         "temas_pedidos": {p["lado_base"]: [p["base"]],
                           p["lado_forcado"]: [p["forcado"]]},
         "temas_saltados": {l: [] for l in C.LADOS},
         "sem_condicao_publicavel": [{"tema_origem": recusado,
                                      "lado": lado_rec, "regra": "R1",
                                      "motivo": "m", "origem": "modelo"}]}
    b[lado_rec] = []
    return b


def test_forcado_recusado_o_base_publica_com_a_marca_par_recusado(nap):
    """O caso `napoleon`: se a objeção das HATERS às batalhas é recusada, as
    batalhas bonitas continuam na página — marcadas, para a revisão julgar
    se sozinhas achatam a recepção. Tirá-las puniria o tema mais citado."""
    p = _par_das_batalhas(nap)
    b = C.consolidar_recusas(_bloco_do_par(p, p["forcado"]), nap)
    assert b[p["lado_base"]] == [{"texto": "base", "tema_origem": p["base"],
                                  "par_recusado": p["forcado"]}]
    assert b["temas_saltados"] == {l: [] for l in C.LADOS}
    assert C.inconsistencias_de_recusa(b, nap) == []


def test_base_recusado_desfaz_o_par_e_o_forcado_sai(nap):
    p = _par_das_batalhas(nap)
    b = C.consolidar_recusas(_bloco_do_par(p, p["base"]), nap)
    assert b[p["lado_forcado"]] == []
    assert b["par_desfeito"] == [{"texto": "forçado", "tema_origem": p["forcado"],
                                  "lado": p["lado_forcado"],
                                  "tema_base": p["base"]}]
    assert b["temas_saltados"] == {l: [] for l in C.LADOS}
    assert C.consolidar_recusas(b, nap) == b                 # idempotente


def test_par_nao_consolidado_e_inconsistencia(nap):
    p = _par_das_batalhas(nap)
    cru = _bloco_do_par(p, p["base"])           # o forçado ainda na coluna
    assert any("par não consolidado" in x
               for x in C.inconsistencias_de_recusa(cru, nap))
