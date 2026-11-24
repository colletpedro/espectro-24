import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace as NS
from pathlib import Path
import sys

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from espectro24 import featherless as F, synthesize as S

MODEL='deepseek-ai/DeepSeek-V4.1-Flash-1017'

@pytest.fixture(autouse=True)
def isolar_dotenv(monkeypatch):
    # Os harnesses carregam o .env real; os testes usam clientes falsos.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)


@pytest.fixture
def sessao(tmp_path):
    (tmp_path/'plano.json').write_text(json.dumps({'concurrency':100,'max_context_length':None}))
    return F.Sessao(tmp_path)


def fake_client(fn):
    return NS(chat=NS(completions=NS(create=fn)))


def resposta(model=MODEL, tokens=20):
    return NS(model=model, usage=NS(prompt_tokens=100,completion_tokens=tokens,
              completion_tokens_details=NS(reasoning_tokens=5)),
              choices=[NS(message=NS(content='{}'))])


def chamar(sessao, fn, **kw):
    return F.resposta('system JSON','user',MODEL, max_tokens=300,json_mode=True,
                      sessao=sessao,client=fake_client(fn), estagio='teste',slug='filme',bucket='positivas',**kw)


def test_provider_transporte_e_registro(sessao):
    calls=[]
    def create(**kw):
        calls.append(kw)
        return resposta()
    chamar(sessao,create)
    assert calls[0]['extra_body']=={'chat_template_kwargs':{'enable_thinking':False}}
    assert calls[0]['response_format']=={'type':'json_object'}
    r=json.loads((sessao.pasta/'uso.jsonl').read_text())
    assert (r['estagio'],r['slug'],r['bucket'],r['modelo_efetivo'],r['reasoning_tokens'],r['tentativa'])==('teste','filme','positivas',MODEL,5,1)
    assert r['custo_usd']==pytest.approx((100*.225+20*.9)/1e6)
    assert sessao.resumo()['reservas_pendentes_usd']==0


def test_reserva_recusa_antes_da_rede(sessao):
    sessao.reservar(2_999_999_999,1)
    with pytest.raises(F.TetoExcedido):
        chamar(sessao,lambda **kw: pytest.fail('não pode chamar'))


def test_teto_atomico_entre_threads_e_instancias(sessao):
    def reservar(_):
        outra=F.Sessao(sessao.pasta)
        try:
            return outra.reservar(1_000_000_000,1)
        except F.TetoExcedido:
            return None
    with ThreadPoolExecutor(max_workers=10) as pool:
        out=list(pool.map(reservar,range(15)))
    assert sum(x is not None for x in out)==3
    assert sessao.resumo()['reservas_pendentes_usd']==3
    with pytest.raises(ValueError,match='imutável'):
        F.Sessao(sessao.pasta,teto_usd='2')


def test_uso_ausente_conserva_reserva(sessao):
    with pytest.raises(S.LLMRespostaComErro):
        chamar(sessao,lambda **kw:NS(usage=None))
    assert sessao.resumo()['custo_usd']==0
    assert sessao.resumo()['reservas_pendentes_usd']>0


def test_transporte_retenta_e_contabiliza_cada_tentativa(sessao,monkeypatch):
    import openai
    import httpx
    monkeypatch.setattr(S.time,'sleep',lambda _:None)
    n=[0]
    def create(**kw):
        n[0]+=1
        if n[0]==1:
            raise openai.APIConnectionError(request=httpx.Request('POST','https://example.test'))
        return resposta()
    chamar(sessao,create)
    regs=[json.loads(l) for l in (sessao.pasta/'uso.jsonl').read_text().splitlines()]
    assert [r['tentativa'] for r in regs]==[1,2]
    assert sessao.resumo()['reservas_pendentes_usd']>0  # chamada ambígua pode ter sido cobrada


def test_4xx_nao_retenta(sessao):
    import openai,httpx
    n=[0]
    def create(**kw):
        n[0]+=1
        raise openai.BadRequestError('parâmetro',response=httpx.Response(400,request=httpx.Request('POST','https://example.test')),body={})
    with pytest.raises(openai.BadRequestError): chamar(sessao,create)
    assert n[0]==1


def test_limite_unidades_respeita_plano(sessao):
    with pytest.raises(ValueError): F.Sessao(sessao.pasta,unidades=101)
    with pytest.raises(ValueError): sessao.reservar(1,101)
    with pytest.raises(ValueError): F.Sessao(sessao.pasta,teto_usd='3.01')


def test_parametros_juiz(sessao):
    calls=[]
    chamar(sessao,lambda **kw:(calls.append(kw) or resposta()),reasoning_effort='low',seed=20261019,temperature=.8)
    assert calls[0]['reasoning_effort']=='low'
    assert calls[0]['seed']==20261019
    assert calls[0]['temperature']==.8


def test_selecao_resposta_e_sem_fallback(monkeypatch):
    monkeypatch.setattr(F,'json_resposta',lambda *a,**kw:kw)
    out=S.resposta_classificacao('s','u',MODEL,max_tokens=300,unidade='slug/b/id/passe1',provider='featherless')
    assert out['estagio']=='classificacao'
    assert out['unidade']=='slug/b/id/passe1'


def test_harnesses_encaminham_modelo_e_provider(tmp_path,monkeypatch):
    import votacao_3 as v3
    import verificador_impacto as vi
    calls=[]
    review=dict(id='id',slug='slug',perfil='perfil',bucket='positivas',nivel=4,n_chars=10,texto='review teste')
    monkeypatch.setattr(v3,'pendentes_do_passe',lambda *a,**kw:('tax',0,[review]))
    monkeypatch.setattr(v3,'ARQ_PASSE',{1:tmp_path/'passe.jsonl'})
    monkeypatch.setattr(v3,'deepseek_client',lambda:pytest.fail('cliente nativo'))
    def fake(*a,**kw):
        calls.append((a,kw))
        return dict(texto='{"eixos":["atuacao"],"temas_livres":[]}',uso={},provider='featherless',modelo=MODEL,latencia_s=0,fallback_conteudo=None,custo_usd=.01)
    monkeypatch.setattr(v3,'resposta_classificacao',fake)
    v3.classificar_passe(1,provider='featherless',modelo=MODEL)
    monkeypatch.setattr(vi,'deepseek_client',lambda:pytest.fail('cliente nativo'))
    def verificar(*a,**kw):
        calls.append((a,kw));return dict(texto='{"confirma":true,"frase":"emociona","alvo":"espectador"}',uso={},provider='featherless',modelo=MODEL,latencia_s=0,fallback_conteudo=None,custo_usd=.01)
    monkeypatch.setattr(vi,'resposta_json_com_fallback',verificar)
    vi.rodar_passe(vi.VARIANTE_PRODUCAO,1,[review],arq=tmp_path/'verif.jsonl',provider='featherless',modelo=MODEL)
    assert len(calls)==2
    assert all(a[2]==MODEL and kw['provider']=='featherless' for a,kw in calls)


def test_c22_nao_admite_override():
    import votacao_3 as v3
    import verificador_impacto as vi
    import lote_em_blocos as lb
    for fn in [lambda:v3.classificar_passe(1,excecao=True,provider='featherless'),lambda:vi.rodar_passe('x',1,[],excecao=True,provider='featherless'),lambda:lb.processar_bloco([],excecao=True,provider='featherless')]:
        with pytest.raises(v3.C22.ForaDaExcecao):fn()


def test_publicador_usa_so_estruturado(monkeypatch):
    import publicar_catalogo as P
    calls=[]
    monkeypatch.setattr(P.subprocess,'run',lambda argv,**kw:(calls.append(argv) or NS(returncode=1,stdout='',stderr='')))
    P.publicar_um('slug')
    assert calls[0][calls[0].index('--tom')+1]=='estruturado'


def test_gate_a_estados_iguais_a_implementacao_congelada():
    import gates_featherless as G
    import avaliar_c1_c4 as A
    entrada=[];regs={}
    for b in range(3):
        for rank in range(1,6):
            pid=f"b{b}-p{rank}"
            entrada.append(dict(id_par=pid,id_bullet=f"b{b}",rank=rank,
                                slug="filme",bucket="positivas",texto="The music adds a great atmosphere here.",
                                julgavel_estimado=not (b==2 and rank==1)))
            if b!=2 or rank<3:
                regs[pid]=dict(ok=True,config_sha256=G.HASH_JUIZ,
                               trecho="The music adds a great atmosphere here.",
                               apoia_ideia_principal=(rank%2==0 or b==0),evidencia_clara=True)
    assert G.estados_juiz(entrada,regs)==A.estados(entrada,regs)


def test_metadados_sintese_e_rotulagem_sem_contexto_externo(monkeypatch):
    from test_synthesize import _bucket_com_reviews
    from espectro24 import rotulagem as R
    vistos=[]
    def sdk(system,user,model,**kw):
        vistos.append(F.metadados())
        text='{"temas":[],"observacao_geral":"As reviews positivas apontam aspectos."}' if F.metadados()['estagio']=='sintese' else '{"rotulos":[]}'
        return NS(choices=[NS(message=NS(content=text))])
    monkeypatch.setenv('FEATHERLESS_API_KEY','fake')
    monkeypatch.setattr(F,'resposta',sdk)
    S.synthesize_bucket(_bucket_com_reviews(),provider='featherless',slug='filme')
    R.rotular_output({'slug':'filme','buckets':[{'bucket':'positivas','n_validas':40,'estado_piso':'completa','temas':[{'tema':'Atuação','exemplo_parafraseado':'As reviews elogiam o elenco.'}]}]},provider='featherless')
    assert vistos
    assert {r['estagio'] for r in vistos}=={'sintese','rotulagem'}
    assert all(r['slug']=='filme' and r['bucket'] for r in vistos)
    assert F.metadados()=={}


def test_custo_cache_confere_com_fatura_sem_mudar_reserva(sessao):
    # Chamada REAL medida: 1530 tokens cacheados + 56 de saída.
    assert F.custo_nano(MODEL,1530,56,1530)==59580
    assert F.custo_nano('Qwen/Qwen3.8-27B',4030,234,4030)==1306500
    assert F.custo_nano('moonshotai/Kimi-K3.1-Pro',5166,67,3712)==4320400
    before=F.custo_nano(MODEL,262144,300)
    def create(**kw):
        r=resposta(tokens=56);r.usage.prompt_tokens=1530;r.usage.cached_tokens=1530
        r.usage.cost=.00005958
        return r
    chamar(sessao,create)
    assert sessao.resumo()['custo_usd']==.00005958
    with sessao.db() as db:
        reservado,=db.execute('select reservado from chamadas').fetchone()
    assert reservado==before
    with pytest.raises(ValueError):F.custo_nano(MODEL,10,10,11)
