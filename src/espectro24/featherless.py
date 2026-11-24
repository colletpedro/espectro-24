"""Featherless: transporte OpenAI com livro-caixa persistente e teto por sessão.

Configuração obrigatória: FEATHERLESS_SESSION_DIR com plano.json obtido de
/v1/plan. Um SQLite compartilhado coordena reserva de USD e unidades entre
threads/processos. Reservas ambíguas (timeout/queda/usage ausente) NÃO são
liberadas. Nunca se presume que erro de transporte custou zero.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from decimal import Decimal, ROUND_CEILING
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid

from .preco import FEATHERLESS_PRECOS, FEATHERLESS_CACHE_PRECOS, agora_utc_iso

_contexto = ContextVar('featherless_contexto', default={})
NANO = Decimal(1_000_000_000)


class TetoExcedido(RuntimeError):
    pass


@contextmanager
def contexto(estagio: str, slug: str | None = None, bucket: str | None = None):
    valores = dict(_contexto.get())
    valores.update({k:v for k,v in dict(estagio=estagio, slug=slug, bucket=bucket).items() if v is not None})
    token = _contexto.set(valores)
    try:
        yield
    finally:
        _contexto.reset(token)


def metadados():
    return dict(_contexto.get())


def custo_nano(model: str, entrada: int, saida: int, cache_tokens: int = 0) -> int:
    if not 0 <= cache_tokens <= entrada or saida < 0:
        raise ValueError('contadores de tokens inválidos')
    p = FEATHERLESS_PRECOS[model]
    cache = Decimal(FEATHERLESS_CACHE_PRECOS.get(model, p['prompt']))
    return int(((Decimal(p['prompt']) * (entrada-cache_tokens) + cache * cache_tokens + Decimal(p['completion']) * saida)
                * NANO).to_integral_value(rounding=ROUND_CEILING))


class Sessao:
    def __init__(self, pasta, teto_usd='3.00', unidades=None, *, etapa='1', prazo_utc=None):
        self.pasta = Path(pasta)
        self.pasta.mkdir(parents=True, exist_ok=True)
        plano = json.loads((self.pasta / 'plano.json').read_text())
        permitidas = int(plano['concurrency'])
        self.unidades = permitidas if unidades is None else int(unidades)
        if not 0 < self.unidades <= permitidas:
            raise ValueError('concorrência deve respeitar /v1/plan')
        self.contexto_maximo = plano.get('max_context_length')
        self.teto = int(Decimal(str(teto_usd)) * NANO)
        limite = {'1': 3_000_000_000, '2': 15_000_000_000}.get(str(etapa), 0)
        if not 0 < self.teto <= limite:
            raise ValueError('teto excede a autorização da etapa')
        self.prazo_utc = prazo_utc
        if str(etapa) == '2' and (prazo_utc is None or prazo_utc > 1794182400):
            raise ValueError('etapa 2 exige prazo até 2026-11-09 00:00 UTC')
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, teto INTEGER, unidades INTEGER)')
            db.execute('INSERT OR IGNORE INTO config VALUES (1, ?, ?)', (self.teto, self.unidades))
            if db.execute('SELECT teto, unidades FROM config').fetchone() != (self.teto, self.unidades):
                raise ValueError('configuração da sessão persistida é imutável')
            db.execute('CREATE TABLE IF NOT EXISTS chamadas (id TEXT PRIMARY KEY, reservado INTEGER, custo INTEGER, unidades INTEGER, estado TEXT, registro TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS politica (etapa TEXT, prazo REAL)')
            if db.execute('SELECT count(*) FROM politica').fetchone()[0] == 0:
                db.execute('INSERT INTO politica VALUES (?, ?)', (str(etapa), prazo_utc))
            if db.execute('SELECT etapa, prazo FROM politica').fetchone() != (str(etapa), prazo_utc):
                raise ValueError('política da sessão persistida é imutável')
            from .sessao_featherless import politica
            global_ = politica(db)
            if global_:
                self.teto, self.prazo_utc, _ = global_

    def db(self):
        return sqlite3.connect(self.pasta / 'caixa.sqlite3', timeout=30)

    def reservar(self, valor: int, unidades: int) -> str:
        if unidades > self.unidades:
            raise ValueError('modelo excede unidades permitidas')
        inicio = time.monotonic()
        while True:
            # Não iniciar uma chamada que possa sobreviver à parada rígida.
            from .synthesize import LLM_PRAZO_PAREDE_S
            if self.prazo_utc is not None and time.time() + LLM_PRAZO_PAREDE_S >= self.prazo_utc:
                raise TetoExcedido('prazo da etapa atingido (incluindo margem da chamada)')
            with self.db() as db:
                db.execute('BEGIN IMMEDIATE')
                from .sessao_featherless import politica
                global_ = politica(db)
                if global_:
                    self.teto, self.prazo_utc, bloqueado = global_
                    if bloqueado: raise TetoExcedido('sessão bloqueada: cobrança fora do contrato')
                gasto, ativas = db.execute("SELECT coalesce(sum(coalesce(custo,reservado)),0), coalesce(sum(CASE WHEN estado IN ('ativa','incerta') THEN unidades ELSE 0 END),0) FROM chamadas").fetchone()
                if gasto + valor > self.teto:
                    raise TetoExcedido(f'reserva excederia teto: {(gasto+valor)/1e9:.6f} > {self.teto/1e9:.2f} USD')
                if ativas + unidades <= self.unidades:
                    rid = uuid.uuid4().hex
                    db.execute('INSERT INTO chamadas VALUES (?, ?, NULL, ?, ?, NULL)', (rid, valor, unidades, 'ativa'))
                    return rid
            if time.monotonic() - inicio > 60:
                raise TimeoutError('unidades de concorrência indisponíveis por 60s')
            time.sleep(.05)

    def concluir(self, rid: str, registro: dict, custo: int | None):
        registro = dict(registro, reserva_id=rid, custo_usd=None if custo is None else custo/1e9)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            reserva, = db.execute('SELECT reservado FROM chamadas WHERE id=?', (rid,)).fetchone()
            # Um dado de cobrança fora do contrato bloqueia novas chamadas.
            estado = 'incerta' if custo is None else 'concluida'
            db.execute('UPDATE chamadas SET custo=?, estado=?, registro=? WHERE id=?',
                       (custo, estado, json.dumps(registro, ensure_ascii=False), rid))
            # SQLite é a fonte durável; JSONL é exportável inclusive após queda.
            with (self.pasta / 'uso.jsonl').open('a') as f:
                f.write(json.dumps(registro, ensure_ascii=False) + '\n')
        if custo is not None and custo > reserva:
            raise TetoExcedido('uso excedeu reserva conservadora; interromper e reconciliar')

    def resumo(self):
        with self.db() as db:
            custo, reservado, n = db.execute('SELECT coalesce(sum(custo),0), coalesce(sum(CASE WHEN custo IS NULL THEN reservado ELSE 0 END),0), count(*) FROM chamadas').fetchone()
        return dict(custo_usd=custo/1e9, reservas_pendentes_usd=reservado/1e9, chamadas=n, teto_usd=self.teto/1e9)


def sessao_ambiente():
    pasta = os.environ.get('FEATHERLESS_SESSION_DIR')
    if not pasta:
        raise ValueError('FEATHERLESS_SESSION_DIR obrigatório: nenhum gasto sem livro-caixa')
    return Sessao(pasta, os.environ.get('FEATHERLESS_TETO_USD', '3.00'),
                  os.environ.get('FEATHERLESS_CONCURRENCY_UNITS'),
                  etapa=os.environ.get('FEATHERLESS_ETAPA', '1'),
                  prazo_utc=float(os.environ['FEATHERLESS_PRAZO_UTC']) if os.environ.get('FEATHERLESS_PRAZO_UTC') else None)


def client():
    from .synthesize import featherless_client
    return featherless_client()


def resposta(system, user, model, *, max_tokens, json_mode, client=None,
             estagio=None, slug=None, bucket=None, reasoning_effort=None,
             temperature=None, seed=None, sessao=None, response_schema=None):
    from . import synthesize as S
    sessao = sessao or sessao_ambiente()
    p = FEATHERLESS_PRECOS[model]  # desconhecido = recusa antes da rede
    ctx = min(p['context_length'], sessao.contexto_maximo or p['context_length'])
    if not isinstance(max_tokens, int) or not 0 < max_tokens < ctx:
        raise ValueError('max_tokens fora do contexto')
    # Toda a janela de entrada, não heurística caracteres/token. Cobre o
    # template do servidor e o pior caso de raciocínio dentro de max_tokens.
    reserva = custo_nano(model, ctx, max_tokens)
    kwargs = dict(model=model, messages=[dict(role='system', content=system), dict(role='user', content=user)], max_tokens=max_tokens)
    if json_mode:
        kwargs['response_format'] = {'type': 'json_object'}
    if response_schema is not None:
        kwargs['response_format'] = {'type': 'json_schema', 'json_schema': {'name': 'juiz_v2_2', 'schema': response_schema}}
    if reasoning_effort:
        kwargs['reasoning_effort'] = reasoning_effort
        kwargs['extra_body'] = {'chat_template_kwargs': {'reasoning_effort': reasoning_effort}}
    else:
        kwargs['extra_body'] = {'chat_template_kwargs': {'enable_thinking': False}}
    if temperature is not None:
        kwargs['temperature'] = temperature
    if seed is not None:
        kwargs['seed'] = seed
    client = client or globals()['client']()
    tentativa = 0
    meta = {**_contexto.get()}
    meta.update({k:v for k,v in dict(estagio=estagio, slug=slug, bucket=bucket).items() if v is not None})
    if not meta.get('estagio') or not meta.get('slug'):
        raise ValueError('estagio e slug obrigatórios para telemetria Featherless')

    def chamar():
        nonlocal tentativa
        rid = sessao.reservar(reserva, p['concurrency_cost'])
        tentativa += 1
        t0 = time.monotonic()
        reg = dict(meta, provider='featherless', modelo=model, tentativa=tentativa, ts=agora_utc_iso(), max_tokens=max_tokens)
        custo = None
        try:
            resp = S._com_prazo_de_parede(
                lambda: S._featherless_sdk_create(client, kwargs),
                S.LLM_PRAZO_PAREDE_S, 'featherless', model)
            u = getattr(resp, 'usage', None)
            if u is None or u.prompt_tokens is None or u.completion_tokens is None:
                raise S.LLMRespostaComErro('Featherless sem usage: reserva retida')
            entrada, saida = int(u.prompt_tokens), int(u.completion_tokens)
            if entrada < 0 or saida < 0:
                raise S.LLMRespostaComErro('contadores negativos')
            efetivo = getattr(resp, 'model', None) or model
            if efetivo != model and efetivo not in FEATHERLESS_PRECOS:
                raise S.LLMRespostaComErro('modelo efetivo sem preço: reserva retida')
            cacheado = int(getattr(u, 'cached_tokens', None) or
                           getattr(getattr(u, 'prompt_tokens_details', None), 'cached_tokens', 0) or 0)
            custo = custo_nano(efetivo, entrada, saida, cacheado)
            # `completion_tokens` já inclui raciocínio: não somar duas vezes.
            detalhes = getattr(u, 'completion_tokens_details', None)
            reg.update(modelo_efetivo=efetivo, prompt_tokens=entrada, completion_tokens=saida,
                       reasoning_tokens=getattr(detalhes, 'reasoning_tokens', None),
                       uso=u.model_dump() if hasattr(u, 'model_dump') else dict(prompt_tokens=entrada, completion_tokens=saida),
                       custo_api_usd=getattr(u, 'cost', None))
            if getattr(u, 'cost', None) is not None:
                # Protege o teto mesmo se a tabela mudar durante a sessão.
                custo = max(custo, int((Decimal(str(u.cost))*NANO).to_integral_value(rounding=ROUND_CEILING)))
            return S._resposta_deepseek_valida(resp)
        except BaseException as e:
            reg['erro'] = type(e).__name__  # não serializar chave/corpo HTTP
            raise
        finally:
            reg['duracao_s'] = round(time.monotonic()-t0, 4)
            sessao.concluir(rid, reg, custo)
    return S._com_retentativa('featherless', model, chamar)


def json_resposta(system, user, model, *, max_tokens, estagio, unidade, client=None):
    partes = unidade.split('/')
    t0 = time.monotonic()
    resp = resposta(system, user, model, max_tokens=max_tokens, json_mode=True,
                    client=client, estagio=estagio, slug=partes[0],
                    bucket=partes[1] if len(partes)>2 else None)
    from .synthesize import uso
    return dict(texto=resp.choices[0].message.content, provider='featherless', modelo=model,
                modelo_efetivo=resp.model, uso=uso(resp, 'featherless'), fallback_conteudo=None,
                latencia_s=round(time.monotonic()-t0,2),
                custo_usd=custo_nano(resp.model, resp.usage.prompt_tokens, resp.usage.completion_tokens,
                                    int(getattr(resp.usage, 'cached_tokens', None) or getattr(getattr(resp.usage, 'prompt_tokens_details', None), 'cached_tokens', 0) or 0))/1e9)
