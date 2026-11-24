import json
from pathlib import Path
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
import pytest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
from espectro24 import featherless as F
from espectro24 import sessao_featherless as G
from lista3_catalogo import lista


def criar(p,etapa='1'):
    p.mkdir();(p/'plano.json').write_text(json.dumps({'concurrency':100}))
    return F.Sessao(p,teto_usd='15' if etapa=='2' else '3',etapa=etapa,prazo_utc=G.PRAZO_UTC if etapa=='2' else None)


def test_orcamento_global_importa_etapa1_sem_zerar_nem_duplicar(tmp_path,monkeypatch):
    monkeypatch.setattr(F.time,'time',lambda:G.PRAZO_UTC-10000)
    e1=criar(tmp_path/'e1');rid=e1.reservar(1_000_000_000,1);e1.concluir(rid,dict(slug='teste'),1_000_000_000)
    e2=criar(tmp_path/'e2','2')
    G.ativar(e2.pasta/'caixa.sqlite3',e1.pasta/'caixa.sqlite3')
    e2=F.Sessao(e2.pasta,teto_usd='15',etapa='2',prazo_utc=G.PRAZO_UTC)
    assert e2.resumo()['teto_usd']==19 and e2.resumo()['custo_usd']==1
    e2.reservar(18_000_000_000,1)
    with pytest.raises(F.TetoExcedido):e2.reservar(1,1)
    # A migração idempotente também funciona quando já não há orçamento livre.
    G.ativar(e2.pasta/'caixa.sqlite3',e1.pasta/'caixa.sqlite3')
    assert e2.resumo()['custo_usd']==1 and e2.resumo()['reservas_pendentes_usd']==18
    # Uma versão anterior à migração continua vendo sua config legada intacta.
    with e2.db() as db: assert db.execute('select teto from config').fetchone()[0]==15_000_000_000


def test_trigger_impede_cliente_legado_de_ignorar_teto_global(tmp_path,monkeypatch):
    monkeypatch.setattr(F.time,'time',lambda:G.PRAZO_UTC-10000)
    e1=criar(tmp_path/'e1');rid=e1.reservar(1,1);e1.concluir(rid,{},1)
    e2=criar(tmp_path/'e2','2');G.ativar(e2.pasta/'caixa.sqlite3',e1.pasta/'caixa.sqlite3')
    def reservar(i):
        try:
            with e2.db() as db: db.execute('insert into chamadas values(?,?,NULL,1,\'ativa\',NULL)',(str(i),1_000_000_000))
            return True
        except sqlite3.IntegrityError:return False
    with ThreadPoolExecutor(max_workers=20) as ex:rs=list(ex.map(reservar,range(25)))
    assert sum(rs)==18
    assert e2.resumo()['custo_usd']+e2.resumo()['reservas_pendentes_usd']<=19


def test_lista3_preserva_ordem_anos_e_idiomas_de_desambiguacao():
    rs=lista();assert len(rs)==144 and rs[0]['titulo']=='High and Low' and rs[-1]['titulo']=='Miracle in Cell No. 7'
    idx={r['titulo']:r for r in rs}
    assert idx['Drishyam']['ano']==2015 and idx['Drishyam']['requisitos']==dict(idioma='hi',pais='IN')
    assert idx['The Hunt']['requisitos']==dict(idioma='da',pais='DK')
    assert idx['Miracle in Cell No. 7']['requisitos']==dict(idioma='tr',pais='TR')


def test_identidade_exige_ano_da_lista_e_idioma_exato():
    import lista3_featherless as L
    item=dict(titulo='Drishyam',ano=2015,requisitos=dict(idioma='hi',pais='IN'))
    ident=dict(letterboxd={'ano':2015},tmdb_ano=2015,idioma_original='ml',paises=['IN'])
    with pytest.raises(ValueError,match='idioma'):L.requisitos_identidade(item,ident)
    ident['idioma_original']='hi';L.requisitos_identidade(item,ident)
    ident.update(letterboxd={'ano':2014},tmdb_ano=2014)
    with pytest.raises(ValueError,match='ano_da_lista'):L.requisitos_identidade(item,ident)
    ident.update(letterboxd={'ano':2015},tmdb_ano=2014);L.requisitos_identidade(item,ident)


def test_id_tmdb_divergente_coloca_bruto_em_quarentena(tmp_path,monkeypatch):
    import lista3_featherless as L
    from espectro24 import ficha
    monkeypatch.setattr(L,'OUT',tmp_path/'lista3')
    bruto=tmp_path/'bruto';(bruto/'filme').mkdir(parents=True);(bruto/'filme/reviews.jsonl').write_text('material')
    monkeypatch.setattr(ficha,'extrair_identidade_letterboxd',lambda html,slug:dict(tmdb_id_letterboxd=999))
    from types import SimpleNamespace as NS
    assert L.conferir_pos_coleta(NS(get=lambda *a:'pagina'),'filme',dict(tmdb_id=123),bruto) is False
    assert not (bruto/'filme').exists() and (L.OUT/'quarentena/filme/reviews.jsonl').exists()


def test_coleta_lista3_apos_21h_nao_inicia_llm(tmp_path,monkeypatch):
    from types import SimpleNamespace as NS
    import lista3_featherless as L
    from espectro24 import pipeline as P,fetcher
    monkeypatch.setattr(L,'BASE',tmp_path/'base');monkeypatch.setattr(L,'OUT',L.BASE/'lista3')
    monkeypatch.setattr(L.D,'OUT',L.BASE)
    L.D.salvar(L.BASE/'manifesto.json',dict(c22_slugs=[],candidatos=[],novos=[]))
    L.D.salvar(L.BASE/'coleta.json',[dict(prioridade=i,estado='coletado') for i in range(50)])
    item=dict(prioridade=1,titulo='Filme',ano=2000,sugestao='filme')
    L.D.salvar(L.OUT/'manifesto.json',dict(coletor_legado=0,c22_slugs=[],lista=[item]))
    monkeypatch.setattr(L,'vivo',lambda *a:False);monkeypatch.setattr(L.D,'fim',lambda:True)
    monkeypatch.setattr(L,'resolver',lambda *a:('filme',dict(tmdb_id=1,ficha={})))
    monkeypatch.setattr(L,'proibidos',lambda:set());monkeypatch.setattr(L,'conferir_pos_coleta',lambda *a:True)
    monkeypatch.setattr(fetcher,'Fetcher',lambda path,**kw:NS(cache_dir=path))
    def collect(f,s,**kw):L.D.salvar(kw['dados_dir']/s/'meta.json',{})
    monkeypatch.setattr(P,'collect_all_levels',collect);monkeypatch.setattr(P,'amostra_do_bruto',lambda *a,**k:{'negativas':[],'medianas':[],'positivas':[]})
    monkeypatch.setattr(L.F,'resposta',lambda *a,**k:pytest.fail('coleta não pode chamar LLM'))
    L.coletar_lista3()
    assert L.D.ler(L.D.pasta('filme')/'estado.json')['estado']=='coletado_nao_gerado'
    assert L.D.ler(L.OUT/'coleta.json')[0]['estado']=='coletado'


def test_geracao_base_termina_sem_kimi_e_sem_alterar_validadores(tmp_path,monkeypatch):
    from espectro24 import pipeline as P,eixos as E,condicoes as C,prosa_local as B,render as R
    import etapa2_featherless as D
    monkeypatch.setattr(D,'ROOT',tmp_path);monkeypatch.setattr(D,'OUT',tmp_path/'exec')
    D.salvar(D.OUT/'manifesto.json',dict(c22_slugs=[]));D.salvar(D.OUT/'sessao_politica.json',dict(condicoes_obrigatorias=[D.DS,'Qwen/Qwen3.8-27B']))
    p=D.pasta('filme');D.salvar(p/'estado.json',dict(slug='filme',estado='pendente',origem='lista3',grupo='coberto',c22=False,bruto_raiz=str(tmp_path/'bruto')))
    D.salvar(tmp_path/'bruto/filme/meta.json',dict(histograma_bruto={'4.0':100}))
    D.salvar(tmp_path/'resultado/votacao-3/consenso_verificado.jsonl',{})
    am={b:[] for b in ('negativas','medianas','positivas')}
    monkeypatch.setattr(P,'amostra_do_bruto',lambda *a,**k:am);monkeypatch.setattr(E,'carregar_classificacao',lambda *a,**k:{'filme':am})
    monkeypatch.setattr(E,'checar_amostra_classificada',lambda *a:None);monkeypatch.setattr(B,'_buckets_do_bruto',lambda *a:[])
    monkeypatch.setattr(R,'build_output',lambda *a,**k:dict(slug='filme',buckets=[],coleta={}));monkeypatch.setattr(P,'montar_eixos',lambda *a,**k:{'linhas':[]})
    chamados=[]
    def gerar(out,**kw):chamados.append(kw['model']);return dict(vale_a_pena=[],talvez_evite=[])
    monkeypatch.setattr(C,'gerar',gerar);D.gerar_filme('filme')
    es=D.ler(p/'estado.json');assert es['estado']=='gerado' and es['sem_kimi']
    assert chamados==[D.DS,'Qwen/Qwen3.8-27B'] and len(list((p/'condicoes').glob('*/condicoes.json')))==2


def test_fila_sempre_frente1_frente2_lista3_na_ordem_original(tmp_path,monkeypatch):
    import lista3_featherless as L
    monkeypatch.setattr(L,'BASE',tmp_path/'base');monkeypatch.setattr(L,'OUT',L.BASE/'lista3')
    L.D.salvar(L.BASE/'manifesto.json',dict(candidatos=[dict(slug='b'),dict(slug='a')],novos=[dict(prioridade=1),dict(prioridade=2)]))
    L.D.salvar(L.OUT/'manifesto.json',dict(lista=[dict(prioridade=1),dict(prioridade=2)]))
    L.D.salvar(L.BASE/'coleta.json',[dict(prioridade=2,slug='n2',estado='coletado'),dict(prioridade=1,slug='n1',estado='coletado')])
    L.D.salvar(L.OUT/'coleta.json',[dict(prioridade=2,slug='l2',estado='coletado'),dict(prioridade=1,slug='l1',estado='coletado')])
    assert L.fila_ordenada()==['b','a','n1','n2','l1','l2']


def test_kimi_respeita_projecao_saldo_e_ordem(tmp_path,monkeypatch):
    from types import SimpleNamespace as NS
    import lista3_featherless as L
    monkeypatch.setattr(L,'OUT',tmp_path/'lista3');monkeypatch.setattr(L.D,'pasta',lambda s:tmp_path/s)
    for s in ['primeiro','segundo']:L.D.salvar(tmp_path/s/'estado.json',dict(estado='gerado'))
    monkeypatch.setattr(L,'fila_ordenada',lambda:['primeiro','segundo'])
    dbfile=tmp_path/'caixa.sqlite3'
    with sqlite3.connect(dbfile) as db:
        db.execute('create table chamadas(registro text)');db.execute('insert into chamadas values(?)',(json.dumps(dict(estagio='condicoes',modelo=L.KIMI,slug='medido',custo_usd=.1)),))
    monkeypatch.setattr(L.F,'sessao_ambiente',lambda:NS(db=lambda:sqlite3.connect(dbfile),resumo=lambda:dict(custo_usd=18.7,reservas_pendentes_usd=.1)))
    assert L.projetar_kimi()==['primeiro']
    assert L.D.ler(L.OUT/'plano_kimi.json')['quantidade_projetada']==1


def test_bloqueio_herdado_nao_libera_fase_kimi(tmp_path,monkeypatch):
    from types import SimpleNamespace as NS
    import lista3_featherless as L
    monkeypatch.setattr(L,'BASE',tmp_path/'base');monkeypatch.setattr(L,'OUT',L.BASE/'lista3')
    L.D.salvar(L.BASE/'manifesto.json',dict(novos=[dict(prioridade=1)]))
    L.D.salvar(L.OUT/'manifesto.json',dict(supervisor_legado=0,lista=[dict(prioridade=1)]))
    L.D.salvar(L.BASE/'coleta.json',[dict(prioridade=1,estado='coleta_bloqueada')])
    L.D.salvar(L.BASE/'coleta_concluida.json',dict(concluida=True))
    L.D.salvar(L.OUT/'coleta_concluida.json',dict(concluida=True,bloqueio_herdado=True))
    monkeypatch.setattr(L,'vivo',lambda *a:False);monkeypatch.setattr(L.D,'fim',lambda:False)
    monkeypatch.setattr(L,'fila_ordenada',lambda:[]);monkeypatch.setattr(L,'diagnosticar_verificadores',lambda:[])
    monkeypatch.setattr(L.F,'sessao_ambiente',lambda:NS(resumo=lambda:dict(custo_usd=1,reservas_pendentes_usd=0)))
    monkeypatch.setattr(L.D,'conta',lambda *a:dict(balance_usd='10'))
    monkeypatch.setattr(L,'projetar_kimi',lambda:pytest.fail('bloqueio não libera Kimi'))
    L.fila_llm()
    assert not L.situacao_coletas()['coletas_completas']
    assert L.D.ler(L.OUT/'llm_concluido.json')['motivo']=='bloqueio_letterboxd'


def test_marcador_concluido_sem_tentar_lista_inteira_nao_libera_kimi(tmp_path,monkeypatch):
    import lista3_featherless as L
    monkeypatch.setattr(L,'BASE',tmp_path/'base');monkeypatch.setattr(L,'OUT',L.BASE/'lista3')
    L.D.salvar(L.BASE/'manifesto.json',dict(novos=[dict(prioridade=1)]))
    L.D.salvar(L.OUT/'manifesto.json',dict(lista=[dict(prioridade=1),dict(prioridade=2)]))
    L.D.salvar(L.BASE/'coleta.json',[dict(prioridade=1,estado='coletado')])
    L.D.salvar(L.OUT/'coleta.json',[dict(prioridade=1,estado='coletado')])
    for f in [L.BASE/'coleta_concluida.json',L.OUT/'coleta_concluida.json']:L.D.salvar(f,dict(concluida=True))
    assert not L.situacao_coletas()['coletas_completas']
    L.D.salvar(L.OUT/'coleta.json',[dict(prioridade=1,estado='coletado'),dict(prioridade=2,estado='pulado_duplicidade')])
    assert L.situacao_coletas()['coletas_completas']
