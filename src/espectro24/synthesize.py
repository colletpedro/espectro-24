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

import difflib
import json
import os
import re

from .config import (
    BUCKETS,
    EDITOR_LIMIAR_EDICAO_NULA,
    EDITOR_MAX_TENTATIVAS,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT_MS,
    MAX_TEMAS,
    MODEL_DEFAULT,
    PROSA_MAX_TOKENS,
    PROSA_THINKING_BUDGET,
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


# Reforço adicional SÓ para o narrador [D2] (v1.4.1) — telemetria por PAR
# {quantificador, tema}: anexado à retentativa combinada quando um
# quantificador declarado é MAIS FORTE que o rótulo pré-computado do tema
# que ele mesmo citou (ou o tema citado não existe no relatório).
_REFORCO_QUANT_DECLARADO = """
- Se algum item de `quantificadores_usados` declarou uma expressão de \
frequência MAIS FORTE que o rótulo_quantificador do tema citado, ou citou um \
tema que não existe com esse nome EXATO no relatório: reescreva a prosa \
usando, para aquele tema, o rótulo_quantificador fornecido (ou um mais \
fraco) e corrija a lista para citar somente nomes de tema copiados \
literalmente do relatório. O rótulo do relatório é a autoridade — sua \
impressão de "quase todos" não é."""


# Reforço adicional SÓ para o narrador [D2] (v1.4.1) — vocabulário do peso:
# rótulo de peso vem do histograma de NOTAS, não das reviews com texto.
_REFORCO_VOCABULARIO_PESO = """
- Se você escreveu um rótulo de peso acompanhado de "reviews", "público" ou \
"espectadores" (ex.: "a grande maioria das reviews"): troque para "das \
notas". O peso vem do histograma de NOTAS do Letterboxd — todo mundo que \
avaliou o filme —, e não das reviews com texto, que são um subconjunto \
menor. As frequências de TEMA, essas sim, continuam em relação às reviews \
analisadas."""


# Reforço adicional SÓ para o narrador [D2] (v1.5.0) — marcação de
# perspectiva: anexado à retentativa combinada quando algum grupo com
# marcação exigida não teve marcador declarado, teve um trecho que não
# aparece literalmente no texto, ou (marcacao="antecipada") o marcador veio
# depois do meio do trecho sobre aquele grupo.
_REFORCO_MARCADORES = """
- Se algum grupo com marcacao_perspectiva "simples" ou "antecipada" ficou \
SEM um marcador de perspectiva dentro do trecho que fala dele (ex.: "para \
eles", "para esse grupo", "nessa leitura"), ou se `marcadores_perspectiva` \
declarou um trecho que não existe literalmente na narrativa: reescreva \
inserindo o marcador que falta, no início do trecho sobre aquele grupo \
quando a marcação for "antecipada", e registre o trecho EXATO em \
`marcadores_perspectiva`."""


# Reforço adicional SÓ para o narrador [D2] (v1.3.1) — telemetria de
# consensos: anexado à retentativa combinada quando `consensos_usados` cita
# grupo/tema inexistente no relatório recebido.
_REFORCO_CONSENSOS = """
- Se `consensos_usados` citou um grupo ("grupos_de_origem") que não é \
exatamente "negativas", "medianas" ou "positivas", ou um tema \
("temas_de_origem") que não existe, com esse nome EXATO, entre os temas do \
grupo citado no relatório recebido: corrija a lista para citar SOMENTE \
grupos e nomes de tema que existem de fato, copiados literalmente do \
relatório — ou remova o item se ele não tiver sustentação real."""


# Reforço adicional SÓ para o narrador [D2] (v1.4.0) — ancoragem de peso:
# anexado à retentativa combinada quando a prosa ignorou os rotulo_peso
# fornecidos (modo de falha esperado: o modelo reescreve a narrativa antiga,
# de pesos iguais, sem citar nenhum share).
_REFORCO_ANCORAGEM = """
- Se você NÃO ancorou cada grupo no rotulo_peso fornecido pelo relatório: \
reescreva o MOVIMENTO 3 apresentando cada grupo com o seu rotulo_peso (e o \
percentual), começando pela perspectiva de MAIOR peso e dando mais espaço a \
ela. Não trate os três grupos como se pesassem o mesmo — o relatório diz \
quanto cada um pesa de verdade."""


class LLMError(RuntimeError):
    pass


class ProviderError(RuntimeError):
    """Erro na seleção/resolução de provider (chave ausente/ambígua, nome inválido)."""


# --- Adaptadores de provider (contrato: (system, user, model) -> str) ---

def anthropic_client_call(system: str, user: str, model: str,
                          max_tokens: int = LLM_MAX_TOKENS) -> str:
    import anthropic

    key = os.environ.get(PROVIDER_ENV_KEYS["anthropic"])
    if not key:
        raise LLMError(f"{PROVIDER_ENV_KEYS['anthropic']} não definida no ambiente.")
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def anthropic_client_call_prosa(system: str, user: str, model: str) -> str:
    """Variante de PROSA (§D2 narrador / §E2 editor) — v1.6.0: só o teto de
    saída muda (`PROSA_MAX_TOKENS`). O Anthropic não compartilha orçamento
    entre raciocínio e resposta como o Gemini, então não há budget a fixar."""
    return anthropic_client_call(system, user, model, max_tokens=PROSA_MAX_TOKENS)


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
    return _gemini_call(system, user, model, max_output_tokens=LLM_MAX_TOKENS,
                        thinking_budget=0, json_mode=True)


def gemini_client_call_prosa(system: str, user: str, model: str) -> str:
    """Variante de PROSA (§D2 narrador / §E2 editor) — v1.6.0.

    Reverte o `thinking_budget=0` da v1.2.x para um budget FIXO
    (`PROSA_THINKING_BUDGET`) com teto de saída folgado
    (`PROSA_MAX_TOKENS`). O diagnóstico v2 mostrou que o truncamento que
    motivou desligar thinking vinha do raciocínio SEM TETO competindo com a
    resposta pelo mesmo orçamento — com budget fixo, 4/4 chamadas
    terminaram em STOP (ver comentário em `config.py`).
    """
    return _gemini_call(system, user, model,
                        max_output_tokens=PROSA_MAX_TOKENS,
                        thinking_budget=PROSA_THINKING_BUDGET, json_mode=True)


def _gemini_call(system: str, user: str, model: str, *, max_output_tokens: int,
                 thinking_budget: int, json_mode: bool) -> str:
    """Transporte comum do Gemini. `thinking_budget` só é enviado quando o
    modelo suporta (`gemini_supports_thinking`) — passá-lo a um gemini-2.0
    pode ser rejeitado pela API. `json_mode=False` desliga
    `response_mime_type` para etapas cuja saída é texto puro (§E2 editor)."""
    from google import genai
    from google.genai import types

    key = os.environ.get(PROVIDER_ENV_KEYS["gemini"])
    if not key:
        raise LLMError(f"{PROVIDER_ENV_KEYS['gemini']} não definida no ambiente.")
    # TIMEOUT (v1.6.0): sem ele o SDK bloqueia INDEFINIDAMENTE. Observado ao
    # vivo durante a regeneração desta versão — um processo ficou 67 minutos
    # parado, 0% de CPU, dormindo num socket, sem nunca voltar nem falhar.
    # Um timeout transforma "trava para sempre" em "erro que o chamador vê".
    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS),
    )
    config_kwargs = dict(
        system_instruction=system,
        max_output_tokens=max_output_tokens,
    )
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    if gemini_supports_thinking(model):
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_budget=thinking_budget)
    resp = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(**config_kwargs),
    )
    return resp.text


def deepseek_client_call(system: str, user: str, model: str) -> str:
    """Adaptador DeepSeek (v1.8.0) via SDK da OpenAI (compatível — só
    `base_url`/`api_key` mudam), usando MODO JSON explícito.

    Provider ADICIONAL, não default de produção (ver PROVIDER_CLIENTS
    abaixo) — decisão registrada após o encerramento dos experimentos de LLM
    local (`experimentos-ollama-arquivado/`): o free tier do Gemini (20
    req/dia) inviabiliza construir catálogo, e o modelo local não sustentou
    as ~18 invariantes do narrador numa única chamada.

    NON-THINKING explícito (`extra_body={"thinking": {"type": "disabled"}}`)
    — MESMO motivo documentado para o Gemini (`gemini_client_call`) e
    observado também no experimento local: tokens de raciocínio competem
    pelo MESMO orçamento de `max_tokens` que a resposta visível, e já
    causaram truncamento de JSON em dois providers diferentes. deepseek-v4-*
    tem thinking LIGADO por padrão (esforço "high") — desligar não é
    cosmético, é a causa raiz que este adaptador evita de saída.

    `response_format={"type": "json_object"}` — a API exige que a palavra
    "json" apareça em algum lugar do prompt quando esse modo é usado; os
    prompts fixos do §D/§D2 já pedem "Responda APENAS o JSON" (byte-idênticos
    entre providers), então nenhum ajuste de prompt foi necessário.
    """
    return _deepseek_call(system, user, model, max_tokens=LLM_MAX_TOKENS,
                          json_mode=True)


def deepseek_client_call_prosa(system: str, user: str, model: str) -> str:
    """Variante de PROSA (§E2 editor) — v1.8.0.

    DIFERENÇA DELIBERADA da variante JSON: `json_mode=False` (sem
    `response_format`). O editor espera e devolve TEXTO PURO
    (`editar_narrativa`/`_uma_chamada` fazem só um strip de fences
    defensivo) — forçar `response_format=json_object` aqui faria a API
    rejeitar a chamada (ela exige a palavra "json" no prompt quando o modo
    está ligado, e o prompt do editor não promete JSON) ou, na melhor das
    hipóteses, embrulhar a prosa num objeto que `_formato_invalido` (§E2,
    v1.7.2) já rejeitaria. Esse foi exatamente o defeito que invalidou o
    teste do editor no experimento local com Ollama — aqui a diferenciação
    é estrutural desde o primeiro commit, não um fix posterior.
    """
    return _deepseek_call(system, user, model, max_tokens=PROSA_MAX_TOKENS,
                          json_mode=False)


def _deepseek_call(system: str, user: str, model: str, *, max_tokens: int,
                   json_mode: bool) -> str:
    """Transporte comum do DeepSeek. Timeout convertido de ms (`LLM_TIMEOUT_MS`,
    ver `config.py`) para segundos, unidade que o SDK da OpenAI espera."""
    from openai import OpenAI

    key = os.environ.get(PROVIDER_ENV_KEYS["deepseek"])
    if not key:
        raise LLMError(f"{PROVIDER_ENV_KEYS['deepseek']} não definida no ambiente.")
    client = OpenAI(
        api_key=key,
        base_url="https://api.deepseek.com",
        timeout=LLM_TIMEOUT_MS / 1000,
    )
    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        # NON-THINKING explícito — ver docstring de deepseek_client_call.
        extra_body={"thinking": {"type": "disabled"}},
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


PROVIDER_CLIENTS = {
    "anthropic": anthropic_client_call,
    "gemini": gemini_client_call,
    "deepseek": deepseek_client_call,
}

# v1.6.0: adaptadores das etapas de PROSA (§D2 narrador, §E2 editor) — thinking
# fixo + teto folgado. A síntese por bucket (§D) continua em PROVIDER_CLIENTS.
PROVIDER_CLIENTS_PROSA = {
    "anthropic": anthropic_client_call_prosa,
    "gemini": gemini_client_call_prosa,
    "deepseek": deepseek_client_call_prosa,
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


def _resolve_call_and_model(client_call, model, provider, prosa: bool = False):
    """Resolve (call, model) para uma etapa LLM — compartilhado por
    `synthesize_bucket` [D], `narrate_output` [D2] e `editar_narrativa` [E2].
    Client custom sem provider conhecido cai no default histórico
    (`MODEL_DEFAULT`); caso contrário o default de modelo segue o provider
    resolvido.

    v1.6.0: `prosa=True` seleciona os adaptadores de PROSA (thinking fixo +
    teto folgado, ver `config.py`). Um `client_call` injetado (testes) é
    respeitado como sempre — a escolha de adaptador só vale quando o cliente
    não foi fornecido."""
    if client_call is not None:
        return client_call, (model or MODEL_DEFAULT)
    resolved_provider = detect_provider(provider)
    clients = PROVIDER_CLIENTS_PROSA if prosa else PROVIDER_CLIENTS
    return clients[resolved_provider], (model or PROVIDER_DEFAULT_MODELS[resolved_provider])


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


_ASPAS_RE = re.compile(r"\\?[" + re.escape(_ASPAS_CHARS) + r"]")


def _remover_aspas(texto: str) -> tuple[str, bool]:
    """Remoção MECÂNICA (não reescrita) de aspas de citação. Retorna
    (texto_limpo, houve_remocao).

    v1.7.1 — bugfix: a remoção trocava só o CARACTERE de aspas por "", então
    uma citação escapada (`\\"A Cura\\"`, do jeito que o texto às vezes sai
    de dentro de um valor JSON) virava `\\A Cura\\` — a aspas sumia, a
    contrabarra de escape ficava, publicada ao vivo em `cure` e
    `the-invite-2026` (v1.7.0). Agora a contrabarra que precede a aspas é
    removida junto, como uma unidade — nunca uma contrabarra sozinha em
    outro lugar do texto, só a que está imediatamente antes de uma aspas.
    """
    if not any(c in texto for c in _ASPAS_CHARS):
        return texto, False
    limpo = _ASPAS_RE.sub("", texto)
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

_NARRADOR_PARTE_1 = """\
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
usando APENAS propriedades DESCRITIVAS da experiência (ritmo, tom, \
atmosfera, intensidade, estrutura, ambientação, nível de violência, \
ambiguidade, densidade) em que os grupos CONCORDAM no NÚCLEO FACTUAL, mesmo \
divergindo na avaliação. Tom NEUTRO, SEM valência — este movimento \
descreve, não julga; gostar ou não gostar fica para o MOVIMENTO 3. Uma \
propriedade só entra neste movimento se passar nos TRÊS critérios abaixo, \
TODOS obrigatórios (v1.3.1 — reescrito após um defeito real observado):

a. CRITÉRIO DE CATEGORIA: só propriedades DESCRITIVAS. É PROIBIDO qualquer \
juízo de QUALIDADE (atuações boas/ruins, roteiro inteligente/fraco, direção \
competente/questionável, elenco talentoso/fraco) — julgamento de qualidade \
é sempre disputado entre quem gostou e quem não gostou, e pertence ao \
MOVIMENTO 3, NUNCA a este.
b. CRITÉRIO DE PRESENÇA: a propriedade precisa derivar de temas de PELO \
MENOS DOIS grupos, com o mesmo núcleo factual — a valência pode divergir \
("lento e tedioso" num grupo + "lento e deliberado" noutro = consenso \
factual "ritmo lento"; a avaliação de cada grupo sobre esse ritmo é coisa \
diferente e não entra aqui).
c. CRITÉRIO DE NÃO-CONTRADIÇÃO: se QUALQUER grupo contradiz o núcleo \
factual (não só diverge na avaliação, mas nega o fato em si), a propriedade \
está desqualificada — não entra no MOVIMENTO 2 de jeito nenhum.

EXEMPLO POSITIVO (os três critérios satisfeitos): as reviews negativas \
chamam o ritmo de "lento e tedioso", as positivas de "lento e deliberado" \
— ambos descrevem RITMO (categoria descritiva, critério a), os dois grupos \
concordam no núcleo "lento" (critério b), nenhum grupo nega isso (critério \
c) → consenso válido para o MOVIMENTO 2: "ritmo lento e contemplativo".

EXEMPLO NEGATIVO (falha real observada, v1.3.0 — caso de "the-invite-2026"): \
as reviews positivas elogiam "atuações marcantes" e "roteiro inteligente"; \
as negativas têm os temas "atuações e direção questionáveis" e "roteiro \
fraco". Isso NÃO é consenso: é uma propriedade AVALIATIVA (qualidade de \
atuação, qualidade de roteiro — falha o critério a) E os grupos se \
contradizem diretamente sobre ela (falha o critério c também). O correto é \
NÃO mencionar qualidade de atuação/roteiro no MOVIMENTO 2 — essa disputa \
pertence ao MOVIMENTO 3, atribuída a cada grupo separadamente.

É PROIBIDO importar qualquer informação que não venha dos temas validados \
dos três grupos.

OMISSÃO AUTORIZADA (v1.4.1 — leia isto antes de escrever o movimento): se \
MENOS DE DUAS propriedades passarem nos três critérios ao mesmo tempo, este \
movimento deve ser CURTO (1 frase) ou AUSENTE — e a narrativa passa direto \
ao MOVIMENTO 3. OMITIR É O COMPORTAMENTO CORRETO, não uma falha: não há cota \
de frases a cumprir aqui, e um filme cujos temas descritivos são poucos \
simplesmente não tem um MOVIMENTO 2. Preencher o espaço com juízo de \
qualidade suavizado ("estilo visual eficaz", "abordagem arrojada", \
"atuações competentes", "roteiro habilidoso") é PIOR do que não ter o \
movimento — é o defeito que o critério (a) proíbe, disfarçado de descrição \
por um advérbio de hesitação. Quando o movimento é omitido, \
`consensos_usados` vem como lista VAZIA ([]) — isso é resultado esperado, \
não erro. Para \
CADA propriedade usada no MOVIMENTO 2, registre em `consensos_usados` (ver \
formato de saída) a propriedade, os grupos de onde ela veio e os nomes \
EXATOS dos temas (copiados literalmente do relatório) que a sustentam — \
esse registro é o artefato de revisão humana que confirma que o consenso é \
real, não inventado.

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
"""


# --- Regra (c): as DUAS variantes (v1.4.0) ---
# Sem distribuição real de notas, vale a proibição total da v1.2.1 (o dado
# que justificaria falar de prevalência não existe). Com distribuição, a
# regra INVERTE: o peso passa a ser obrigatório e ancorado no share real.
# Só esta regra muda entre as variantes — todo o resto do prompt é
# byte-idêntico, para que a comparação A/B isole a mudança.

_REGRA_C_SEM_DISTRIBUICAO = """\
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
"""


_REGRA_C_COM_DISTRIBUICAO = """\
c. PESO REAL DE CADA GRUPO — REGRA CRÍTICA (a distribuição está disponível \
neste relatório): você recebeu a DISTRIBUIÇÃO REAL das notas do filme, vinda \
do histograma público — quantas pessoas deram cada nota. Isso é um dado \
diferente do tamanho dos grupos de reviews analisadas (50/20/30), que é \
apenas a COTA DE COLETA e continua NÃO significando prevalência. Regras:
- ANCORAGEM OBRIGATÓRIA: cada grupo DEVE ser apresentado, na primeira vez que \
aparecer no MOVIMENTO 3, com o rotulo_peso que veio no relatório para ele \
(ex.: "a grande maioria das notas (~79%)"). É PROIBIDO usar um rótulo MAIS \
FORTE do que o fornecido; um MAIS FRACO é permitido se a fluência pedir — \
nunca o oposto. Você NÃO calcula nem escolhe esse rótulo: ele é dado.
- ABERTURA OBRIGATÓRIA: o MOVIMENTO 3 começa pela perspectiva de MAIOR peso. \
Esta regra tem precedência sobre a liberdade de ordem da regra (e).
- ÊNFASE PROPORCIONAL: dê aproximadamente mais espaço ao grupo de maior peso \
e menos ao de menor peso — um filme amplamente amado não pode soar dividido, \
e um amplamente rejeitado não pode soar morno.
- RESPEITO À MINORIA: a perspectiva minoritária é apresentada COMO \
minoritária, mas SEM desdém, ironia ou insinuação de que quem pensa assim \
está errado. Menos espaço, mesma seriedade analítica: quem procura saber se \
vai gostar precisa entender o que incomodou essa parcela.
- VOCABULÁRIO OBRIGATÓRIO — NOTAS, NUNCA REVIEWS (v1.4.1): o rotulo_peso vem \
do histograma de NOTAS do Letterboxd, ou seja, de TODO MUNDO que avaliou o \
filme; os temas vêm das REVIEWS COM TEXTO, um subconjunto bem menor. São \
duas populações diferentes. Portanto, ao expressar peso, é OBRIGATÓRIO \
escrever "das notas" ("a grande maioria das notas (~79%)") e é PROIBIDO \
escrever "das reviews", "dos espectadores" ou "do público" — o histograma \
não diz nada sobre quem escreveu review nem sobre quem assistiu sem avaliar. \
As frequências de TEMA seguem no vocabulário oposto (regra d): sempre em \
relação às reviews analisadas daquele grupo. Os dois vocabulários nunca se \
misturam.
- Continua PROIBIDO inventar um número-síntese do filme (nota média, score, \
"X de 10", "nota N"): os shares por faixa são a ÚNICA quantificação \
permitida, e são três números, nunca um só.

MARCAÇÃO DE PERSPECTIVA (v1.5.0 — motivada pela regra de REGISTRO abaixo): \
ao reduzir os verbos de reporte, a fala de um grupo minoritário pode soar \
como fato do narrador — porque ela chega depois de o texto já ter \
estabelecido a leitura dominante. Cada grupo do relatório vem com uma \
`marcacao_perspectiva` PRÉ-COMPUTADA (nenhuma/simples/antecipada, a partir \
do share_real — você NÃO calcula nem escolhe esse valor):
- TODO trecho que falar de um grupo precisa conter ao menos uma ANCORAGEM \
de perspectiva para ele; para o grupo DOMINANTE, o próprio rótulo de peso \
já cumpre esse papel ("quem gostou é a grande maioria das notas (~74%)" já \
ancora — nenhum marcador extra é exigido).
- marcacao_perspectiva="simples": além da abertura, inclua ao menos UM \
marcador de perspectiva DENTRO do trecho que fala desse grupo (ex.: "para \
eles", "para esse grupo", "nessa leitura", "quem está nessa faixa").
- marcacao_perspectiva="antecipada": o marcador interno precisa vir ANTES \
da primeira afirmação substantiva sobre esse grupo, não no fim do trecho.
- Um marcador de perspectiva NÃO é um verbo de reporte e NÃO conta para o \
limite da regra (f) de REGISTRO: "para eles o humor é previsível" é \
marcação; "eles apontam que o humor é previsível" é reporte e continua \
limitado.
- É PROIBIDO um marcador com carga depreciativa ("apenas para eles", "só \
para esses poucos") — a perspectiva minoritária continua apresentada com \
respeito (mesma RESPEITO À MINORIA acima).
Para CADA marcador de perspectiva que você usar, registre em \
`marcadores_perspectiva` (ver formato de saída) o grupo e o TRECHO EXATO, \
copiado literalmente da narrativa, onde ele aparece.

"""


_NARRADOR_PARTE_2 = """\
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
DECLARAÇÃO OBRIGATÓRIA DOS QUANTIFICADORES (v1.4.1): para CADA expressão de \
frequência que você usar na prosa ao falar de um tema, registre um item em \
`quantificadores_usados` (ver formato de saída) com o quantificador EXATO \
que você escreveu e o NOME EXATO do tema (copiado literalmente do relatório) \
de onde aquela frequência vem — um item por expressão usada. Antes de \
declarar, confira o par contra o relatório: se o quantificador que você \
escreveu for mais forte que o rótulo_quantificador daquele tema, corrija a \
PROSA (não o registro). Se você não usar nenhum quantificador de tema, a \
lista vem vazia.
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

NOTA SOBRE ESTILO (v1.6.0): não se preocupe com ritmo, variação de frase ou \
elegância da prosa. Um ESTÁGIO SEGUINTE de edição cuida disso, e ele NÃO \
pode alterar nenhum número, rótulo ou atribuição que você escrever. Sua \
única responsabilidade é dizer a verdade com a estrutura acima — escreva de \
forma clara e gramaticalmente correta, e deixe o polimento para depois.

Responda APENAS com JSON puro no formato: {"narrativa": "<seu texto>", \
"consensos_usados": [{"propriedade": "<nome curto da propriedade \
descritiva>", "grupos_de_origem": ["<negativas|medianas|positivas>", ...], \
"temas_de_origem": ["<nome EXATO do tema, copiado do relatório>", ...]}], \
"quantificadores_usados": [{"quantificador": "<a expressão de frequência \
EXATA que você escreveu na prosa>", "tema": "<nome EXATO do tema, copiado \
do relatório, de onde ela vem>"}], "marcadores_perspectiva": [{"grupo": \
"<negativas|medianas|positivas>", "trecho": "<o trecho EXATO da narrativa, \
copiado literalmente, onde o marcador de perspectiva desse grupo \
aparece>"}]}. `consensos_usados` pode ser `[]` se o MOVIMENTO 2 não usou \
nenhuma propriedade consensual (ver OMISSÃO AUTORIZADA); \
`quantificadores_usados` pode ser `[]` se a prosa não quantificou nenhum \
tema; `marcadores_perspectiva` pode ser `[]` quando nenhum grupo do \
relatório exige marcação de perspectiva (regra específica, presente só \
quando o relatório trouxer distribuição real de notas)."""


# Prompt histórico (sem distribuição) — mantido como CONSTANTE com o mesmo
# nome e o mesmo conteúdo byte-a-byte da v1.3.1, para que o fallback seja
# literalmente o comportamento anterior, não uma reescrita parecida.
NARRATOR_SYSTEM_PROMPT = (
    _NARRADOR_PARTE_1 + _REGRA_C_SEM_DISTRIBUICAO + _NARRADOR_PARTE_2
)

NARRATOR_SYSTEM_PROMPT_COM_DISTRIBUICAO = (
    _NARRADOR_PARTE_1 + _REGRA_C_COM_DISTRIBUICAO + _NARRADOR_PARTE_2
)


def build_narrator_prompt(com_distribuicao: bool) -> str:
    """Escolhe a variante da regra (c) do §D2 (v1.4.0).

    `com_distribuicao=False` devolve EXATAMENTE o prompt da v1.3.1 — o
    fallback não é uma aproximação, é o texto anterior. A escolha é feita
    pelo CÓDIGO a partir da presença do dado, nunca pelo LLM.
    """
    return (NARRATOR_SYSTEM_PROMPT_COM_DISTRIBUICAO if com_distribuicao
            else NARRATOR_SYSTEM_PROMPT)


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


# --- v1.4.1: telemetria POR PAR {quantificador, tema} ---
# Motivação (3ª ocorrência do mesmo modo de falha): na v1.4.0 a narrativa de
# `the-invite-2026` escreveu "Quase todos" para o tema "Atuações e química do
# elenco" (20/30 = 67%, rótulo pré-computado "a maioria"). A rede de
# segurança da v1.2.3 é de nível de BUCKET — ela só pergunta se ALGUM tema do
# filme tem fração >=80% — e outro tema do mesmo grupo tinha 83%, dando
# lastro. Nenhuma checagem via prosa consegue saber a QUAL tema um "quase
# todos" solto se refere; por isso o próprio narrador passa a DECLARAR o par,
# no mesmo padrão de `consensos_usados` (v1.3.1), e o código confere par a par
# contra o rótulo pré-computado. O LLM continua sem decidir número ou rótulo:
# ele só declara o que usou, e o código julga.

# Expressão declarada -> posição na escala de força do prompt (0 = mais
# fraco). As chaves cobrem os sinônimos que o próprio prompt autoriza
# ("a maioria" ~ "mais da metade"; "muitos" ~ "boa parte"; "alguns" ~ "uma
# parte") mais as flexões de gênero, que aparecem naturalmente em pt-BR.
_FORCA_QUANTIFICADOR = {
    "poucos": 0, "poucas": 0,
    "alguns": 1, "algumas": 1, "uma parte": 1, "parte dos": 1, "parte das": 1,
    "muitos": 2, "muitas": 2, "boa parte": 2,
    "cerca de metade": 3, "aproximadamente metade": 3, "metade": 3,
    "a maioria": 4, "maioria": 4, "mais da metade": 4,
    "quase todos": 5, "quase todas": 5,
    "praticamente todos": 5, "praticamente todas": 5,
}

# Ordem canônica dos rótulos pré-computados = a própria escala de força.
_ORDEM_ROTULO_QUANTIFICADOR = [r for r, _, _, _ in
                               _BANDAS_QUANTIFICADOR_FRACA_PARA_FORTE]


def _forca_declarada(quantificador: str) -> int | None:
    """Força (0-5) da expressão declarada pelo narrador, ou None se ela não
    for reconhecível.

    Casa por SUBSTRING, testando as chaves mais longas primeiro — assim
    "quase todos os elogios" resolve para "quase todos", e "mais da metade"
    não é confundido com "metade". Expressão irreconhecível devolve None e a
    checagem a ignora: heurística deliberadamente permissiva, como as demais
    redes de segurança do §D2 (limitação documentada na SPEC).
    """
    q = quantificador.lower()
    for chave in sorted(_FORCA_QUANTIFICADOR, key=len, reverse=True):
        if chave in q:
            return _FORCA_QUANTIFICADOR[chave]
    return None


def _rotulos_por_tema(output: dict) -> dict[str, int]:
    """{nome do tema: força do rótulo pré-computado}.

    Tema com o MESMO nome em mais de um grupo (frações diferentes) resolve
    para a força MAIS ALTA entre eles — o par declarado não diz de qual grupo
    veio, e na ambiguidade a checagem prefere não flaggar uma prosa correta.
    """
    forcas: dict[str, int] = {}
    for b in output.get("buckets", []):
        for t in b.get("temas") or []:
            nome = str(t.get("tema", ""))
            _pct, rotulo = _fracao_e_rotulo(t)
            forca = _ORDEM_ROTULO_QUANTIFICADOR.index(rotulo)
            forcas[nome] = max(forcas.get(nome, -1), forca)
    return forcas


def _quantificadores_validos(quantificadores: list, output: dict) -> bool:
    """True se todo par {quantificador, tema} declarado cita um tema REAL do
    filme e usa uma expressão que NÃO é mais forte que o rótulo pré-computado
    daquele tema. Lista vazia é vacuamente válida (a prosa pode não
    quantificar tema nenhum)."""
    forcas = _rotulos_por_tema(output)
    for q in quantificadores or []:
        if not isinstance(q, dict):
            return False
        tema = str(q.get("tema", ""))
        if tema not in forcas:
            return False
        declarada = _forca_declarada(str(q.get("quantificador", "")))
        if declarada is not None and declarada > forcas[tema]:
            return False
    return True


def _normalizar_quantificadores(quantificadores: list) -> list[dict]:
    out = []
    for q in quantificadores or []:
        if not isinstance(q, dict):
            continue
        out.append({
            "quantificador": str(q.get("quantificador", "")),
            "tema": str(q.get("tema", "")),
        })
    return out


def conferencia_quantificador(output: dict, tema_nome: str) -> tuple[int, str] | None:
    """(fração%, rótulo pré-computado) do tema com esse nome exato, ou None se
    ele não existir no relatório. Usada pelo render para exibir, ao lado de
    cada par declarado, o número real contra o qual ele foi conferido —
    telemetria legível, não só um booleano de flag."""
    for b in output.get("buckets", []):
        for t in b.get("temas") or []:
            if str(t.get("tema", "")) == tema_nome:
                return _fracao_e_rotulo(t)
    return None


# --- Peso pré-computado por grupo (v1.4.0) ---
# MESMO princípio da v1.2.3 (quantificador) e da v1.1.1 (denominador): o LLM
# não escolhe o rótulo, o CÓDIGO escolhe. Aqui o insumo é o `share_real` do
# bucket (percentual inteiro vindo do histograma real), não a cota de coleta.
#
# Faixas na ordem do mais FRACO ao mais FORTE; cada uma é
# (rótulo, limite_inferior_inclusive, limite_superior, superior_inclusive).
# "uma pequena minoria" é a única com superior EXCLUSIVO (pct < 10).
#
# Resolução de fronteira (itera do mais fraco pro mais forte, primeiro match
# vence) — MESMA convenção da v1.2.3, "na dúvida, o rótulo mais fraco":
#   pct == 10 -> "uma minoria"            (pequena minoria exige pct < 10)
#   pct == 25 -> "uma minoria"            (empata com parcela expressiva)
#   pct == 45 -> "uma parcela expressiva" (empata com a maioria)
#   pct == 70 -> "a maioria"              (empata com a grande maioria)
# Nota: por isso "a grande maioria" começa de fato em 71%, não em 70% —
# subestimar o peso é aceitável, inflar não é.
# v1.6.0 — faixa NOVA no extremo fraco: "uma fração mínima" (<5%). Motivo
# (observado em `cidade-de-deus`, shares 91/8/1): 8% e 1% recebiam ambos
# "uma pequena minoria", achatando uma diferença de OITO VEZES entre os dois
# grupos minoritários. A faixa nova separa o "muito pouco" do "quase nada"
# sem tocar nas demais fronteiras. Convenção de desempate inalterada (itera
# do mais fraco ao mais forte, primeiro match vence => `pct == 5` resolve
# para "uma pequena minoria", o mais fraco dos dois que batem).
_BANDAS_PESO_FRACA_PARA_FORTE = [
    ("uma fração mínima", 0, 5, False),
    ("uma pequena minoria", 5, 10, False),
    ("uma minoria", 10, 25, True),
    ("uma parcela expressiva", 25, 45, True),
    ("a maioria", 45, 70, True),
    ("a grande maioria", 70, 100, True),
]


def _rotulo_peso(pct: int) -> str:
    """Rótulo determinístico para um share real (0-100)."""
    for rotulo, lo, hi, hi_inclusive in _BANDAS_PESO_FRACA_PARA_FORTE:
        if pct < lo:
            continue
        if (hi_inclusive and pct <= hi) or (not hi_inclusive and pct < hi):
            return rotulo
    return "a grande maioria"  # pct > 100 não deveria ocorrer; fallback seguro


def _rotulo_peso_completo(pct: int) -> str:
    """Forma como o narrador deve escrever: rótulo + percentual, sempre
    juntos — o percentual é o que impede o rótulo de virar retórica solta."""
    return f"{_rotulo_peso(pct)} das notas (~{pct}%)"


def _rotulos_ate(rotulo: str) -> list[str]:
    """O rótulo dado + todos os MAIS FRACOS que ele.

    O prompt permite descer de força ("a grande maioria" -> "a maioria") mas
    nunca subir; a checagem de ancoragem aceita exatamente esse conjunto.
    """
    ordem = [r for r, _, _, _ in _BANDAS_PESO_FRACA_PARA_FORTE]
    return ordem[: ordem.index(rotulo) + 1] if rotulo in ordem else [rotulo]


# --- Marcação de perspectiva pré-computada (v1.5.0) ---
# Motivação: a regra de REGISTRO (v1.5.0) reduz os verbos de reporte a no
# máximo 1 por movimento — mas isso tem um efeito colateral: a fala de um
# grupo minoritário, sem "eles apontam que", pode soar como fato do narrador,
# porque chega depois de o texto já ter estabelecido a leitura dominante. A
# marcação é pré-computada a partir do share_real (MESMO princípio das demais
# pré-computações do §D2: o LLM não decide o valor, só o usa) — depende do
# dado real, por isso só existe quando há distribuição (o mesmo motivo pelo
# qual não dá para usar a COTA de coleta aqui: usar 50/20/30 apresentaria a
# cota como se fosse prevalência, o exato defeito que a v1.2.1 proíbe).
#
# Limiares (ponto de partida, calibráveis — não há evidência empírica ainda
# que os justifique com precisão, ao contrário das faixas de quantificador/
# peso, que vieram de casos reais observados):
#   share > dominante/3   -> "nenhuma"     (grupo grande o bastante por si)
#   share <= dominante/3  -> "simples"     (1 marcador em algum lugar do trecho)
#   share <= dominante/10 -> "antecipada"  (marcador ANTES da 1ª afirmação)
# A condição mais restritiva (antecipada) é checada primeiro: um share que
# satisfaz dominante/10 também satisfaz dominante/3, e "antecipada" implica
# "simples" (o marcador continua lá, só que mais cedo).
def _dominante_share(pesos: dict[str, tuple[int, str]]) -> int | None:
    """Maior share_real entre os grupos com peso, ou None se `pesos` vazio
    (sem distribuição — não há o que ser dominante)."""
    if not pesos:
        return None
    return max(pct for pct, _rot in pesos.values())


def _marcacao_perspectiva(pct: int, dominante: int | None) -> str:
    """Classifica um grupo (nenhuma/simples/antecipada) a partir do seu
    share_real e do share_real do grupo dominante do filme."""
    if not dominante:  # None ou 0 -> nada é dominante o bastante para exigir
        return "nenhuma"
    if pct <= dominante / 10:
        return "antecipada"
    if pct <= dominante / 3:
        return "simples"
    return "nenhuma"


def _marcacoes_por_bucket(pesos: dict[str, tuple[int, str]]) -> dict[str, str]:
    """{bucket: marcacao_perspectiva} para os buckets que TÊM share real.
    Vazio quando `pesos` é vazio (sem distribuição) — mesmo padrão de
    `_pesos_por_bucket`: o vazio é o próprio fallback, sem flag extra."""
    dominante = _dominante_share(pesos)
    return {nome: _marcacao_perspectiva(pct, dominante)
            for nome, (pct, _rot) in pesos.items()}


def _pesos_por_bucket(output: dict) -> dict[str, tuple[int, str]]:
    """{bucket: (share_real, rótulo)} para os buckets que TÊM share real.

    Vazio quando a distribuição não foi coletada — e é esse vazio que faz o
    pipeline inteiro (prompt + validação + render) voltar ao comportamento
    da v1.2.1, sem nenhuma flag extra para checar.
    """
    pesos: dict[str, tuple[int, str]] = {}
    for b in output.get("buckets", []):
        share = b.get("share_real")
        if isinstance(share, int):
            pesos[b.get("bucket", "?")] = (share, _rotulo_peso(share))
    return pesos


def _ancoragem_de_peso_ok(texto: str, pesos: dict[str, tuple[int, str]]) -> bool:
    """True se TODO grupo com peso foi ancorado na prosa.

    Aceita, por grupo: o rótulo fornecido, qualquer rótulo mais fraco (o
    prompt permite), ou o percentual literal. Heurística deliberadamente
    permissiva — a defesa principal é a instrução; isto é rede de segurança
    para o caso de o narrador simplesmente ignorar os pesos e escrever a
    narrativa antiga, que é o modo de falha que importa detectar.

    v1.6.1 — bugfix: `f"{pct}%" in t` era substring solta, então "1%" batia
    DENTRO de "91%" — um grupo de 1% podia ser dado como ancorado só por
    coincidência com o percentual de outro grupo (91%), mascarando um
    `peso_nao_ancorado` real. Mesma causa raiz de `_ancora_de_grupo` (ver
    ali); agora exige que o dígito não seja precedido por outro dígito.
    """
    t = texto.lower()
    for pct, rotulo in pesos.values():
        if any(r in t for r in _rotulos_ate(rotulo)):
            continue
        if re.search(rf"(?<!\d){pct}%", t):
            continue
        return False
    return True


# --- v1.4.1: invariante de vocabulário do peso (notas × reviews) ---
# O rotulo_peso deriva do histograma de NOTAS (todos que avaliaram); os temas
# derivam das REVIEWS COM TEXTO (subconjunto). Dizer "a grande maioria das
# reviews" atribui ao peso um denominador que ele não tem — e é uma
# infidelidade barata de detectar.
_PESO_SUBSTANTIVOS_PROIBIDOS = ("reviews", "público", "publico", "espectadores")

# Rótulos que só podem ser peso. "a maioria" fica DE FORA porque também é um
# rótulo de quantificador de tema, e "a maioria das reviews negativas
# analisadas" é a forma CORRETA exigida pela regra (d) — flaggá-la marcaria
# prosa certa. O caso de "a maioria" usado como peso é coberto pela segunda
# passada, ancorada no percentual (que só acompanha peso).
_ROTULOS_PESO_INEQUIVOCOS = ("uma fração mínima", "uma pequena minoria",
                             "uma minoria", "uma parcela expressiva",
                             "a grande maioria")


def _janela_troca_notas_por_outro(janela: str) -> bool:
    """True se a janela usa um substantivo proibido ANTES de "notas" (ou sem
    "notas" nenhuma) — isto é, o peso foi atribuído a reviews/público/
    espectadores em vez de à população de notas."""
    pos_notas = janela.find("notas")
    for termo in _PESO_SUBSTANTIVOS_PROIBIDOS:
        pos = janela.find(termo)
        if pos != -1 and (pos_notas == -1 or pos < pos_notas):
            return True
    return False


def _vocabulario_peso_ok(texto: str, pesos: dict[str, tuple[int, str]]) -> bool:
    """True se todo rótulo de peso na prosa está acompanhado de "notas".

    Duas passadas complementares, ambas baratas e literais (não é NLP):
    1. rótulos INEQUÍVOCOS de peso -> olha os 40 chars seguintes;
    2. qualquer percentual (`~79%`) -> olha os 60 chars anteriores, o que pega
       "a maioria", ambígua com o quantificador de tema, sem falso positivo:
       frequência de tema nunca vem com percentual na prosa.
    Sem distribuição não há peso a expressar — vacuamente OK.
    """
    if not pesos:
        return True
    t = texto.lower()
    for rotulo in _ROTULOS_PESO_INEQUIVOCOS:
        for m in re.finditer(re.escape(rotulo), t):
            if _janela_troca_notas_por_outro(t[m.end():m.end() + 40]):
                return False
    for m in re.finditer(r"~?\d{1,3}\s?%", t):
        if _janela_troca_notas_por_outro(t[max(0, m.start() - 60):m.start()]):
            return False
    return True


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

    v1.4.0: quando há distribuição real, um bloco DISTRIBUIÇÃO REAL abre o
    relatório e cada GRUPO passa a carregar seu `rotulo_peso` pré-computado.
    Sem distribuição, nada disso aparece e o relatório é o da v1.3.1 — o
    silêncio é o próprio fallback.
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

    pesos = _pesos_por_bucket(output)
    marcacoes = _marcacoes_por_bucket(pesos)
    if pesos:
        distrib = output.get("distribuicao") or {}
        linhas.append(
            "DISTRIBUIÇÃO REAL DAS NOTAS (histograma público do Letterboxd — "
            f"{distrib.get('n_notas_total', 0)} notas no total). Este é o PESO "
            "de cada faixa na recepção real, e é diferente do número de "
            "reviews analisadas (que é cota de coleta). Use o rotulo_peso "
            "abaixo — não calcule nem escolha outro:")
        for nome, (pct, _rot) in pesos.items():
            linhas.append(
                f'  {nome}: share_real {pct}% · rotulo_peso: '
                f'"{_rotulo_peso_completo(pct)}" · marcacao_perspectiva: '
                f'"{marcacoes[nome]}"')
        linhas.append("")

    rotulo = {"negativas": "NÃO GOSTARAM", "medianas": "FICARAM NO MEIO",
              "positivas": "GOSTARAM"}
    for b in output.get("buckets", []):
        nome = b.get("bucket", "?")
        intervalo = _intervalo_bucket(nome) if nome in BUCKETS else ""
        peso_txt = ""
        if nome in pesos:
            peso_txt = (f' · rotulo_peso: "{_rotulo_peso_completo(pesos[nome][0])}"'
                        f' · marcacao_perspectiva: "{marcacoes[nome]}"')
        linhas.append(
            f"GRUPO {nome.upper()} ({rotulo.get(nome, '')}, {intervalo}) — "
            f"{b.get('n_validas', 0)} reviews analisadas · "
            f"modo={b.get('modo')}{peso_txt}:")
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


# --- v1.3.1: telemetria/validação de consensos_usados (MOVIMENTO 2) ---

_GRUPOS_VALIDOS = {"negativas", "medianas", "positivas"}


def _temas_por_grupo(output: dict) -> dict[str, set[str]]:
    return {
        b.get("bucket"): {t.get("tema") for t in (b.get("temas") or [])}
        for b in output.get("buckets", [])
    }


def _consensos_validos(consensos: list, output: dict) -> bool:
    """True se todo item de `consensos_usados` cita SOMENTE grupos válidos
    (negativas/medianas/positivas presentes no relatório) e temas que
    existem, com o nome EXATO, em algum dos grupos citados naquele item.
    Lista vazia é vacuamente válida (MOVIMENTO 2 pode não usar nenhuma)."""
    temas_por_grupo = _temas_por_grupo(output)
    for c in consensos or []:
        if not isinstance(c, dict):
            return False
        grupos = c.get("grupos_de_origem")
        temas = c.get("temas_de_origem")
        if not isinstance(grupos, list) or not isinstance(temas, list):
            return False
        if not all(g in _GRUPOS_VALIDOS and g in temas_por_grupo for g in grupos):
            return False
        temas_disponiveis = set()
        for g in grupos:
            temas_disponiveis |= temas_por_grupo.get(g, set())
        if not all(t in temas_disponiveis for t in temas):
            return False
    return True


def _normalizar_consensos(consensos: list) -> list[dict]:
    out = []
    for c in consensos or []:
        if not isinstance(c, dict):
            continue
        out.append({
            "propriedade": str(c.get("propriedade", "")),
            "grupos_de_origem": [str(g) for g in (c.get("grupos_de_origem") or [])],
            "temas_de_origem": [str(t) for t in (c.get("temas_de_origem") or [])],
        })
    return out


# --- v1.5.0: telemetria/validação de marcadores_perspectiva ---
# "Antecipada" na SPEC significa "antes da PRIMEIRA AFIRMAÇÃO SUBSTANTIVA
# sobre aquele grupo" — não antes do movimento inteiro. No exemplo de estilo
# do prompt, o marcador da minoria ("Para eles...") vem DEPOIS da frase que
# ANCORA o grupo ("Já uma pequena minoria (~3%) não entra na brincadeira"),
# só que na frase SEGUINTE — antes de qualquer afirmação de conteúdo sobre
# esse grupo. A checagem aproxima isso por FRASE (não por parágrafo): acha a
# frase onde o grupo é ancorado (rótulo de peso ou percentual) e exige que o
# marcador apareça naquela mesma frase ou na imediatamente seguinte.

def _ancora_de_grupo(texto: str, pct: int, rotulo: str) -> int | None:
    """Índice (char, minúsculas) da primeira menção ao rótulo de peso do
    grupo (ou um mais fraco — mesmo critério de `_ancoragem_de_peso_ok`) ou
    ao seu percentual. None se nada for encontrado.

    v1.6.1 — bugfix: a busca pelo percentual usava substring solta
    (`t.find(f"{pct}%")`), que casa "1%" DENTRO de "91%" — descoberto ao
    vivo no `cidade-de-deus` real (shares 1/8/91): a âncora de `negativas`
    (1%) "encontrava" o "1" final de "(~91%)" de `positivas`, muito antes
    da menção real, corrompendo o MOVIMENTO inteiro e produzindo falso
    positivo em `perspectiva_nao_marcada`. A busca agora exige que o
    percentual não seja precedido por outro dígito (`(?<!\\d)`), então "1%"
    só casa como número de fato, nunca como sufixo de "91%"/"21%"/etc.
    """
    t = texto.lower()
    candidatos = [t.find(r) for r in _rotulos_ate(rotulo) if t.find(r) != -1]
    m_pct = re.search(rf"(?<!\d){pct}%", t)
    if m_pct:
        candidatos.append(m_pct.start())
    return min(candidatos) if candidatos else None


def _indice_frase_de(frases: list[str], texto: str, idx_char: int) -> int | None:
    """Índice (0-based) da frase de `frases` (saída de `_dividir_frases`)
    que contém o caractere de posição `idx_char` no `texto` original —
    reconstrói offsets por busca sequencial, já que as frases preservam a
    ordem de aparição."""
    if idx_char is None:
        return None
    cursor = 0
    for i, f in enumerate(frases):
        pos = texto.find(f, cursor)
        if pos == -1:
            continue
        fim = pos + len(f)
        if pos <= idx_char <= fim:
            return i
        cursor = fim
    return None


def _span_de_movimento(texto: str, grupo: str,
                       pesos: dict[str, tuple[int, str]]) -> tuple[int, int] | None:
    """(início, fim) do trecho de `texto` associado a `grupo` (v1.6.1) — do
    ponto em que o grupo é ANCORADO (rótulo de peso ou percentual) até a
    âncora do PRÓXIMO grupo que aparece depois dele, ou o fim do texto.

    Aproximação do "movimento daquele grupo", no mesmo espírito de
    `_indice_frase_de`: os movimentos não têm marcação estrutural no texto
    final (o prompt proíbe subtítulos), então a fronteira é inferida pela
    ORDEM em que os grupos são ancorados — coerente com a regra do §D2 de
    que o MOVIMENTO 3 segue a ordem de peso. None se o grupo não tiver peso
    ou não estiver ancorado no texto (nesse caso `_ancoragem_de_peso_ok`,
    checagem separada, já cobre o defeito)."""
    if grupo not in pesos:
        return None
    pct, rotulo = pesos[grupo]
    inicio = _ancora_de_grupo(texto, pct, rotulo)
    if inicio is None:
        return None
    seguintes = [
        idx for g, (p, r) in pesos.items() if g != grupo
        for idx in [_ancora_de_grupo(texto, p, r)]
        if idx is not None and idx > inicio
    ]
    fim = min(seguintes) if seguintes else len(texto)
    return inicio, fim


def _ocorrencias_de_atribuicao(texto: str, inicio: int, fim: int) -> list[int]:
    """Índices ABSOLUTOS (no `texto` completo) de toda ocorrência de uma
    expressão de atribuição reconhecida (`_EXPRESSOES_DE_PERSPECTIVA`)
    dentro de `texto[inicio:fim]`, busca case-insensitive."""
    janela = texto[inicio:fim].lower()
    ocorrencias = []
    for e in _EXPRESSOES_DE_PERSPECTIVA:
        pos = 0
        while True:
            i = janela.find(e, pos)
            if i == -1:
                break
            ocorrencias.append(inicio + i)
            pos = i + len(e)
    return sorted(ocorrencias)


def _marcadores_validos(marcadores: list, texto: str,
                        marcacoes: dict[str, str],
                        pesos: dict[str, tuple[int, str]]) -> bool:
    """True se, para TODO grupo com `marcacao_perspectiva != "nenhuma"`: (a)
    o MOVIMENTO daquele grupo (§`_span_de_movimento`) contém alguma
    expressão de atribuição reconhecida (`_EXPRESSOES_DE_PERSPECTIVA`); (b)
    para `marcacao_perspectiva == "antecipada"`, PELO MENOS UMA dessas
    ocorrências aparece na mesma frase em que o grupo é ancorado (rótulo de
    peso/percentual) ou na imediatamente seguinte. Vacuamente válido quando
    `marcacoes` é vazio (sem distribuição) ou nenhum grupo exige marcação.

    `marcadores` (o que o LLM DECLAROU em `marcadores_perspectiva`) não
    participa mais desta checagem — ver `_normalizar_marcadores`, que
    continua persistindo a declaração como TELEMETRIA de auditoria humana,
    e o changelog v1.6.1 para o porquê.

    **v1.6.1 — por que a checagem passou a escanear o TEXTO, não o
    `trecho` declarado:** a v1.6.0 já tinha corrigido dois defeitos aqui
    (bastar UM marcador bem posicionado por grupo; normalizar caixa/acento/
    demonstrativo antes de comparar), mas um caso real do `cidade-de-deus`
    continuou dando falso positivo mesmo depois: o narrador declarou
    *"Para esse grupo, muitos reconhecem…"* e escreveu na prosa *"Muitos
    NESTE grupo reconhecem…"* — divergência de ORDEM DAS PALAVRAS, não de
    grafia, que nenhuma normalização de caixa/acento fecha. Fechar por
    comparação difusa (similaridade com limiar) foi descartado: um limiar é
    uma linha arbitrária, e a checagem existe para confirmar que o marcador
    de perspectiva EXISTE no texto — não que a frase declarada é uma
    transcrição fiel dele. A correção pela raiz é verificar exatamente essa
    existência: procurar, no trecho de texto associado ao grupo, qualquer
    expressão da MESMA lista que `montar_protegidos` já usa para reconhecer
    atribuição (`_EXPRESSOES_DE_PERSPECTIVA`) — fonte única, sem duplicação.
    """
    frases = _dividir_frases(texto)
    for grupo, marcacao in marcacoes.items():
        if marcacao == "nenhuma":
            continue
        span = _span_de_movimento(texto, grupo, pesos)
        if span is None:
            return False
        ocorrencias = _ocorrencias_de_atribuicao(texto, *span)
        if not ocorrencias:
            return False
        if marcacao == "antecipada":
            pct, rotulo = pesos[grupo]
            si_ancora = _indice_frase_de(
                frases, texto, _ancora_de_grupo(texto, pct, rotulo))
            cedo = any(
                si_ancora is not None
                and _indice_frase_de(frases, texto, idx) in (si_ancora, si_ancora + 1)
                for idx in ocorrencias
            )
            if not cedo:
                return False
    return True


def _normalizar_marcadores(marcadores: list) -> list[dict]:
    out = []
    for m in marcadores or []:
        if not isinstance(m, dict):
            continue
        out.append({
            "grupo": str(m.get("grupo", "")),
            "trecho": str(m.get("trecho", "")),
        })
    return out


# --- v1.5.0: telemetria de fluência (pós-parsing, código) ---
# Diagnóstico (registrado no changelog): o acúmulo de invariantes de
# honestidade (peso ancorado, quantificador pré-computado, escopo por
# grupo...) levou o modelo à ÚNICA forma sintática que satisfaz todas
# simultaneamente — rótulo de peso + verbo de reporte + complemento,
# repetida três vezes, frases de 25-35 palavras quase sem variação. As
# métricas abaixo tornam esse padrão MENSURÁVEL: o código não reescreve a
# prosa, só mede e sinaliza — mesma filosofia das demais telemetrias do §D2.

_VERBOS_REPORTE_STEMS = (
    "elogi", "destac", "apont", "relat", "consider", "classific",
    "mencion", "ressalt", "reconhec", "express", "descrev",
)
_RE_VERBO_REPORTE = re.compile(
    r"\b(?:" + "|".join(_VERBOS_REPORTE_STEMS) + r")\w*", re.IGNORECASE)

# Lista fechada e literal (não é NLP) — os quatro exemplos da regra (h) mais
# sinônimos comuns da mesma família de intensificador. Deliberadamente NÃO
# cobre todo advérbio em -mente (ex. "praticamente"/"geralmente" não são
# intensificadores) — heurística restrita, como as demais do módulo.
_ADVERBIOS_INTENSIFICADORES = {
    "intensamente", "profundamente", "extremamente", "excessivamente",
    "totalmente", "completamente", "absolutamente", "imensamente",
    "tremendamente", "surpreendentemente", "extraordinariamente",
    "impressionantemente", "brutalmente", "fortemente",
}

_RE_FRASE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")
_RE_PALAVRA = re.compile(r"[^\W\d_]+", re.UNICODE)


def _dividir_frases(texto: str) -> list[str]:
    """Divisão simples por pontuação de fim de frase (.!?) — heurística, não
    trata abreviações; suficiente para telemetria de estilo, propositalmente
    imperfeita como o resto do módulo."""
    return [f.strip() for f in _RE_FRASE.findall(texto) if f.strip()]


def _n_palavras(frase: str) -> int:
    return len(_RE_PALAVRA.findall(frase))


def _primeira_palavra(frase: str) -> str:
    m = _RE_PALAVRA.search(frase)
    return m.group(0).lower() if m else ""


def _metricas_fluencia(texto: str) -> dict:
    """Calcula as métricas de ritmo sobre o texto final da narrativa.

    `cv_comprimento` = desvio padrão ÷ média de palavras por frase — mede
    VARIAÇÃO de comprimento (a regra de ritmo pede variação, não frases
    curtas o tempo todo). `aberturas_repetidas` conta pares de frases
    CONSECUTIVAS que começam pela mesma primeira palavra (normalizada,
    minúscula) — proxy barato para "mesma estrutura de abertura" (regra b),
    não uma análise sintática real.
    """
    frases = _dividir_frases(texto)
    n_frases = len(frases)
    if n_frases == 0:
        return {
            "n_frases": 0, "media_palavras": 0.0, "cv_comprimento": 0.0,
            "frase_mais_curta": 0, "aberturas_repetidas": 0,
            "verbos_reporte": 0, "adverbios_mente": 0,
        }
    comprimentos = [_n_palavras(f) for f in frases]
    media = sum(comprimentos) / n_frases
    variancia = sum((c - media) ** 2 for c in comprimentos) / n_frases
    desvio = variancia ** 0.5
    cv = (desvio / media) if media > 0 else 0.0

    aberturas = [_primeira_palavra(f) for f in frases]
    aberturas_repetidas = sum(
        1 for i in range(1, n_frases)
        if aberturas[i] and aberturas[i] == aberturas[i - 1]
    )

    palavras_lower = [w.lower() for w in _RE_PALAVRA.findall(texto)]
    adverbios_mente = sum(1 for w in palavras_lower
                          if w in _ADVERBIOS_INTENSIFICADORES)
    verbos_reporte = len(_RE_VERBO_REPORTE.findall(texto))

    return {
        "n_frases": n_frases,
        "media_palavras": round(media, 1),
        "cv_comprimento": round(cv, 2),
        "frase_mais_curta": min(comprimentos),
        "aberturas_repetidas": aberturas_repetidas,
        "verbos_reporte": verbos_reporte,
        "adverbios_mente": adverbios_mente,
    }


# v1.6.0 — `_fluencia_ok` REMOVIDA, e com ela os gatilhos automáticos de
# retentativa por métrica e a flag `fluencia_baixa`.
#
# Motivo (DIAGNOSTICO_FLUENCIA_V2.md): as métricas NÃO acompanham qualidade.
# No `cure`, o texto qualitativamente melhor (thinking on) pontuou PIOR em
# `cv_comprimento` (0.35 -> 0.28) e em `verbos_reporte` (3 -> 6) que o texto
# pior. `cv_comprimento` mede DISPERSÃO de comprimento de frase, não
# legibilidade: um texto com frases uniformemente boas pontua mal, e um texto
# truncado no meio pontua bem. Otimizar contra elas — que é o que uma
# retentativa automática faz — empurra o modelo a degradar a prosa para
# satisfazer um número.
#
# `_metricas_fluencia` continua sendo calculada e persistida em
# `metricas_fluencia`: vira telemetria de DIAGNÓSTICO para leitura humana,
# no mesmo estatuto de `consensos_usados` — material de revisão, não critério
# automático. O eixo de fluência passa a ser responsabilidade do editor (§E2).


def _validar_prosa(texto: str, com_distribuicao: bool = False
                   ) -> tuple[str, bool, bool, bool, bool]:
    """Aplica as validações do §D que fazem sentido para prosa livre:
    remoção mecânica de aspas + checagem de idioma, escopo e prevalência (v1.2.1).
    Retorna (texto_limpo, idioma_ok, escopo_ok, prevalencia_ok, aspas_removidas).

    v1.4.0 — a checagem de PREVALÊNCIA muda de sinal conforme o dado:
    - SEM distribuição: como na v1.2.1, palavras como "minoria"/"a maioria do
      público" são violação (o dado que as justificaria não existe).
    - COM distribuição: essas mesmas palavras passam a ser EXIGIDAS pela
      regra (c) invertida — manter o detector ligado geraria flag em toda
      narrativa correta. Ele é desligado, e quem cobre este eixo passa a ser
      a checagem de ANCORAGEM (`_ancoragem_de_peso_ok`), aplicada em
      `narrate_output`.
    """
    limpo, aspas_removidas = _remover_aspas(texto)
    idioma_ok = _idioma_e_pt_br(limpo)
    escopo_ok = not _tem_marcador_de_escopo(limpo)
    prevalencia_ok = (True if com_distribuicao
                      else not _tem_marcador_de_prevalencia(limpo))
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

    v1.4.1 — telemetria POR PAR: a checagem acima é de nível de BUCKET e não
    pegou a 3ª reincidência do modo de falha ("quase todos" para um tema de
    67%, enquanto outro tema do mesmo grupo tinha 83% e dava lastro). O
    narrador passa a DECLARAR `quantificadores_usados` — {quantificador,
    tema} — e o código confere par a par contra o rótulo pré-computado
    daquele tema; par inflado ou tema inexistente => retentativa com reforço
    e, se persistir, a mesma flag `quantificador_suspeito`. Também v1.4.1: o
    vocabulário do peso ("das notas", nunca "das reviews"/"do público"/"dos
    espectadores"), com flag própria `vocabulario_peso_suspeito`.
    """
    from .models import NarrativaResult

    call, model = _resolve_call_and_model(client_call, model, provider)
    # v1.4.0: a presença do dado — não uma flag de configuração — decide qual
    # variante da regra (c) vale. Sem distribuição, tudo abaixo degrada
    # sozinho para o comportamento da v1.3.1.
    pesos = _pesos_por_bucket(output)
    com_distribuicao = bool(pesos)
    # v1.5.0: marcação de perspectiva também depende do dado real — vazio
    # sem distribuição, mesmo padrão de `pesos`.
    marcacoes = _marcacoes_por_bucket(pesos)
    system = build_narrator_prompt(com_distribuicao)
    user = _serialize_output_for_narrator(output)
    tem_tema_forte = _algum_tema_tem_fracao_forte(output)

    def _uma_chamada(sys_prompt: str) -> tuple[str, list, list, list] | None:
        raw = call(sys_prompt, user, model)
        try:
            data = _parse_llm_json(raw)
        except (ValueError, json.JSONDecodeError):
            return None
        consensos = data.get("consensos_usados")
        if not isinstance(consensos, list):
            consensos = []
        quantificadores = data.get("quantificadores_usados")
        if not isinstance(quantificadores, list):
            quantificadores = []
        marcadores = data.get("marcadores_perspectiva")
        if not isinstance(marcadores, list):
            marcadores = []
        return str(data.get("narrativa", "")), consensos, quantificadores, marcadores

    def _quantificador_bucket_ok(texto: str) -> bool:
        """Rede de segurança da v1.2.3 (nível de BUCKET) — mantida em vigor."""
        return not (_tem_quantificador_forte_no_texto(texto) and not tem_tema_forte)

    # chamada + 1 retentativa de JSON inválido
    resultado = _uma_chamada(system)
    if resultado is None:
        resultado = _uma_chamada(system)
    if resultado is None:
        return NarrativaResult(texto="", falhou=True,
                               idioma_invalido=False, escopo_suspeito=False)

    def _ancoragem_ok(texto: str) -> bool:
        # Sem distribuição não há o que ancorar: vacuamente OK.
        return _ancoragem_de_peso_ok(texto, pesos) if com_distribuicao else True

    prosa, consensos_brutos, quantificadores_brutos, marcadores_brutos = resultado
    texto, idioma_ok, escopo_ok, prevalencia_ok, aspas_removidas = _validar_prosa(
        prosa, com_distribuicao)
    quant_bucket_ok = _quantificador_bucket_ok(texto)
    quant_declarado_ok = _quantificadores_validos(quantificadores_brutos, output)
    consensos_ok = _consensos_validos(consensos_brutos, output)
    ancoragem_ok = _ancoragem_ok(texto)
    vocabulario_ok = _vocabulario_peso_ok(texto, pesos)
    marcadores_ok = _marcadores_validos(marcadores_brutos, texto, marcacoes, pesos)
    # v1.6.0: métricas viram DIAGNÓSTICO — calculadas e persistidas, mas sem
    # gatilho de retentativa (ver nota em `_metricas_fluencia`).
    metricas = _metricas_fluencia(texto)

    # 1 retentativa combinada se idioma, escopo, prevalência, quantificador
    # (nível de bucket, v1.2.3, ou por par declarado, v1.4.1), consensos_usados
    # (v1.3.1), ancoragem de peso (v1.4.0), vocabulário do peso (v1.4.1) ou
    # marcadores de perspectiva (v1.5.0) falharem. Fluência saiu desta lista
    # na v1.6.0 — é responsabilidade do editor (§E2), não do narrador.
    if not idioma_ok or not escopo_ok or not prevalencia_ok \
            or not quant_bucket_ok or not quant_declarado_ok \
            or not consensos_ok or not ancoragem_ok or not vocabulario_ok \
            or not marcadores_ok:
        reforco = _REFORCO_VALIDACAO + _REFORCO_QUANTIFICADOR
        # o reforço de prevalência PROÍBE falar de peso — anexá-lo com
        # distribuição presente contradiria a regra (c) invertida.
        if not com_distribuicao:
            reforco += _REFORCO_PREVALENCIA
        if not quant_declarado_ok:
            reforco += _REFORCO_QUANT_DECLARADO
        if not consensos_ok:
            reforco += _REFORCO_CONSENSOS
        if not ancoragem_ok:
            reforco += _REFORCO_ANCORAGEM
        if not vocabulario_ok:
            reforco += _REFORCO_VOCABULARIO_PESO
        if not marcadores_ok:
            reforco += _REFORCO_MARCADORES
        retry = _uma_chamada(system + reforco)
        if retry is not None:
            prosa2, consensos2, quantificadores2, marcadores2 = retry
            t2, i2, e2, p2, a2 = _validar_prosa(prosa2, com_distribuicao)
            texto, idioma_ok, escopo_ok, prevalencia_ok = t2, i2, e2, p2
            aspas_removidas = aspas_removidas or a2
            quant_bucket_ok = _quantificador_bucket_ok(texto)
            quantificadores_brutos = quantificadores2
            quant_declarado_ok = _quantificadores_validos(
                quantificadores_brutos, output)
            consensos_brutos = consensos2
            consensos_ok = _consensos_validos(consensos_brutos, output)
            ancoragem_ok = _ancoragem_ok(texto)
            vocabulario_ok = _vocabulario_peso_ok(texto, pesos)
            marcadores_brutos = marcadores2
            marcadores_ok = _marcadores_validos(marcadores_brutos, texto, marcacoes, pesos)
            metricas = _metricas_fluencia(texto)

    return NarrativaResult(
        texto=texto,
        idioma_invalido=not idioma_ok,
        escopo_suspeito=not escopo_ok,
        prevalencia_suspeita=not prevalencia_ok,
        # v1.4.1: a MESMA flag passa a ser alimentada pelas DUAS checagens —
        # a de bucket (v1.2.3) e a por par declarado (v1.4.1).
        quantificador_suspeito=not (quant_bucket_ok and quant_declarado_ok),
        aspas_removidas=aspas_removidas,
        consensos_usados=_normalizar_consensos(consensos_brutos),
        consenso_suspeito=not consensos_ok,
        peso_nao_ancorado=not ancoragem_ok,
        quantificadores_usados=_normalizar_quantificadores(quantificadores_brutos),
        vocabulario_peso_suspeito=not vocabulario_ok,
        marcadores_perspectiva=_normalizar_marcadores(marcadores_brutos),
        perspectiva_nao_marcada=not marcadores_ok,
        metricas_fluencia=metricas,
    )


# =====================================================================
# [E2] Editor — passe de EDIÇÃO pós-narrador (SPEC §E2, v1.6.0)
# =====================================================================
# Por que existe: até a v1.5.0, um único prompt acumulava honestidade
# (números, rótulos, atribuição, anti-spoiler) E fluência (ritmo, registro).
# O diagnóstico mostrou que isso falhou em três frentes — as regras de ritmo
# não transferiram entre filmes, as métricas que as fiscalizavam não
# acompanhavam qualidade, e a configuração de produção chegou a publicar uma
# frase agramatical. A v1.6.0 separa: o narrador (§D2) responde por VERDADE,
# o editor (§E2) por LEITURA — e o editor é estruturalmente incapaz de
# mentir, porque não recebe nenhuma fonte de fato (nem buckets, nem reviews,
# nem ficha), só o texto já validado e a lista de trechos intocáveis.

_EDITOR_SYSTEM_PROMPT = """\
Você é um EDITOR de texto. Recebe um texto pronto sobre a recepção de um \
filme e o reescreve para que ele SOE MELHOR — sem mudar nada do que ele diz.

Você NÃO tem acesso aos dados de origem. Tudo o que você pode afirmar já \
está no texto recebido; não há nada a acrescentar, e você não teria como \
verificar nada que inventasse.

REGRA INVIOLÁVEL — TRECHOS PROTEGIDOS: junto do texto você recebe uma lista \
de TRECHOS PROTEGIDOS. Cada um deles precisa aparecer no seu texto final \
EXATAMENTE como foi entregue — mesmos caracteres, mesma pontuação, mesmos \
números, sem reformulação, sem sinônimo, sem reordenar as palavras dentro \
do trecho. Você pode mover um trecho protegido para outro ponto da frase ou \
do parágrafo, e pode reescrever tudo em volta dele; o que não pode é alterar \
o trecho por dentro. Se uma melhoria de ritmo exigir quebrar um trecho \
protegido, NÃO faça a melhoria — o trecho vence. EXCEÇÃO ÚNICA: se mover um \
trecho protegido para o meio de uma frase deixar a letra inicial dele com a \
caixa errada (maiúscula que devia virar minúscula, ou o contrário), você \
PODE ajustar só essa primeira letra — nenhuma outra letra, palavra, número \
ou pontuação do trecho.

TAMBÉM PROIBIDO:
- adicionar, remover ou alterar QUALQUER número ou percentual, mesmo fora \
dos trechos protegidos;
- adicionar, remover ou alterar nome próprio (de pessoa, filme, lugar);
- adicionar, remover ou alterar qualquer afirmação factual — se o texto diz \
que um grupo achou o ritmo lento, o seu texto diz a mesma coisa;
- acrescentar informação que não esteja no texto recebido, inclusive \
conhecimento seu sobre o filme;
- trocar a quem uma opinião é atribuída.

O QUE VOCÊ DEVE FAZER:

RITMO:
- alterne períodos longos (30-50 palavras) com frases curtas (3-10 palavras);
- o texto final precisa ter pelo menos UMA frase de até 10 palavras;
- não abra dois períodos seguidos com a mesma estrutura;
- use conectivos de fala ("só que", "aí", "já", "e", "mas"); pode iniciar \
período por conjunção.

REGISTRO:
- prefira verbos a nominalizações: "as situações se repetem e o filme cansa", \
não "a repetição das situações torna a experiência cansativa";
- no máximo UM advérbio terminado em -mente no texto inteiro;
- reduza verbos de reporte (elogia, destaca, aponta, relata, considera, \
classifica, menciona, ressalta, reconhece) quando já estiver claro de quem é \
a opinião — MAS nunca à custa de um trecho protegido, e nunca apagando a \
atribuição de quem pensa o quê.

TOM: alguém contando de um filme para um amigo. Fluido e leve, mas SEM \
gíria, SEM emoji, SEM interpelação direta ao leitor ("você vai adorar"), SEM \
hipérbole, SEM aspas de citação.

GRAMÁTICA (obrigatório): cada período do texto final precisa ser uma frase \
completa e correta em português do Brasil — sujeito e predicado coerentes, \
concordância certa, sem anacoluto. Se o texto recebido contiver um período \
quebrado ou truncado, CORRIGI-LO É OBRIGATÓRIO; essa é a única situação em \
que você reescreve a estrutura de uma frase por necessidade, e mesmo assim \
preservando o que ela afirma e os trechos protegidos que ela contém. Isso \
vale mesmo quando o defeito ocorre perto de um trecho protegido ou o \
encosta ("destacando a a maioria o estilo visual", "de de", artigo ou \
preposição repetidos): CORRIGIR É OBRIGATÓRIO, contanto que o trecho \
protegido em si permaneça intacto por dentro — o que pode mudar é a \
palavra ao lado dele, nunca ele mesmo.

TAMANHO: o texto final deve ter entre 220 e 400 palavras.

EXEMPLO DE RITMO COM FILME FICTÍCIO — nunca reaproveitar seu conteúdo. O \
filme abaixo NÃO EXISTE e os números são INVENTADOS: servem só para mostrar \
a FORMA (variação de comprimento, aberturas diferentes, atribuição \
preservada). Copiar qualquer fato, adjetivo ou número daqui seria inventar \
informação.

ANTES (ritmo monótono):
"A grande maioria das notas (~74%) elogia intensamente a condução do filme \
e o trabalho de câmera, destacando a habilidade de sustentar o clima em \
cena. Uma minoria das notas (~19%) reconhece a competência técnica, mas \
sente que a indefinição do meio e a duração prolongada tornam a experiência \
cansativa na segunda metade. Uma pequena minoria (~7%) classifica o ritmo \
como arrastado e os personagens como estáticos."

DEPOIS (ritmo desejado — mesmos fatos, mesmos números, mesma atribuição):
"Quem gostou é a grande maioria das notas (~74%), e o elogio se concentra \
num ponto só: o filme não tem pressa e usa isso a favor, porque cada \
silêncio entre os dois protagonistas pesa mais que a cena anterior. Uma \
minoria das notas (~19%) chega até a metade junto. Para esse grupo, o \
problema aparece quando a história precisa decidir para onde vai, e não \
decide. Já uma pequena minoria (~7%) não embarca em momento nenhum. Para \
eles a lentidão nunca vira método, os personagens não saem do lugar, e o \
final chega sem ter construído nada."

Responda APENAS com o texto final editado, em PROSA CORRIDA. Sem \
preâmbulo, sem explicação, sem JSON, sem markdown, sem cerca de código \
(```), sem envolver a resposta num objeto ou campo (nada de `{`, `}`, \
`"text":`, `"narrativa":` ou qualquer rótulo antes do texto), sem aspas \
envolvendo o texto. A primeira palavra da sua resposta já é a primeira \
palavra da narrativa."""


_REFORCO_EDITOR_PROTEGIDOS = """

REFORÇO CRÍTICO — sua edição anterior QUEBROU trechos protegidos. Os \
trechos abaixo precisam aparecer no texto final EXATAMENTE assim, \
caractere por caractere, e NÃO apareceram:
{lista}
Reescreva mantendo cada um deles intacto. Se precisar, use menos liberdade \
de ritmo: a integridade dos trechos vem antes do estilo."""


_REFORCO_EDITOR_NUMEROS = """

REFORÇO CRÍTICO — sua edição anterior ALTEROU os números do texto. O \
conjunto de números e percentuais do texto final tem de ser IDÊNTICO ao do \
texto recebido: nenhum número novo, nenhum removido, nenhum modificado. \
Não arredonde, não converta, não escreva por extenso um número que veio em \
algarismo (nem o contrário)."""


# v1.7.2 — reforço para formato inválido (invólucro estrutural em vez de
# prosa corrida): caso real do `cidade-de-deus`, onde o editor devolveu
# `{ text: "..." }` em vez de só o texto.
_REFORCO_EDITOR_FORMATO = """

REFORÇO CRÍTICO — sua edição anterior veio EMBRULHADA em alguma estrutura \
(JSON, cerca de código, um objeto com campo "text"/"narrativa") em vez de \
ser só o texto corrido. Responda de novo com APENAS a prosa final, sem \
chaves, colchetes, aspas de campo, cercas de código (```), ou qualquer \
rótulo antes do texto — a primeira palavra da sua resposta já é a primeira \
palavra da narrativa."""


# v1.7.4 — reforço para edição NULA (texto devolvido praticamente idêntico
# ao recebido, sem reestruturação real de ritmo).
_REFORCO_EDITOR_EDICAO_NULA = """

REFORÇO CRÍTICO — o texto que você devolveu é PRATICAMENTE IDÊNTICO ao que \
você recebeu. Isso não é uma edição: é a mesma coisa de novo. Reescreva de \
verdade — reestruture os períodos (junte frases curtas, quebre frases \
longas, varie a abertura de cada uma), sem mudar nenhum número, rótulo de \
peso ou atribuição. O texto final deve LER diferente do original, mesmo \
dizendo exatamente a mesma coisa."""


def _tokens_numericos(texto: str) -> list[str]:
    """Multiconjunto ORDENADO de tokens numéricos do texto (números com ou
    sem `~`/`%`). Usado para provar que a edição não mexeu em nenhum número:
    a comparação é de multiconjunto, então repetições contam — trocar
    "~79%" por "~78%" ou duplicar um número quebra a igualdade."""
    return sorted(re.findall(r"\d[\d.,]*\s?%?", texto))


# Expressões de atribuição de perspectiva (§D2). São elas que carregam o
# sentido "isto é a leitura DAQUELE grupo" — o resto do período declarado é
# conteúdo comum, que o editor precisa poder reescrever.
_EXPRESSOES_DE_PERSPECTIVA = (
    "quem está nessa faixa", "quem está nesta faixa",
    "para esse grupo", "para este grupo", "neste grupo", "nesse grupo",
    "para esse público", "para este público", "esse público", "este público",
    "nessa leitura", "nesta leitura", "para esses", "para estes",
    "para eles", "para elas",
    # v1.7.1 (Tarefa 3) — família "quem gostou/não gostou/amou/...": caso
    # real do `cure`, grupo de 3% ("quem não gostou considerou o ritmo
    # lento e tedioso") — a construção CUMPRE a função de atribuição, só
    # não estava na lista, e produzia falso positivo em
    # `perspectiva_nao_marcada` mesmo com o texto honesto e bem marcado.
    "quem gostou", "quem não gostou", "quem amou", "quem ficou no meio",
    "para quem gostou", "para quem não gostou",
    # "para quem" ISOLADO ficou DE FORA de propósito: é pronome relativo
    # comum ("para quem o filme é superestimado…") e casava dentro da
    # própria frase agramatical do `cure`, blindando o defeito que o editor
    # tem de consertar. Todo item acima exige uma palavra a mais depois de
    # "quem" — nunca casa com esse uso solto.
)


def _fatia_real(texto: str, candidato: str) -> str | None:
    """A fatia de `texto` que casa `candidato` ignorando maiúsculas, com o
    caixa ORIGINAL preservado — ou None se não ocorrer."""
    i = texto.lower().find(candidato.lower())
    return texto[i:i + len(candidato)] if i != -1 else None


def montar_protegidos(res, output: dict) -> list[str]:
    """Lista de TRECHOS PROTEGIDOS (§E2 3.3), montada em CÓDIGO a partir do
    que o narrador JÁ declarou — o editor nunca escolhe o que é intocável.

    Fontes: (1) rótulos de peso COMPLETOS com percentual, (2) todo token que
    contenha dígito.

    v1.7.0 — a lista foi ENXUGADA: até a v1.6.2, também protegia as
    expressões de quantificador (`quantificadores_usados`) e de atribuição
    de perspectiva (`marcadores_perspectiva`) literalmente. Na prática, com
    14-16 protegidos por filme (incluindo palavras soltas como "muitos"), o
    editor era descartado com frequência (`cure`) ou inventava frases
    penduradas só para reencaixar um protegido no lugar novo
    (`cidade-de-deus`: "Essa é a opinião de uma fração mínima das notas.").
    Um defeito gramatical real da bruta ("destacando a a maioria o estilo
    visual") sobreviveu porque "a maioria" estava protegido.

    A remoção é segura porque as duas coisas JÁ TÊM verificação SEMÂNTICA
    melhor do que a comparação literal: quantificador é conferido pelo par
    declarado contra o rótulo pré-computado (`conferencia_quantificador`,
    v1.4.1), e atribuição é conferida pela varredura do movimento
    (`_marcadores_validos`, v1.6.1) — nenhuma das duas exige que a STRING
    exata sobreviva, só que a AFIRMAÇÃO sobreviva. Proteger a string era
    redundante com uma checagem melhor, e engessava a reescrita.

    Só entram candidatos que REALMENTE aparecem no texto do narrador —
    proteger uma string ausente tornaria a checagem impossível de satisfazer
    (o editor seria punido por algo que o narrador não escreveu).
    """
    texto = res.texto or ""
    candidatos: list[str] = []

    # (1) rótulos de peso — SEMPRE com percentual, a forma canônica e as
    # mais fracas permitidas (nunca a forma nua "___ das notas" sem
    # percentual, que não é o que a Tarefa 2.1(a) pede para proteger).
    for pct, rotulo in _pesos_por_bucket(output).values():
        candidatos.append(_rotulo_peso_completo(pct))
        for r in _rotulos_ate(rotulo):
            candidatos.append(f"{r} das notas (~{pct}%)")

    # (2) todo token numérico (percentual, ano, duração), SEM a pontuação
    # em volta: proteger "(~3%)," blindaria o parêntese e a vírgula, e
    # repontuar é metade do trabalho de ritmo do editor.
    candidatos.extend(re.findall(r"~?\d[\d.,]*\s?%?", texto))

    vistos: set[str] = set()
    protegidos: list[str] = []
    for c in candidatos:
        c = c.strip()
        if not c:
            continue
        # O protegido tem de ser a forma COMO ELA APARECE no texto: o
        # narrador capitaliza no início de frase ("A grande maioria das
        # notas (~79%)"), enquanto o rótulo canônico é minúsculo. Proteger a
        # forma canônica cobraria do editor uma string que o narrador nunca
        # escreveu. Casa case-insensitive e guarda a fatia real.
        real = c if c in texto else _fatia_real(texto, c)
        if real is None or real in vistos:
            continue
        vistos.add(real)
        protegidos.append(real)
    # mais longos primeiro: se um protegido contém outro, o maior é o que
    # realmente restringe, e a lista fica legível para o modelo
    protegidos.sort(key=len, reverse=True)
    return protegidos


def build_editor_user_message(texto: str, protegidos: list[str]) -> str:
    """Entrada do editor: SÓ o texto e os trechos protegidos.

    Nenhum bucket, nenhuma review, nenhuma ficha, nenhum tema — a garantia
    anti-invenção do §E2 é estrutural, não uma instrução que o modelo possa
    ignorar: o que não está aqui, o editor não tem como saber.
    """
    linhas = ["TEXTO A EDITAR:", texto, "", "TRECHOS PROTEGIDOS (reproduza cada um EXATAMENTE):"]
    if protegidos:
        linhas.extend(f"- {p}" for p in protegidos)
    else:
        linhas.append("(nenhum)")
    return "\n".join(linhas)


def _variante_primeira_letra(s: str) -> str:
    """`s` com a caixa da PRIMEIRA letra alternada (maiúscula<->minúscula) e
    o resto intocado. Sem efeito se `s` for vazio ou começar por algo que
    não é letra (ex. um token numérico)."""
    if not s or not s[0].isalpha():
        return s
    primeira = s[0].lower() if s[0].isupper() else s[0].upper()
    return primeira + s[1:]


def _protegido_presente(protegido: str, texto: str) -> bool:
    """True se `protegido` aparece LITERALMENTE em `texto`, ou aparece com
    só a PRIMEIRA LETRA em caixa alternada (v1.7.1, Tarefa 2).

    O rótulo de peso guarda a caixa de onde apareceu a primeira vez — em
    início de frase, capitalizado ("A grande maioria das notas (~91%)").
    Quando o editor move o trecho para o meio de um período
    ("Para a grande maioria das notas (~91%), Cidade de Deus..."), só a
    letra inicial deveria minguar para minúscula; o resto do trecho (a
    palavra, o número, o percentual) continua exigido letra por letra.
    Sem esta folga, o editor não tinha como corrigir a capitalização sem
    quebrar o protegido e ser descartado — publicado ao vivo em
    `cidade-de-deus` (v1.7.0): "Para A grande maioria...", "Já Uma pequena
    minoria...", maiúscula no meio da frase.
    """
    return protegido in texto or _variante_primeira_letra(protegido) in texto


def _protegidos_perdidos(texto_editado: str, protegidos: list[str]) -> list[str]:
    return [p for p in protegidos if not _protegido_presente(p, texto_editado)]


_CAMPO_JSON_RE = re.compile(r'^\s*"?[A-Za-z_][\w]*"?\s*:\s*\S')


def _formato_invalido(bruto_editado: str) -> bool:
    """[E2] Checagem ESTRUTURAL (v1.7.2), aplicada ANTES das demais.

    Caso real: o `cidade-de-deus` (v1.7.1) devolveu a prosa embrulhada num
    invólucro `{ text: "..." }`, ignorando a instrução de responder só
    texto puro. As checagens de então (protegidos, conjunto numérico,
    honestidade) rodam sobre SUBSTRING, então o protegido e os números
    continuavam achados DENTRO do invólucro — nada pegou o defeito, que só
    foi visto por leitura humana antes de publicar.

    Sinais de invólucro, qualquer um já é o bastante:
    - o texto COMEÇA com `{` ou `[` — a prosa nunca começa assim;
    - contém cerca de código markdown (```);
    - alguma das primeiras linhas casa um campo estilo JSON
      (`"text":`, `text:`, `"narrativa":` — identificador seguido de `:`
      logo no início da linha, com ou sem aspas);
    - chaves desbalanceadas (`{`/`}` em quantidade diferente) — um objeto
      truncado ou mal formado deixa esse rastro mesmo sem bater nos sinais
      acima.

    Deliberadamente NÃO rejeita uma chave/colchete equilibrado no MEIO da
    prosa (ex. uma citação entre chaves que o narrador tenha usado) — só
    pega o formato de invólucro, não qualquer ocorrência do caractere.
    """
    t = bruto_editado.strip()
    if not t:
        return False   # texto vazio é tratado em outro lugar
    if t[0] in "{[":
        return True
    if "```" in t:
        return True
    primeiras_linhas = [l for l in t.splitlines() if l.strip()][:3]
    if any(_CAMPO_JSON_RE.match(l) for l in primeiras_linhas):
        return True
    if t.count("{") != t.count("}"):
        return True
    return False


def _normalizar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def _similaridade(a: str, b: str) -> float:
    """[E2] Similaridade (0-1) entre dois textos, normalizados só por
    espaço em branco (v1.7.4) — `difflib.SequenceMatcher.ratio`, a mesma
    ferramenta que `diff`/`git diff` usam por baixo. Não normaliza caixa
    nem pontuação de propósito: o que importa aqui é se o editor
    REESTRUTUROU o texto, não se ele preserva palavras (preservar
    vocabulário protegido é esperado e correto)."""
    return difflib.SequenceMatcher(
        None, _normalizar_espacos(a), _normalizar_espacos(b)).ratio()


_ROTULOS_PESO_CANONICOS = [r for r, _, _, _ in _BANDAS_PESO_FRACA_PARA_FORTE]


def _inicio_de_periodo(texto: str, pos: int) -> bool:
    """True se a posição `pos` está em início de período: ou é o início do
    próprio texto, ou o primeiro caractere não-espaço antes dela é
    `.`/`!`/`?`."""
    i = pos - 1
    while i >= 0 and texto[i].isspace():
        i -= 1
    return i < 0 or texto[i] in ".!?"


def _corrigir_capitalizacao_residual(texto: str) -> tuple[str, bool]:
    """[E2] Pós-processamento DETERMINÍSTICO sobre a edição já ACEITA
    (v1.7.4, Tarefa 2) — baixa a inicial de um rótulo de peso que apareça
    capitalizado no MEIO de um período.

    Defeito conhecido e recorrente: a v1.7.1 AUTORIZOU o editor a ajustar
    a caixa de um rótulo de peso movido para o meio da frase (ver
    `_protegido_presente`), mas não o OBRIGA — e ele frequentemente não
    ajusta ("Já Uma fração mínima das notas...", "Para A grande
    maioria..."). Mesmo princípio de todas as pré-computações do pipeline:
    o que é determinístico, o CÓDIGO decide, o LLM só usa. Só a primeira
    letra do rótulo é tocada, e só quando ele NÃO está em início de
    período; nenhuma outra palavra, número ou pontuação é alterada.
    """
    ajustado = False
    for rotulo in _ROTULOS_PESO_CANONICOS:
        capitalizado = rotulo[0].upper() + rotulo[1:]
        padrao = re.compile(r"\b" + re.escape(capitalizado) + r"\b")
        pos = 0
        while True:
            m = padrao.search(texto, pos)
            if not m:
                break
            if _inicio_de_periodo(texto, m.start()):
                pos = m.end()
                continue
            texto = texto[:m.start()] + rotulo[0].lower() + rotulo[1:] + texto[m.end():]
            ajustado = True
            pos = m.start() + len(rotulo)
    return texto, ajustado


def editar_narrativa(narrativa_result, protegidos: list[str], output: dict | None = None,
                     client_call=None, model: str | None = None,
                     provider: str | None = None):
    """[E2] Reescreve a narrativa para ritmo/leitura sem alterar conteúdo.

    De 1 a `1 + EDITOR_MAX_TENTATIVAS` chamadas LLM por filme, após o
    narrador (v1.7.3 — até a v1.7.2 eram no máximo 2). A assinatura da spec
    (`-> str`) corresponde ao campo `.texto` do `EdicaoResult` devolvido.

    Verificação mecânica (§E2, Tarefa 4) sobre o texto editado, na ordem:
      (0, v1.7.2) checagem ESTRUTURAL — rejeita invólucro tipo JSON/markdown;
      (a) todo trecho protegido aparece LITERALMENTE (com a exceção de
          capitalização inicial, v1.7.1);
      (b) o multiconjunto de tokens numéricos é IDÊNTICO ao do original;
      (c) as validações de honestidade do §D2 são REEXECUTADAS (idioma,
          aspas, escopo, prevalência, vocabulário de peso, ancoragem,
          atribuição de perspectiva) e nenhuma pode regredir;
      (d, v1.7.4) EDIÇÃO NULA — se (a)-(c) TERIAM passado mas o texto é
          praticamente idêntico à bruta (similaridade >=
          `EDITOR_LIMIAR_EDICAO_NULA`), reprova mesmo assim: um editor que
          devolve a entrada quase intacta passava por (a)-(c) sem
          nenhum sinal (é o mesmo texto), e ficava marcado "aplicada".
    Falha em qualquer uma → retentativa com o reforço da checagem que
    falhou, ACUMULADO com o de tentativas anteriores (v1.7.3, Tarefa 2 —
    se a tentativa 1 falhar por número e a 2 por atribuição, a 3 recebe os
    dois reforços, para o modelo não consertar um problema criando outro).
    Esgotadas as `EDITOR_MAX_TENTATIVAS` retentativas, a edição é
    DESCARTADA e a narrativa original do narrador prevalece
    (`edicao_descartada=True`). O editor pode não melhorar o texto; o que
    ele não pode, em hipótese alguma, é piorá-lo. `n_tentativas` e
    `motivos_por_tentativa` (`EdicaoResult`) registram quantas chamadas
    foram feitas e por que cada uma falhou, para telemetria.
    `similaridade` (v1.7.4) é persistida SEMPRE, aceita ou não, para
    calibração humana do limiar. Uma edição ACEITA ainda passa por um
    pós-processamento determinístico (`_corrigir_capitalizacao_residual`,
    v1.7.4) que baixa a caixa de um rótulo de peso capitalizado fora de
    início de período — `capitalizacao_ajustada` registra se algo mudou.
    """
    from .models import EdicaoResult

    texto_bruto = (narrativa_result.texto or "").strip()
    if not texto_bruto:
        return EdicaoResult(texto="", texto_bruto="", falhou=True,
                            edicao_descartada=True,
                            motivo_descarte="narrativa vazia — nada a editar")

    call, model = _resolve_call_and_model(client_call, model, provider, prosa=True)

    output = output or {}
    pesos = _pesos_por_bucket(output)
    com_distribuicao = bool(pesos)
    numeros_originais = _tokens_numericos(texto_bruto)
    marcacoes = _marcacoes_por_bucket(pesos) if com_distribuicao else {}

    # estado de honestidade do texto ORIGINAL — a edição não pode regredir
    # em relação a ele (e não é obrigada a consertar o que já vinha marcado)
    _, idioma0, escopo0, prevalencia0, _ = _validar_prosa(texto_bruto, com_distribuicao)
    vocab0 = _vocabulario_peso_ok(texto_bruto, pesos)
    ancora0 = _ancoragem_de_peso_ok(texto_bruto, pesos) if com_distribuicao else True
    # v1.7.0 — a atribuição de perspectiva não é mais protegida por STRING
    # literal (Tarefa 2): a checagem que garante que ela sobrevive é esta
    # revalidação SEMÂNTICA (`_marcadores_validos`, a mesma do §D2 v1.6.1),
    # não mais a presença de "Para eles"/"Para esse grupo" em `protegidos`.
    marc0 = _marcadores_validos([], texto_bruto, marcacoes, pesos) if com_distribuicao else True

    user = build_editor_user_message(texto_bruto, protegidos)

    def _uma_chamada(sys_prompt: str) -> str | None:
        raw = call(sys_prompt, user, model)
        if not raw:
            return None
        # o editor responde texto puro; o strip de fences é defensivo
        return _strip_fences(str(raw)).strip() or None

    def _avaliar(bruto_editado: str):
        """(texto_limpo, perdidos, numeros_ok, honestidade_ok, motivo, similaridade).

        v1.7.2 — a checagem ESTRUTURAL (`_formato_invalido`) roda PRIMEIRO,
        antes de qualquer outra: um invólucro tipo `{ text: "..." }` ainda
        contém os protegidos e os números como SUBSTRING lá dentro, então
        as checagens seguintes o aceitariam. Se o formato já está errado,
        nem avalia o resto — falha direto com motivo "formato_invalido".

        v1.7.4 — a SIMILARIDADE com a bruta é calculada SEMPRE (mesmo nos
        casos que falham por outro motivo), para telemetria persistida em
        todo resultado. A checagem de EDIÇÃO NULA roda por ÚLTIMO, só
        quando as demais TERIAM passado: se perdidos/números/honestidade
        já reprovam a edição por um motivo mais específico, é esse motivo
        que importa reportar — a edição nula só precisa de checagem
        própria no caso que mais importa, o que passaria despercebido por
        TODAS as outras (o editor devolve a entrada praticamente intacta:
        protegidos presentes porque nunca saíram, números idênticos porque
        nada mudou, honestidade não regride porque é o mesmo texto).
        """
        similaridade = _similaridade(texto_bruto, bruto_editado)
        if _formato_invalido(bruto_editado):
            return bruto_editado, [], True, False, "formato_invalido", similaridade
        texto, idioma_ok, escopo_ok, prevalencia_ok, _asp = _validar_prosa(
            bruto_editado, com_distribuicao)
        perdidos = _protegidos_perdidos(texto, protegidos)
        numeros_ok = _tokens_numericos(texto) == numeros_originais
        vocab_ok = _vocabulario_peso_ok(texto, pesos)
        ancora_ok = _ancoragem_de_peso_ok(texto, pesos) if com_distribuicao else True
        marc_ok = (_marcadores_validos([], texto, marcacoes, pesos)
                  if com_distribuicao else True)
        regressoes = []
        if idioma0 and not idioma_ok:
            regressoes.append("idioma")
        if escopo0 and not escopo_ok:
            regressoes.append("escopo")
        if prevalencia0 and not prevalencia_ok:
            regressoes.append("prevalencia")
        if vocab0 and not vocab_ok:
            regressoes.append("vocabulario_peso")
        if ancora0 and not ancora_ok:
            regressoes.append("ancoragem_peso")
        if marc0 and not marc_ok:
            regressoes.append("perspectiva_nao_marcada")
        motivo = ""
        if perdidos:
            motivo = f"{len(perdidos)} trecho(s) protegido(s) perdido(s)"
        elif not numeros_ok:
            motivo = "conjunto de números do texto foi alterado"
        elif regressoes:
            motivo = "regressão de honestidade: " + ", ".join(regressoes)
        elif similaridade >= EDITOR_LIMIAR_EDICAO_NULA:
            # v1.7.4: só chega aqui quando NENHUMA outra checagem reprovou —
            # é exatamente o caso que passava despercebido até esta versão.
            return bruto_editado, [], True, False, "edicao_nula", similaridade
        return texto, perdidos, numeros_ok, not regressoes, motivo, similaridade

    def _reforco_desta_falha(motivo: str, perdidos: list[str], numeros_ok: bool) -> str:
        """Bloco de reforço específico da checagem que falhou NESTA
        tentativa. v1.7.3: cada bloco distinto é ACUMULADO entre
        tentativas (ver loop abaixo) em vez de substituir o anterior — se
        a tentativa 1 falhou por número e a 2 por atribuição, a 3 recebe
        os dois reforços, para o modelo não consertar um problema criando
        outro."""
        r = ""
        if motivo == "formato_invalido":
            r += _REFORCO_EDITOR_FORMATO
        if motivo == "edicao_nula":
            r += _REFORCO_EDITOR_EDICAO_NULA
        if perdidos:
            r += _REFORCO_EDITOR_PROTEGIDOS.format(
                lista="\n".join(f"- {p}" for p in perdidos))
        if not numeros_ok:
            r += _REFORCO_EDITOR_NUMEROS
        if not r:   # regressão de honestidade sem os motivos acima: reforça o essencial
            r = _REFORCO_EDITOR_NUMEROS
        return r

    # v1.7.3 (Tarefa 1): até `1 + EDITOR_MAX_TENTATIVAS` chamadas no total —
    # a chamada inicial mais até `EDITOR_MAX_TENTATIVAS` retentativas.
    # Defeito real que motivou a mudança: na regeneração da v1.7.1, a
    # mesma combinação de código+dados que a v1.7.0 tinha aceitado nos 3
    # filmes foi DESCARTADA em 2 deles (`cure` — número alterado;
    # `cidade-de-deus` — regressão de `perspectiva_nao_marcada`) — pura
    # VARIÂNCIA do modelo entre chamadas, não regressão de código. Uma
    # única retentativa dava pouca chance de a variância favorecer, e o
    # descarte já é fail-safe (a bruta sempre prevalece), então o custo de
    # tentar mais vezes é só chamadas de API, nunca honestidade.
    reforcos_acumulados: list[str] = []   # blocos DISTINTOS já usados
    motivos_por_tentativa: list[str] = []
    texto = texto_bruto
    perdidos: list[str] = []
    numeros_ok = True
    honestidade_ok = True
    motivo = ""
    similaridade = None   # só definida quando alguma tentativa é avaliada
    n_tentativas = 0
    teve_resposta = False   # ao menos uma chamada devolveu texto avaliável

    for _ in range(1 + EDITOR_MAX_TENTATIVAS):
        sys_prompt = _EDITOR_SYSTEM_PROMPT + "".join(reforcos_acumulados)
        resposta = _uma_chamada(sys_prompt)
        n_tentativas += 1

        if resposta is None:
            motivo = "editor não devolveu texto"
            perdidos, numeros_ok, honestidade_ok = [], True, False
        else:
            teve_resposta = True
            texto, perdidos, numeros_ok, honestidade_ok, motivo, similaridade = _avaliar(resposta)
            if not (perdidos or not numeros_ok or not honestidade_ok):
                break   # aceita — nenhuma checagem falhou

        motivos_por_tentativa.append(motivo)
        bloco = _reforco_desta_falha(motivo, perdidos, numeros_ok)
        if bloco not in reforcos_acumulados:
            reforcos_acumulados.append(bloco)

    houve_retentativa = n_tentativas > 1

    if perdidos or not numeros_ok or not honestidade_ok:
        # DESCARTE: esgotadas as tentativas, a narrativa do narrador prevalece.
        return EdicaoResult(
            texto=texto_bruto, texto_bruto=texto_bruto,
            edicao_descartada=True, motivo_descarte=motivo, falhou=not teve_resposta,
            protegidos_perdidos=perdidos[:10], numeros_alterados=not numeros_ok,
            houve_retentativa=houve_retentativa,
            metricas_fluencia=_metricas_fluencia(texto_bruto),
            n_tentativas=n_tentativas, motivos_por_tentativa=motivos_por_tentativa,
            similaridade=similaridade,
        )

    # v1.7.4 (Tarefa 2): pós-processamento DETERMINÍSTICO sobre a edição já
    # ACEITA — baixa a caixa de um rótulo de peso capitalizado no meio de
    # um período (a v1.7.1 autorizou o editor a fazer isso, mas não o
    # obriga, e ele frequentemente não ajusta).
    texto, capitalizacao_ajustada = _corrigir_capitalizacao_residual(texto)

    return EdicaoResult(
        texto=texto, texto_bruto=texto_bruto,
        edicao_descartada=False, houve_retentativa=houve_retentativa,
        metricas_fluencia=_metricas_fluencia(texto),
        n_tentativas=n_tentativas, motivos_por_tentativa=motivos_por_tentativa,
        similaridade=similaridade, capitalizacao_ajustada=capitalizacao_ajustada,
    )
