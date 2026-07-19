"""[D] Síntese temática por bucket via LLM (SPEC §D).

Prompt fixo reproduz §D LITERALMENTE e é BYTE-IDÊNTICO entre providers — só o
transporte (client_call) muda. v1.1.2: o prompt passou a ser PARAMETRIZADO
POR BUCKET (preâmbulo de papel com nome + intervalo de notas), não mais uma
string única — a parametrização é por bucket, nunca por modelo/provider.

Contrato formal do cliente injetável (v1.1.1):
    client_call(system: str, user: str, model: str) -> str
Qualquer implementação (Anthropic, Gemini, mock de teste) deve respeitar essa
assinatura. `synthesize_bucket` faz parsing defensivo (strip de fences,
try/except) com 1 retentativa sobre o texto devolvido, independente do
provider.

v1.1.2 — motivação das validações pós-parsing (ver `resultado/comparacao/
COMPARACAO.md`): rodando o MESMO prompt sobre o MESMO corpus, o flash-lite (a)
gerou uma `observacao_geral` do bucket NEGATIVAS dizendo "a maioria dos
críticos considera o filme um fracasso" — generalizando um recorte filtrado
por construção (só as notas baixas) para a opinião geral do filme; e o
2.5-flash (b) usou frases entre aspas em `exemplo_parafraseado`, violando a
regra de paráfrase (citação literal, ainda que traduzida). O preâmbulo de
papel ataca (a) na raiz (o modelo agora sabe que só vê um recorte enviesado);
as validações pós-parsing abaixo são rede de segurança/telemetria para os dois
problemas, não a defesa principal.
"""
from __future__ import annotations

import json
import os
import re

from .config import (
    BUCKETS,
    LLM_MAX_TOKENS,
    MAX_TEMAS,
    MODEL_DEFAULT,
    PROVIDER_DEFAULT_MODELS,
    PROVIDER_ENV_KEYS,
    nota_para_url,
)
from .models import BucketResult, Tema


def _intervalo_bucket(bucket_nome: str) -> str:
    """Ex.: 'negativas' -> '0.5–2.5 estrelas'."""
    niveis = BUCKETS[bucket_nome]
    lo, hi = min(niveis), max(niveis)
    return f"{nota_para_url(lo)}–{nota_para_url(hi)} estrelas"


def build_system_prompt(bucket_nome: str) -> str:
    """Monta o prompt fixo (SPEC §D). Parametrizado por BUCKET (preâmbulo de
    papel: nome + intervalo de notas) — NÃO por provider/modelo, que
    continuam recebendo texto byte-idêntico para o mesmo bucket.

    v1.1.2: preâmbulo novo antes das instruções invariantes, atacando na raiz
    o erro de enquadramento observado na comparação de modelos (ver docstring
    do módulo) — o modelo precisa saber que só está vendo um recorte
    enviesado por construção, não a recepção geral do filme.
    """
    intervalo = _intervalo_bucket(bucket_nome)
    return f"""\
Você é uma etapa de um pipeline que agrega reviews de usuários de um filme \
do Letterboxd. O pipeline separa as reviews em três faixas de nota ANTES \
desta etapa (negativas, medianas, positivas); você está recebendo \
EXCLUSIVAMENTE a faixa "{bucket_nome}" ({intervalo}) — um recorte enviesado \
POR CONSTRUÇÃO, que NÃO representa a recepção geral do filme.

Sua função é descrever o que ESTE grupo específico de reviews diz. Outros \
módulos do pipeline cuidam das outras faixas de nota; o usuário final verá \
as três análises lado a lado, cada uma rotulada com sua faixa.

Consequência explícita: é PROIBIDO generalizar para "os críticos", "a \
maioria", "o consenso" ou "a recepção do filme". A `observacao_geral` deve \
se referir sempre a ESTE grupo (ex.: "as reviews {bucket_nome} apontam...", \
"este grupo destaca..."), nunca ao filme em termos absolutos.

Instruções fixas (invariáveis):
1. Anti-spoiler: descreva as críticas em nível temático (ritmo, atuações, \
fotografia, roteiro em termos abstratos). É PROIBIDO mencionar eventos da \
trama, destinos de personagens, reviravoltas ou o final, mesmo que as reviews \
os mencionem.
2. `exemplo_parafraseado` é paráfrase, NUNCA citação literal de nenhuma review.
3. Temas ordenados por `mencoes_aproximadas` decrescente; no máximo {MAX_TEMAS} \
temas por bucket; não invente temas de menção única, salvo se o bucket tiver \
menos de 5 reviews.
4. As reviews podem estar em qualquer idioma; sua saída é SEMPRE em pt-BR.
5. Responda APENAS o JSON, sem preâmbulo, sem cercas de código.
6. É PROIBIDO usar aspas (simples, duplas ou angulares) dentro de \
`exemplo_parafraseado` — nunca cite nem reproduza um trecho entre aspas, \
mesmo traduzido; reescreva sempre em terceira pessoa, com suas próprias \
palavras.
7. Reforço de idioma: TODOS os campos de texto da saída devem estar em \
pt-BR, incluindo os NOMES DOS TEMAS — nunca deixe um tema em inglês ou \
outro idioma, mesmo que a review de origem esteja nesse idioma.

Formato de saída (JSON puro):
{{
  "bucket": "<nome>",
  "temas": [
    {{
      "tema": "<curto>",
      "mencoes_aproximadas": <int>,
      "n_reviews_analisadas": <int>,
      "exemplo_parafraseado": "<paráfrase>"
    }}
  ],
  "observacao_geral": "<1-2 frases>"
}}"""


# Reforço anexado ao prompt SOMENTE na retentativa de validação (idioma
# e/ou escopo) — v1.1.2 §D.
_REFORCO_VALIDACAO = """

REFORÇO CRÍTICO — sua resposta anterior violou uma regra fixa; corrija AGORA:
- Se usou qualquer palavra/frase fora de pt-BR (inclusive nos nomes dos \
temas): reescreva TUDO em português do Brasil.
- Se a `observacao_geral` generalizou para "os críticos", "a maioria", "o \
consenso" ou "a recepção do filme": reescreva se referindo apenas a ESTE \
grupo de reviews (a faixa de nota analisada), nunca ao filme como um todo."""


# Reforço adicional SÓ para o narrador [D2] (v1.2.1): tamanhos de grupo vêm da
# cota de coleta, não da recepção real — anexado à retentativa combinada.
_REFORCO_PREVALENCIA = """
- Se comparou o TAMANHO dos grupos ou inferiu prevalência no público (maioria/\
minoria/grupo maior ou menor/igualmente expressivo/polarizada/dividida/\
consenso): reescreva tratando os grupos como PERSPECTIVAS, sem comparar \
tamanhos — os tamanhos vêm da cota de amostragem por faixa de nota, não da \
opinião real do público."""


# Reforço adicional SÓ para o narrador [D2] (v1.2.3) — rede de segurança do
# quantificador pré-computado: anexado à retentativa combinada.
_REFORCO_QUANTIFICADOR = """
- Se usou "quase todos" ou "praticamente todos" para algum tema sem que o \
rótulo_quantificador fornecido para aquele tema fosse exatamente esse: \
troque pelo rótulo_quantificador correto que veio no relatório — nunca \
invente um quantificador mais forte do que o fornecido."""


class LLMError(RuntimeError):
    pass


class ProviderError(RuntimeError):
    """Erro na seleção/resolução de provider (chave ausente/ambígua, nome inválido)."""


# --- Adaptadores de provider (contrato: (system, user, model) -> str) ---

def anthropic_client_call(system: str, user: str, model: str) -> str:
    import anthropic

    key = os.environ.get(PROVIDER_ENV_KEYS["anthropic"])
    if not key:
        raise LLMError(f"{PROVIDER_ENV_KEYS['anthropic']} não definida no ambiente.")
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model,
        max_tokens=LLM_MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def gemini_supports_thinking(model: str) -> bool:
    """Família gemini-2.5+ suporta `ThinkingConfig`; gemini-2.0 e anteriores
    não têm o mecanismo de thinking e podem rejeitar o parâmetro.

    Heurística: extrai a versão major.minor do nome do modelo
    (`gemini-2.5-flash` -> (2,5), `gemini-2.0-flash` -> (2,0)) e compara com
    (2,5). Nome sem versão reconhecível (formato inesperado/futuro) ->
    conservador, assume que NÃO suporta (não arrisca passar um parâmetro que
    pode ser rejeitado por um modelo desconhecido).
    """
    m = re.match(r"gemini-(\d+)\.(\d+)", model)
    if not m:
        return False
    major, minor = int(m.group(1)), int(m.group(2))
    return (major, minor) >= (2, 5)


def gemini_client_call(system: str, user: str, model: str) -> str:
    """Adaptador Gemini via google-genai, usando modo JSON nativo.

    O parsing defensivo (fences/try-except) e a retentativa continuam vivendo
    em `synthesize_bucket` — response_mime_type="application/json" reduz a
    chance de precisar deles, mas não os torna dispensáveis (o modelo ainda
    pode devolver um JSON sintaticamente inválido ou fora do schema).

    thinking_budget=0 — CONDICIONAL ao modelo (v1.1.1, comparação de
    modelos): modelos gemini-2.5-* gastam tokens de "thinking" do MESMO
    orçamento de max_output_tokens, ANTES de gerar a resposta visível.
    Medido ao vivo: no bucket real "negativas" (50 reviews, maior do
    sistema), thinking sozinho consumiu 7679/8000 tokens, cortando o JSON no
    meio (finish_reason=MAX_TOKENS) mesmo com um teto generoso — o consumo
    escala com o tamanho do prompt e não é previsível de antemão. Para uma
    tarefa de extração estruturada como esta (não raciocínio livre), desligar
    thinking resolve a causa raiz em vez de perseguir um teto de tokens
    maior. MAS `ThinkingConfig` é específico da família 2.5+ — passá-lo para
    gemini-2.0-flash (sem mecanismo de thinking) pode ser rejeitado pela API;
    por isso o parâmetro só é incluído quando `gemini_supports_thinking(model)`.
    """
    from google import genai
    from google.genai import types

    key = os.environ.get(PROVIDER_ENV_KEYS["gemini"])
    if not key:
        raise LLMError(f"{PROVIDER_ENV_KEYS['gemini']} não definida no ambiente.")
    client = genai.Client(api_key=key)
    config_kwargs = dict(
        system_instruction=system,
        response_mime_type="application/json",
        max_output_tokens=LLM_MAX_TOKENS,
    )
    if gemini_supports_thinking(model):
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    resp = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(**config_kwargs),
    )
    return resp.text


PROVIDER_CLIENTS = {
    "anthropic": anthropic_client_call,
    "gemini": gemini_client_call,
}


def detect_provider(explicit: str | None = None) -> str:
    """Resolve qual provider usar (CLI §B2/Tarefa 2).

    Prioridade: `explicit` (--provider) > chave única presente no ambiente.
    Ambas as chaves presentes sem --provider, ou nenhuma chave presente,
    são erro — a spec exige decisão explícita nesses casos, não um default
    silencioso. Mesmo com `explicit`, a chave correspondente precisa estar
    presente — falha aqui em vez de só na hora da chamada real, para que o
    CLI possa recusar antes de gastar qualquer requisição de coleta.
    """
    if explicit is not None:
        if explicit not in PROVIDER_CLIENTS:
            raise ProviderError(
                f"provider {explicit!r} desconhecido — use um de "
                f"{sorted(PROVIDER_CLIENTS)}."
            )
        if not os.environ.get(PROVIDER_ENV_KEYS[explicit]):
            raise ProviderError(
                f"--provider {explicit} escolhido, mas "
                f"{PROVIDER_ENV_KEYS[explicit]} não está definida no ambiente."
            )
        return explicit

    presentes = [p for p, env in PROVIDER_ENV_KEYS.items() if os.environ.get(env)]
    if len(presentes) == 1:
        return presentes[0]
    if not presentes:
        chaves = " ou ".join(PROVIDER_ENV_KEYS.values())
        raise ProviderError(
            f"nenhuma chave de API encontrada ({chaves}) — defina uma delas "
            f"ou passe --provider explicitamente."
        )
    raise ProviderError(
        f"múltiplas chaves de API presentes ({', '.join(presentes)}) — "
        f"especifique --provider {{{','.join(sorted(PROVIDER_CLIENTS))}}}."
    )


def _resolve_call_and_model(client_call, model, provider):
    """Resolve (call, model) para uma etapa LLM — compartilhado por
    `synthesize_bucket` [D] e `narrate_output` [D2]. Client custom sem provider
    conhecido cai no default histórico (`MODEL_DEFAULT`); caso contrário o
    default de modelo segue o provider resolvido."""
    if client_call is not None:
        return client_call, (model or MODEL_DEFAULT)
    resolved_provider = detect_provider(provider)
    return PROVIDER_CLIENTS[resolved_provider], (model or PROVIDER_DEFAULT_MODELS[resolved_provider])


def build_user_message(bucket: BucketResult) -> str:
    reviews = bucket.reviews_analisadas
    linhas = [
        f"Bucket: {bucket.nome}",
        f"Total de reviews analisadas neste bucket: {len(reviews)}",
        "",
        "Reviews (nota em estrelas + texto completo):",
    ]
    for i, r in enumerate(reviews, 1):
        linhas.append(f"[{i}] nota={r.rating} estrelas:")
        linhas.append(r.effective_text)
        linhas.append("")
    return "\n".join(linhas)


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.endswith("```"):
            t = t[: -3]
        # remove possível "json" na primeira linha
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    return t.strip()


def _parse_llm_json(raw: str) -> dict:
    return json.loads(_strip_fences(raw))


# --- Validações pós-parsing (código, não prompt) — SPEC §D, v1.1.2 ---
# Rede de segurança/telemetria: o preâmbulo de papel (build_system_prompt) é
# a defesa principal contra vazamento de escopo; estas checagens são baratas
# e propositalmente imperfeitas (heurísticas), não substituem revisão humana.

_ASPAS_CHARS = "\"'“”‘’«»‹›"


def _remover_aspas(texto: str) -> tuple[str, bool]:
    """Remoção MECÂNICA (não reescrita) de aspas de citação. Retorna
    (texto_limpo, houve_remocao)."""
    if not any(c in texto for c in _ASPAS_CHARS):
        return texto, False
    limpo = texto
    for c in _ASPAS_CHARS:
        limpo = limpo.replace(c, "")
    limpo = re.sub(r"[ \t]{2,}", " ", limpo).strip()
    return limpo, True


# Heurística de stopwords — mesma família da usada em scripts/compare_models.py
# (checagem factual de idioma), agora promovida a validação de produção.
_STOPWORDS_PT = {
    "de", "da", "do", "das", "dos", "que", "para", "com", "uma", "um", "e",
    "os", "as", "não", "mais", "como", "por", "sobre", "são", "foi", "ao",
    "à", "às", "seu", "sua", "entre", "também", "muito", "há", "este",
    "esta", "esse", "essa", "mas", "ou", "já", "só", "sem", "pelo", "pela",
}
_STOPWORDS_EN = {
    "the", "and", "of", "to", "in", "is", "for", "with", "on", "are", "as",
    "this", "that", "by", "from", "or", "an", "its", "be", "was", "were",
    "but", "not", "at", "it", "his", "her", "their", "than", "into",
}


def _idioma_e_pt_br(texto: str) -> bool:
    """True se pt-BR OU indeterminado (sem stopwords de nenhum idioma) — a
    ausência de evidência não vira falso positivo de violação."""
    palavras = [w.strip(".,;:!?()\"'").lower() for w in texto.split()]
    n_pt = sum(1 for w in palavras if w in _STOPWORDS_PT)
    n_en = sum(1 for w in palavras if w in _STOPWORDS_EN)
    if n_pt == 0 and n_en == 0:
        return True
    return n_pt >= n_en


def _texto_para_checagem_idioma(temas: list[Tema], observacao_geral: str) -> str:
    partes = [t.tema for t in temas] + [t.exemplo_parafraseado for t in temas]
    partes.append(observacao_geral)
    return " ".join(partes)


# Marcadores de vazamento de escopo (generalização do bucket p/ o filme
# inteiro) — lista propositalmente pequena e literal, não é NLP.
_MARCADORES_ESCOPO = [
    "a maioria dos críticos", "o consenso", "os críticos consideram",
    "amplamente aclamado", "amplamente rejeitado",
]


def _tem_marcador_de_escopo(observacao_geral: str) -> bool:
    texto = observacao_geral.lower()
    return any(m in texto for m in _MARCADORES_ESCOPO)


# Marcadores de PREVALÊNCIA entre grupos (v1.2.1) — a prosa narrativa
# apresentando a cota de amostragem como distribuição da recepção (comparar
# tamanhos de grupo / inferir prevalência global). Heurística acento-sensível
# como as demais: rede de segurança/telemetria; a defesa principal é a
# invariante (c) do prompt §D2. Lista mínima, literal, não é NLP.
_MARCADORES_PREVALENCIA = [
    "maioria dos espectadores", "maioria do público", "minoria",
    "grupo maior", "grupo menor", "igualmente expressivo",
    "polarizada", "dividida", "consenso",
]


def _tem_marcador_de_prevalencia(texto: str) -> bool:
    t = texto.lower()
    return any(m in t for m in _MARCADORES_PREVALENCIA)


def _construir_temas(data: dict, n_analisadas: int) -> list[Tema]:
    """Constrói a lista de Tema a partir do JSON parseado: clamp do
    numerador (v1.1.1) + remoção mecânica de aspas (v1.1.2)."""
    temas = []
    for t in (data.get("temas") or [])[:MAX_TEMAS]:
        try:
            bruto = int(t.get("mencoes_aproximadas", 0))
        except (TypeError, ValueError):
            bruto = 0
        clampado = max(0, min(bruto, n_analisadas))
        foi_clampado = clampado != bruto

        exemplo_bruto = str(t.get("exemplo_parafraseado", ""))
        exemplo_limpo, aspas_removidas = _remover_aspas(exemplo_bruto)

        temas.append(Tema(
            tema=str(t.get("tema", "")),
            mencoes_aproximadas=clampado,
            n_reviews_analisadas=n_analisadas,
            exemplo_parafraseado=exemplo_limpo,
            mencoes_clampadas=foi_clampado,
            mencoes_valor_original=bruto if foi_clampado else None,
            aspas_removidas=aspas_removidas,
        ))
    temas.sort(key=lambda x: x.mencoes_aproximadas, reverse=True)  # §D.3
    return temas


def synthesize_bucket(bucket: BucketResult, client_call=None,
                      model: str | None = None,
                      provider: str | None = None) -> BucketResult:
    """Preenche `bucket.temas` e `bucket.observacao_geral`.

    Buckets sem análise (§C piso) NÃO chamam o LLM. Reviews enviadas usam
    SEMPRE texto completo (garantido por C'). Uma retentativa em JSON inválido.

    Provider (v1.1.1): se `client_call` for omitido, resolve o adaptador via
    `provider` (--provider) ou auto-detecção pela chave de API presente no
    ambiente (`detect_provider`) — ver GATE de ambiguidade lá. O modelo
    default também passa a depender do provider resolvido
    (`PROVIDER_DEFAULT_MODELS`), a menos que `model` seja passado explicitamente.

    Validações pós-parsing (v1.1.2, código não-prompt):
    - Aspas em `exemplo_parafraseado`: removidas mecanicamente, SEM
      retentativa (correção barata, não precisa de nova chamada). Flag
      `aspas_removidas` por tema.
    - Idioma e escopo: verificados juntos; se qualquer um falhar, UMA
      retentativa COMBINADA (mesma chamada cobre os dois — mantém o
      orçamento de chamadas previsível). Se persistir, aceita o resultado da
      retentativa e sinaliza `idioma_invalido`/`escopo_suspeito` no bucket
      (visível no render) em vez de insistir indefinidamente.
    """
    if bucket.modo == "sem_analise":
        bucket.observacao_geral = (
            f"Bucket sem análise temática: apenas {bucket.n_validas} review(s) "
            f"válida(s) (piso é 3)."
        )
        return bucket

    call, model = _resolve_call_and_model(client_call, model, provider)

    system = build_system_prompt(bucket.nome)
    user = build_user_message(bucket)
    n_analisadas = len(bucket.reviews_analisadas)

    data = None
    for tentativa in range(2):  # chamada + 1 retentativa de JSON inválido (§D)
        raw = call(system, user, model)
        try:
            data = _parse_llm_json(raw)
            break
        except (ValueError, json.JSONDecodeError):
            if tentativa == 1:
                bucket.observacao_geral = "Falha ao obter JSON válido do LLM."
                return bucket

    temas = _construir_temas(data, n_analisadas)
    observacao_geral = str(data.get("observacao_geral", ""))

    idioma_ok = _idioma_e_pt_br(_texto_para_checagem_idioma(temas, observacao_geral))
    escopo_ok = not _tem_marcador_de_escopo(observacao_geral)

    if not idioma_ok or not escopo_ok:
        raw_retry = call(system + _REFORCO_VALIDACAO, user, model)
        try:
            data_retry = _parse_llm_json(raw_retry)
            temas = _construir_temas(data_retry, n_analisadas)
            observacao_geral = str(data_retry.get("observacao_geral", ""))
            idioma_ok = _idioma_e_pt_br(
                _texto_para_checagem_idioma(temas, observacao_geral))
            escopo_ok = not _tem_marcador_de_escopo(observacao_geral)
        except (ValueError, json.JSONDecodeError):
            pass  # retentativa não parseou -> mantém o resultado original

    bucket.temas = temas
    bucket.observacao_geral = observacao_geral
    bucket.idioma_invalido = not idioma_ok
    bucket.escopo_suspeito = not escopo_ok
    return bucket


# =====================================================================
# [D2] Narrador — etapa PÓS-síntese (SPEC §D2, v1.2.0)
# =====================================================================
# Recebe EXCLUSIVAMENTE o JSON validado (dict de saída de build_output —
# temas/números/observacoes, NUNCA reviews brutas) e reescreve como prosa.
# A saída volta como JSON {"narrativa": "<texto>"} para reusar os mesmos
# adaptadores (modo JSON nativo) e o parsing defensivo do §D.

NARRATOR_SYSTEM_PROMPT = """\
Você recebe um RELATÓRIO DE RECEPÇÃO já validado de um filme: três grupos de \
reviews separados por faixa de nota (negativas, medianas, positivas), cada um \
com seus temas, frequências aproximadas e uma observação; e, quando \
disponível, uma FICHA TÉCNICA do filme (sinopse oficial, diretor, gênero, \
ano, duração — fonte: TMDB). Sua tarefa é reescrever esse material como um \
texto corrido e envolvente, em TRÊS MOVIMENTOS, SEM subtítulos ou marcações \
entre eles (a divisão é para você se organizar, não para aparecer no texto), \
NESTA ORDEM:

MOVIMENTO 1 — O FILME (2-3 frases; SÓ escreva este movimento SE houver FICHA \
TÉCNICA no relatório — sem ficha, comece direto no MOVIMENTO 2): apresente a \
premissa do filme a partir da `sinopse_oficial` da ficha — pode condensá-la, \
mas é PROIBIDO expandi-la com qualquer conhecimento externo sobre o filme, \
elenco, direção ou produção que não esteja na ficha fornecida. Se a \
`sinopse_oficial` parecer revelar algo além da premissa inicial do filme, \
use só a parte que é premissa e ignore o resto (a ficha NÃO tem passe livre \
sobre a regra de anti-spoiler abaixo). Mencione diretor, gênero e ano; \
duração só se for relevante para o que os dois movimentos seguintes vão \
dizer (ex.: filme muito longo/curto vira tema na experiência).

MOVIMENTO 2 — A EXPERIÊNCIA (3-5 frases): descreva como é assistir ao filme \
usando APENAS características em que os grupos CONCORDAM factualmente, \
mesmo divergindo na avaliação — ex.: se as reviews negativas chamam o ritmo \
de "lento e tedioso" e as positivas de "lento e deliberado", o fato \
consensual compartilhado por trás da divergência é "ritmo lento e \
contemplativo". Tom NEUTRO, SEM valência — este movimento descreve, não \
julga; gostar ou não gostar fica para o MOVIMENTO 3. É PROIBIDO importar \
qualquer informação que não venha dos temas validados dos três grupos. Se \
não houver consensos claros o bastante entre os grupos, este movimento pode \
ser curto (1-2 frases sobre o que os dados permitem dizer, sem forçar um \
consenso que os dados não sustentam).

MOVIMENTO 3 — O CONTRASTE (enxuto — a interface já exibe as barras de \
frequência tema a tema, então aqui priorize os 2-3 temas MAIS FORTES de \
cada grupo, não a cobertura completa dos 6 possíveis): as perspectivas dos \
três grupos — quem não gostou, quem ficou no meio, quem gostou — sobre o \
filme. Neste movimento (e em qualquer lugar do texto que fale de grupos) \
valem as invariantes abaixo, TODAS ainda em vigor:

a. PAPEL: o texto inteiro é para alguém que está DECIDINDO se assiste ao \
filme e que AINDA NÃO ASSISTIU.
b. FIDELIDADE: toda afirmação deve derivar da ficha técnica e/ou dos temas e \
números recebidos. É PROIBIDO adicionar fatos, opiniões próprias, ou \
qualquer contexto externo sobre o filme, elenco, direção ou produção que \
não esteja no relatório. Se não está nos dados, não existe.
c. TAMANHO DOS GRUPOS — REGRA CRÍTICA: os três grupos NÃO têm o tamanho da \
opinião real do público. O tamanho de cada grupo é fixado pelo MÉTODO DE \
COLETA (uma cota fixa por faixa de nota), não pela quantidade de pessoas que \
pensam assim — as medianas, por exemplo, serão sempre o menor grupo por \
construção, em todo filme. Portanto é PROIBIDO comparar tamanhos entre grupos \
ou inferir prevalência global: NADA de "a maioria dos espectadores", "a \
maioria do público", "grupo maior", "grupo menor", "minoria", "igualmente \
expressivo", "recepção polarizada", "opiniões divididas", "consenso" ou \
qualquer equivalente. Trate cada grupo como uma PERSPECTIVA, não como uma \
fatia quantificada do público: apresente-os como "entre quem não gostou...", \
"já entre quem amou...", "para quem ficou no meio-termo...".
d. PROPORÇÕES (só DENTRO de um grupo): proporções são permitidas APENAS \
internamente a um grupo e SEMPRE ancoradas ao denominador daquele grupo. \
NUNCA uma proporção que compare grupos ou fale do público como um todo.
QUANTIFICADOR PRÉ-COMPUTADO (obrigatório, v1.2.3): cada tema do relatório já \
vem com um rótulo_quantificador calculado pelo CÓDIGO a partir da fração \
real de menções — você NÃO calcula nem escolhe o quantificador sozinho. Ao \
expressar a frequência de um tema em prosa, USE o rótulo_quantificador \
fornecido para aquele tema (sinônimos de mesma força são permitidos: "a \
maioria" ~ "mais da metade"; "muitos" ~ "boa parte"; "alguns" ~ "uma \
parte"). É PROIBIDO usar um quantificador MAIS FORTE do que o fornecido. Um \
quantificador MAIS FRACO é permitido se a fluência do texto pedir — nunca \
o oposto. Escala de força, do mais fraco ao mais forte: poucos < \
alguns/uma parte < muitos/boa parte < cerca de metade < a maioria/mais da \
metade < quase todos/praticamente todos.
e. ESTRUTURA: a divisão em três grupos (quem não gostou / quem ficou no meio \
/ quem gostou) deve permanecer legível na prosa do MOVIMENTO 3, em qualquer \
ordem que sirva à narrativa.
f. ESCOPO: cada afirmação sobre um grupo é atribuída ao SEU grupo ("as \
reviews negativas apontam...", "quem deu notas altas destaca..."). É \
PROIBIDO generalizar para "os críticos", "a maioria" (do filme todo) ou "o \
consenso".
g. ANTI-SPOILER: em QUALQUER movimento (incluindo o 1, com a sinopse \
oficial), é PROIBIDO mencionar eventos de trama, personagens específicos ou \
desfechos, mesmo que a sinopse ou algum tema tangencie isso (defesa em \
profundidade — a camada anterior já filtra os temas, você reforça, e a \
sinopse oficial é tratada com a mesma cautela).
h. FORMA: português do Brasil, SEM aspas de citação, SEM subtítulos ou \
rótulos dos movimentos no texto final, entre 250 e 400 palavras ao todo.

Responda APENAS com JSON puro no formato: {"narrativa": "<seu texto>"}"""


# --- Quantificador pré-computado (v1.2.3) ---
# Correção pela raiz do mesmo tipo da v1.1.1 (denominador): o LLM não decide
# mais número nem rótulo numérico — o código é a autoridade. Motivação: a
# calibração por INSTRUÇÃO (v1.2.2, o LLM calculava a fração e escolhia o
# quantificador sozinho) reduziu mas não eliminou o modo de falha "quase
# todos"/"praticamente todos" aplicado a frações de 65-70% — reincidiu 2x na
# primeira regeneração pós-fix (ver changelog v1.2.3).
#
# Faixas idênticas às da v1.2.2, na ordem do mais FRACO ao mais FORTE.
# Cada faixa é (rótulo, limite_inferior_inclusive, limite_superior,
# superior_inclusive). "poucos" é a ÚNICA faixa com superior EXCLUSIVO
# ("abaixo de 10%", i.e. pct < 10); todas as demais são inclusivas nos dois
# extremos, exatamente como escritas na v1.2.2 ("25%-50%" inclui 25 e 50).
#
# Resolução determinística de sobreposição (regra: "sempre o rótulo mais
# fraco"): iterando as faixas do mais fraco pro mais forte e retornando o
# PRIMEIRO match, cada fronteira compartilhada resolve assim:
#   pct == 10  -> só "alguns" bate ("poucos" exige pct < 10, exclusivo)
#   pct == 25  -> "alguns" (10-25) e "muitos" (25-50) empatam -> "alguns"
#   pct == 50  -> "muitos" (25-50), "cerca de metade" (40-60) e "a maioria"
#                 (50-80) empatam -> "muitos" (o mais fraco dos três)
#   pct == 80  -> "a maioria" (50-80) e "quase todos" (≥80) empatam -> "a maioria"
_BANDAS_QUANTIFICADOR_FRACA_PARA_FORTE = [
    ("poucos", 0, 10, False),
    ("alguns", 10, 25, True),
    ("muitos", 25, 50, True),
    ("cerca de metade", 40, 60, True),
    ("a maioria", 50, 80, True),
    ("quase todos", 80, 100, True),
]


def _fracao_percentual(mencoes: int, n_analisadas: int) -> int:
    """Fração mencoes/n_analisadas do grupo, em percentual arredondado
    (inteiro 0-100). n_analisadas <= 0 -> 0 (sem denominador válido)."""
    if not n_analisadas or n_analisadas <= 0:
        return 0
    return round(100 * mencoes / n_analisadas)


def _rotulo_quantificador(pct: int) -> str:
    """Resolve o rótulo determinístico para uma fração percentual (0-100).
    Ver bloco de comentário acima para a tabela de faixas e a resolução
    exata das fronteiras compartilhadas (sempre o rótulo mais fraco)."""
    for rotulo, lo, hi, hi_inclusive in _BANDAS_QUANTIFICADOR_FRACA_PARA_FORTE:
        if pct < lo:
            continue
        if (hi_inclusive and pct <= hi) or (not hi_inclusive and pct < hi):
            return rotulo
    return "quase todos"  # pct > 100 não deveria ocorrer; fallback seguro


def _fracao_e_rotulo(tema: dict) -> tuple[int, str]:
    """(fração%, rótulo) pré-computados para um tema (dict com as chaves
    mencoes_aproximadas/n_reviews_analisadas, como em output['buckets'][i]['temas'])."""
    pct = _fracao_percentual(
        tema.get("mencoes_aproximadas", 0) or 0,
        tema.get("n_reviews_analisadas", 0) or 0,
    )
    return pct, _rotulo_quantificador(pct)


def _algum_tema_tem_fracao_forte(output: dict, limiar_pct: int = 80) -> bool:
    """True se QUALQUER tema de QUALQUER bucket do filme tem fração >= limiar
    — usado pela rede de segurança (v1.2.3) para saber se "quase todos"/
    "praticamente todos" tem lastro em algum lugar do relatório."""
    for b in output.get("buckets", []):
        for t in b.get("temas") or []:
            pct, _ = _fracao_e_rotulo(t)
            if pct >= limiar_pct:
                return True
    return False


def _tem_quantificador_forte_no_texto(texto: str) -> bool:
    t = texto.lower()
    return "quase todos" in t or "praticamente todos" in t


def _serialize_output_for_narrator(output: dict) -> str:
    """Serialização COMPACTA do JSON validado para o narrador (§D2).

    Lê apenas campos seguros de `output` (temas/números/observacoes) — nunca
    reviews brutas (que não existem em `output`). Buckets `sem_analise` entram
    com a contagem e o modo, para que a prosa reflita a escassez sem inventar.

    v1.2.3: cada tema carrega `fracao`/`rótulo_quantificador` PRÉ-COMPUTADOS
    pelo código (`_fracao_e_rotulo`) — o narrador só usa o rótulo dado, nunca
    calcula nem escolhe (ver regra (d) do prompt e a motivação no changelog).

    v1.3.0: quando `output['ficha']` existe (TMDB — ver ficha.py), uma seção
    FICHA TÉCNICA precede os grupos, fonte exclusiva do MOVIMENTO 1 do
    prompt. Ficha ausente (busca falhou/pulada) -> a seção some inteira e o
    prompt já instrui o narrador a pular o MOVIMENTO 1 nesse caso.
    """
    linhas = [
        "RELATÓRIO DE RECEPÇÃO (dados já validados; use SOMENTE isto):",
        f"Total de reviews observadas na coleta do filme: "
        f"{output.get('total_reviews_observadas', 0)}",
        "",
    ]
    ficha = output.get("ficha")
    if ficha:
        linhas.append(
            "FICHA TÉCNICA (TMDB — fonte EXCLUSIVA do MOVIMENTO 1; "
            "sinopse_oficial é material de divulgação curado, PROIBIDO "
            "expandir com conhecimento externo):")
        linhas.append(f"  titulo: {ficha.get('titulo')}")
        linhas.append(f"  ano: {ficha.get('ano')}")
        linhas.append(f"  diretor: {ficha.get('diretor')}")
        linhas.append(f"  generos: {', '.join(ficha.get('generos') or [])}")
        linhas.append(f"  duracao_min: {ficha.get('duracao_min')}")
        linhas.append(f"  sinopse_oficial: {ficha.get('sinopse_oficial')}")
        linhas.append("")
    rotulo = {"negativas": "NÃO GOSTARAM", "medianas": "FICARAM NO MEIO",
              "positivas": "GOSTARAM"}
    for b in output.get("buckets", []):
        nome = b.get("bucket", "?")
        intervalo = _intervalo_bucket(nome) if nome in BUCKETS else ""
        linhas.append(
            f"GRUPO {nome.upper()} ({rotulo.get(nome, '')}, {intervalo}) — "
            f"{b.get('n_validas', 0)} reviews analisadas · modo={b.get('modo')}:")
        obs = b.get("observacao_geral", "")
        if obs:
            linhas.append(f"  observação do grupo: {obs}")
        temas = b.get("temas") or []
        if temas:
            linhas.append("  temas (por frequência decrescente):")
            for t in temas:
                pct, rot_quant = _fracao_e_rotulo(t)
                linhas.append(
                    f"    - {t.get('tema')} — ~{t.get('mencoes_aproximadas')} de "
                    f"{t.get('n_reviews_analisadas')} reviews "
                    f"(fracao: {pct}%, rótulo_quantificador: \"{rot_quant}\"). "
                    f"ex.: {t.get('exemplo_parafraseado')}")
        else:
            linhas.append("  (sem temas — poucas reviews neste grupo)")
        linhas.append("")
    return "\n".join(linhas)


def _validar_prosa(texto: str) -> tuple[str, bool, bool, bool, bool]:
    """Aplica as validações do §D que fazem sentido para prosa livre:
    remoção mecânica de aspas + checagem de idioma, escopo e prevalência (v1.2.1).
    Retorna (texto_limpo, idioma_ok, escopo_ok, prevalencia_ok, aspas_removidas)."""
    limpo, aspas_removidas = _remover_aspas(texto)
    idioma_ok = _idioma_e_pt_br(limpo)
    escopo_ok = not _tem_marcador_de_escopo(limpo)
    prevalencia_ok = not _tem_marcador_de_prevalencia(limpo)
    return limpo, idioma_ok, escopo_ok, prevalencia_ok, aspas_removidas


def narrate_output(output: dict, client_call=None, model: str | None = None,
                   provider: str | None = None) -> "NarrativaResult":
    """[D2] Gera a narrativa em prosa a partir do JSON validado `output`.

    UMA chamada LLM para o filme inteiro (não por bucket), mesmo provider/modelo
    da síntese. Parsing defensivo do JSON `{"narrativa": ...}` com 1 retentativa;
    validações de prosa (idioma/aspas/escopo) com 1 retentativa combinada, nos
    mesmos moldes do §D. A assinatura da spec é `-> str` (o texto); aqui
    retornamos `NarrativaResult` para carregar também a telemetria das flags.
    Rede de segurança do quantificador (v1.2.3): mesmo com o rótulo
    pré-computado no relatório, checa se a prosa usou "quase todos"/
    "praticamente todos" sem QUALQUER tema do filme ter fração >= 80% — o
    único modo de falha observado (ver changelog v1.2.3). Deliberadamente
    restrita a esse quantificador mais forte; não cobre uso indevido dos
    demais rótulos.
    """
    from .models import NarrativaResult

    call, model = _resolve_call_and_model(client_call, model, provider)
    system = NARRATOR_SYSTEM_PROMPT
    user = _serialize_output_for_narrator(output)
    tem_tema_forte = _algum_tema_tem_fracao_forte(output)

    def _uma_chamada(sys_prompt: str) -> str | None:
        raw = call(sys_prompt, user, model)
        try:
            data = _parse_llm_json(raw)
        except (ValueError, json.JSONDecodeError):
            return None
        return str(data.get("narrativa", ""))

    def _quantificador_ok(texto: str) -> bool:
        return not (_tem_quantificador_forte_no_texto(texto) and not tem_tema_forte)

    # chamada + 1 retentativa de JSON inválido
    prosa = _uma_chamada(system)
    if prosa is None:
        prosa = _uma_chamada(system)
    if prosa is None:
        return NarrativaResult(texto="", falhou=True,
                               idioma_invalido=False, escopo_suspeito=False)

    texto, idioma_ok, escopo_ok, prevalencia_ok, aspas_removidas = _validar_prosa(prosa)
    quantificador_ok = _quantificador_ok(texto)

    # 1 retentativa combinada se idioma, escopo, prevalência e/ou
    # quantificador falharem
    if not idioma_ok or not escopo_ok or not prevalencia_ok or not quantificador_ok:
        reforco = _REFORCO_VALIDACAO + _REFORCO_PREVALENCIA + _REFORCO_QUANTIFICADOR
        prosa_retry = _uma_chamada(system + reforco)
        if prosa_retry is not None:
            t2, i2, e2, p2, a2 = _validar_prosa(prosa_retry)
            texto, idioma_ok, escopo_ok, prevalencia_ok = t2, i2, e2, p2
            aspas_removidas = aspas_removidas or a2
            quantificador_ok = _quantificador_ok(texto)

    return NarrativaResult(
        texto=texto,
        idioma_invalido=not idioma_ok,
        escopo_suspeito=not escopo_ok,
        prevalencia_suspeita=not prevalencia_ok,
        quantificador_suspeito=not quantificador_ok,
        aspas_removidas=aspas_removidas,
    )
