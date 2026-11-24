import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import etapa2_featherless as D
from espectro24 import featherless as F


def sessao(tmp_path, **kw):
    (tmp_path/'plano.json').write_text(json.dumps(dict(concurrency=100)))
    return F.Sessao(tmp_path,**kw)


def test_autorizacao_15_so_etapa2_com_prazo(tmp_path):
    with pytest.raises(ValueError): sessao(tmp_path,teto_usd=15)
    with pytest.raises(ValueError): sessao(tmp_path,teto_usd=15,etapa='2')
    with pytest.raises(ValueError): sessao(tmp_path,teto_usd=15,etapa='2',prazo_utc=D.PRAZO+1)
    s=sessao(tmp_path,teto_usd=15,etapa='2',prazo_utc=D.PRAZO)
    assert s.resumo()['teto_usd']==15
    with pytest.raises(ValueError): F.Sessao(tmp_path,teto_usd=15,etapa='2',prazo_utc=D.PRAZO-1)


def test_prazo_recusa_antes_rede_incluindo_margem(tmp_path,monkeypatch):
    s=sessao(tmp_path,teto_usd=15,etapa='2',prazo_utc=D.PRAZO)
    monkeypatch.setattr(F.time,'time',lambda:D.PRAZO-1)
    with pytest.raises(F.TetoExcedido): s.reservar(1,1)
    assert s.resumo()['chamadas']==0


def test_teto_atomicamente_reserva_pior_caso(tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    monkeypatch.setattr(F.time,'time',lambda:D.PRAZO-10000)
    s=sessao(tmp_path,teto_usd=15,etapa='2',prazo_utc=D.PRAZO)
    def reserva(_):
        try:return s.reservar(1_000_000_000,1)
        except F.TetoExcedido:return None
    with ThreadPoolExecutor(max_workers=20) as ex: rs=list(ex.map(reserva,range(25)))
    assert sum(x is not None for x in rs)==15
    assert s.resumo()['reservas_pendentes_usd']==15


def test_cache_retoma_sem_pagar_e_preserva_replicas(tmp_path,monkeypatch):
    calls=[]
    def resposta(*a,**kw):
        calls.append(kw)
        return NS(model=D.DS,choices=[NS(message=NS(content='{"n":'+str(len(calls))+'}'))])
    monkeypatch.setattr(F,'resposta',resposta)
    from espectro24 import synthesize as S
    monkeypatch.setattr(S,'uso',lambda *a:dict(prompt_tokens=1,completion_tokens=1))
    def executar():
        c=D.Chamador(tmp_path,'filme')
        return [c.chamar('s','u',D.DS,'condicoes',300)['texto'] for _ in range(3)]
    assert executar()==['{"n":1}','{"n":2}','{"n":3}']
    assert executar()==['{"n":1}','{"n":2}','{"n":3}']
    assert len(calls)==3


def test_modelo_efetivo_divergente_nao_e_cacheado(tmp_path,monkeypatch):
    monkeypatch.setattr(F,'resposta',lambda *a,**k:NS(model='outro'))
    with pytest.raises(AssertionError):D.Chamador(tmp_path,'filme').chamar('s','u',D.DS,'sintese',300)
    assert not list(tmp_path.rglob('*.json'))


def test_escopo_c22_destino_lacrado_e_novos_na_lista(tmp_path,monkeypatch):
    monkeypatch.setattr(D,'OUT',tmp_path)
    D.salvar(tmp_path/'manifesto.json',dict(c22_slugs=['protegido']))
    assert D.pasta('protegido')==tmp_path/'lacrado_c22/protegido'
    assert D.pasta('novo')==tmp_path/'aberto/novo'
    assert len(D.NOVOS)==50 and D.NOVOS[0][0]=='The Shawshank Redemption'
    assert len({s for _,_,s in D.NOVOS})==50


def test_validacao_mesma_funcao_da_auditoria():
    # A auditoria reexporta o validador puro; importar o harness instala guarda global.
    from espectro24.validacao_publicado import validar_publicado
    b=dict(n_validas=40,temas=[],observacao_geral='')
    r=validar_publicado(b)
    assert r['passa_publicado'] is False
    assert r['publicado']['campos_nao_vazios'] is False


def test_callback_condicoes_entrega_texto_para_parser_da_producao(tmp_path,monkeypatch):
    c=D.Chamador(tmp_path,'filme')
    monkeypatch.setattr(c,'chamar',lambda *a:dict(texto='{"vale_a_pena":[]}',uso={}))
    texto,uso,dt=c.condicoes(D.DS)('system','user')
    assert isinstance(texto,str) and json.loads(texto)==dict(vale_a_pena=[])
    assert uso=={} and dt>=0


def test_juiz_para_no_segundo_sim_e_retoma_falha():
    import juiz_etapa2_windows as W
    ps=[dict(id_bullet='b',id_par=str(i),rank=i,texto='a fotografia da imagem',julgavel_estimado=True) for i in range(1,6)]
    regs={str(i):dict(ok=True,config_sha256=W.HASH,apoio='sim',trecho='fotografia da imagem') for i in (1,2)}
    # O schema do v2.2 usa campos específicos; a regra de apoio pertence ao juiz congelado.
    from unittest.mock import patch
    with patch.object(W.J,'motivo_da_versao',return_value=None):
        e=W.estados(ps,regs)['b'];assert e['estado']=='apoio_2' and e['julgados']==2 and e['proximo'] is None
        regs['2']['ok']=False
        e=W.estados(ps,regs)['b'];assert e['estado']=='pendente' and e['proximo']['id_par']=='2'


def test_revalidacao_condicoes_reconstitui_lado_e_preserva_flags(monkeypatch):
    from espectro24 import condicoes as C
    recebidos=[]
    monkeypatch.setattr(C,'indexar',lambda out:{})
    def validar(c,idx):
        recebidos.append(c)
        return ['falha_real'] if c['texto']=='invalida' else []
    monkeypatch.setattr(C,'validar',validar)
    monkeypatch.setattr(C,'inconsistencias_de_recusa',lambda b,i:[])
    b=dict(vale_a_pena=[dict(texto='valida')],talvez_evite=[dict(texto='invalida')],descartadas=[{}])
    r=D.validar_condicoes({},b)
    assert r['aprovadas']==2 and r['flags']==1 and r['descartadas']==1
    assert [c['lado'] for c in recebidos]==['vale_a_pena','talvez_evite']
    assert all('lado' not in c for lado in C.LADOS for c in b[lado])


def test_filme_so_e_gerado_apos_tres_condicoes_e_resume_nao_repete(tmp_path,monkeypatch):
    from espectro24 import pipeline as P,eixos as E,condicoes as C
    from espectro24 import prosa_local as L,render as R
    monkeypatch.setattr(D,'ROOT',tmp_path)
    monkeypatch.setattr(D,'OUT',tmp_path/'exec')
    D.salvar(D.OUT/'manifesto.json',dict(c22_slugs=[]))
    p=D.pasta('filme');p.mkdir(parents=True)
    D.salvar(p/'estado.json',dict(slug='filme',estado='pendente',origem='novo',c22=False,grupo='coberto'))
    D.salvar(D.OUT/'bruto/filme/meta.json',dict(histograma_bruto={'4.0':100}))
    am={b:[] for b in ('negativas','medianas','positivas')}
    monkeypatch.setattr(P,'amostra_do_bruto',lambda *a,**k:am)
    D.salvar(tmp_path/'resultado/votacao-3/consenso_verificado.jsonl',{})
    monkeypatch.setattr(E,'carregar_classificacao',lambda *a,**k:{'filme':am})
    monkeypatch.setattr(E,'checar_amostra_classificada',lambda *a:None)
    monkeypatch.setattr(L,'_buckets_do_bruto',lambda *a:[])
    monkeypatch.setattr(R,'build_output',lambda *a,**k:dict(slug='filme',buckets=[],coleta={}))
    monkeypatch.setattr(P,'montar_eixos',lambda *a,**k:{'linhas':[]})
    chamadas=[]
    def gerar(out,**kw):
        chamadas.append(kw['model'])
        if len(chamadas)==3:raise F.TetoExcedido('parada')
        return dict(vale_a_pena=[],talvez_evite=[])
    monkeypatch.setattr(C,'gerar',gerar)
    with pytest.raises(F.TetoExcedido):D.gerar_filme('filme')
    assert D.ler(p/'estado.json')['estado']!='gerado'
    assert len(list((p/'condicoes').rglob('condicoes.json')))==2
    D.gerar_filme('filme')
    assert D.ler(p/'estado.json')['estado']=='gerado'
    assert chamadas==D.MODELOS+[D.MODELOS[2]]


def test_vigia_so_encerra_processo_pago_registrado_e_confirmado(tmp_path,monkeypatch):
    import signal
    monkeypatch.setattr(D,'OUT',tmp_path)
    monkeypatch.setattr(D,'fim',lambda:True)
    D.salvar(tmp_path/'aberto/filme/processo_pago.json',dict(pid=123,slug='filme'))
    D.salvar(tmp_path/'aberto/outro/processo_pago.json',dict(pid=456,slug='outro'))
    monkeypatch.setattr(D.subprocess,'run',lambda args,**kw:NS(stdout='python scripts/etapa2_featherless.py gerar --slug filme' if args[2]=='123' else 'outro processo'))
    kills=[];monkeypatch.setattr(D.os,'kill',lambda pid,sig:kills.append((pid,sig)))
    D.vigiar()
    assert kills==[(123,signal.SIGKILL)]
    assert (tmp_path/'parada_rigida.json').exists()


def test_pacote_juiz_vazio_registra_zero_sem_chamar_ollama(tmp_path,monkeypatch):
    import juiz_etapa2_windows as W
    D.salvar(tmp_path/'preparado.json',dict(config_sha256=W.HASH,pares=0))
    (tmp_path/W.C.ARQ_ENTRADA).write_text('')
    monkeypatch.setattr(W.J,'_exigir_modelo',lambda:pytest.fail('zero pares não chama modelo'))
    r=W.executar(tmp_path)
    assert sum(r.values())==0
    assert D.ler(tmp_path/'juiz_v2/estado.json')['sem_pares_julgaveis'] is True


def test_pacote_juiz_nao_leva_bruto_cache_bullets_ou_segredos(tmp_path,monkeypatch):
    import zipfile
    monkeypatch.setattr(D,'ROOT',tmp_path);monkeypatch.setattr(D,'OUT',tmp_path/'exec')
    for d in ['scripts','src/espectro24']: (tmp_path/d).mkdir(parents=True)
    (tmp_path/'scripts/juiz.py').write_text('codigo')
    (tmp_path/'pyproject.toml').write_text('')
    D.OUT.mkdir();(D.OUT/'rodar_juiz_windows.ps1').write_text('')
    (tmp_path/'.env').write_text('segredo')
    d=D.OUT/'lacrado_c22/filme/juiz';D.salvar(d/'preparado.json',dict(pares=0))
    (d/'juiz_entrada.jsonl').write_text('')
    D.salvar(d.parent/'bullets.json',dict(conteudo='nao_empacotar'))
    D.salvar(D.OUT/'bruto/filme/meta.json',{})
    D.empacotar_juiz()
    with zipfile.ZipFile(D.OUT/'lacrado_c22/juiz_windows.zip') as z:
        names=z.namelist()
        assert any(n.endswith('/juiz/juiz_entrada.jsonl') for n in names)
        assert not any(n.endswith('.env') or '/bruto/' in n or '/cache/' in n or n.endswith('bullets.json') for n in names)
    assert D.ler(d/'preparado.json')['entrada_sha256']==hashlib.sha256(b'').hexdigest()


def test_projecao_primeiros_tres_inclui_tempo_de_coleta_que_falhou():
    coleta=[dict(prioridade=1,estado='coletado',duracao_s=400),dict(prioridade=2,estado='coletado',duracao_s=350),dict(prioridade=3,estado='identidade_ou_coleta_falhou',duracao_s=450)]
    r=D.projetar_coleta(coleta,47,agora=D.PRAZO-3600)
    assert r['n_medido']==3 and r['media_s']==400
    assert r['coletas_concluidas_na_medicao']==2 and r['falhas_na_medicao']==1
    assert r['filmes_adicionais_ate_parada']==9
