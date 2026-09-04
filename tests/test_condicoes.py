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
    obs = _idx("obsession-2026")
    for lado in C.LADOS:
        assert C.peso_do_lado(obs, lado)["peso_pct"] is not None
    assert all(t["rotulo_forca"] is None for t in obs.values())


def test_rotulo_forca_suprimido_nos_estados_de_piso():
    obs = _idx("obsession-2026")
    assert all(t["rotulo_forca"] is None for t in obs.values())
    normal = _idx("interstellar")
    assert all(t["rotulo_forca"] is not None for t in normal.values())


# ===========================================================================
# BRIEFING — as garantias por construção
# ===========================================================================

def test_briefing_nao_tem_algarismo_em_nenhum_dos_35():
    """A garantia "zero dígitos" do §3[V] é mais fraca aqui do que lá — o
    briefing precisa carregar a paráfrase (P4 REVISADO) e a paráfrase não é
    limpa. MEDIDO: 1 tema do catálogo tem algarismo, e ele está fora do
    top-3. Este teste é onde um filme novo que reabra o buraco aparece."""
    for caminho in sorted(RESULTADO.glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        b = C.montar_briefing(d)
        if b is None:
            continue
        texto = C.serializar_briefing(b)
        assert not any(ch.isdigit() for ch in texto), d["slug"]


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
    assert C.extrair("não é json") == {"vale_a_pena": [], "talvez_evite": []}
    assert C.extrair("") == {"vale_a_pena": [], "talvez_evite": []}


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
    `pearl-2022`, cujas colunas somam 81% e que o defeito não inclui."""
    pearl = _idx("pearl-2022")
    assert C.peso_do_meio(pearl) is None
    alvos = {"napoleon-2023", "friday-the-13th-2009", "wonka",
             "joker-folie-a-deux", "longlegs", "obsession-2026",
             "talk-to-me-2022", "barbie", "mother-2017"}
    com_linha = set()
    for caminho in sorted(RESULTADO.glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        idx = C.indexar(d)
        if idx and C.peso_do_meio(idx):
            com_linha.add(d["slug"])
    assert com_linha == alvos


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
