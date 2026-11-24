import sys,json
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerar_candidatos_sintese_featherless as G


@pytest.mark.skipif(not (G.FT/'split.json').exists(),
                    reason='precisa da árvore irmã espectro-24-finetune (branch finetune)')
def test_exclusoes_incluem_c22_validacao_teste_e_avaliacoes_auxiliares():
 motivos,fontes=G.exclusoes();sp=G.D.ler(G.FT/'split.json');c22={x['slug'] for x in G.D.ler(G.FT/'c22/escopo.json')['incluidos']}
 assert len(c22)==35
 assert c22<=set(motivos)
 assert set(sp['teste'])|set(sp['validacao'])<=set(motivos)
 for nome in ['especificidade/mapa/validacao_v2_mapa.json','guarda/fluencia_mapa.json']:
  assert {r['slug'] for r in G.D.ler(G.FT/nome)['itens']}<=set(motivos)
 assert all(G.D.sha(p)==h for p,h in fontes.items())


def test_manifesto_recusa_slug_excluido_e_escopo_alterado(tmp_path,monkeypatch):
 monkeypatch.setattr(G,'OUT',tmp_path);fonte=tmp_path/'split.json';fonte.write_text('{}')
 m=dict(prazo_utc=G.PRAZO,modelo=G.D.DS,incorporado_ao_treino=False,slugs=['permitido'],excluidos=['protegido'],fontes_exclusao_sha256={str(fonte):G.D.sha(fonte)})
 G.D.salvar(tmp_path/'manifesto.json',m);assert G.carregar_manifesto()==m
 m['slugs'].append('protegido');G.D.salvar(tmp_path/'manifesto.json',m)
 with pytest.raises(AssertionError):G.carregar_manifesto()
 m['slugs']=['permitido'];G.D.salvar(tmp_path/'manifesto.json',m);fonte.write_text('{"novo":true}')
 with pytest.raises(AssertionError):G.carregar_manifesto()


def test_filme_completo_nao_chama_sintese(tmp_path,monkeypatch):
 monkeypatch.setattr(G,'OUT',tmp_path);monkeypatch.setattr(G,'carregar_manifesto',lambda:dict(slugs=['a'],excluidos=[]))
 G.D.salvar(tmp_path/'filmes/a/estado.json',dict(completo=True))
 from espectro24 import synthesize as S
 monkeypatch.setattr(S,'synthesize_bucket',lambda *a,**kw:pytest.fail('não pagar novamente'))
 G.gerar_filme('a')


def test_prazo_nao_inicia_sintese(tmp_path,monkeypatch):
 monkeypatch.setattr(G,'OUT',tmp_path);monkeypatch.setattr(G,'carregar_manifesto',lambda:dict(slugs=['a'],excluidos=[]))
 monkeypatch.setattr(G.time,'time',lambda:G.PRAZO-94)
 from espectro24 import synthesize as S
 monkeypatch.setattr(S,'synthesize_bucket',lambda *a,**kw:pytest.fail('fora da janela'))
 G.gerar_filme('a');assert not (tmp_path/'filmes/a/estado.json').exists()


def test_slug_protegido_nunca_alcanca_sintese(tmp_path,monkeypatch):
 monkeypatch.setattr(G,'OUT',tmp_path);monkeypatch.setattr(G,'carregar_manifesto',lambda:dict(slugs=[],excluidos=['protegido']))
 from espectro24 import synthesize as S
 monkeypatch.setattr(S,'synthesize_bucket',lambda *a,**kw:pytest.fail('não enviar protegido'))
 with pytest.raises(AssertionError):G.gerar_filme('protegido')

@pytest.mark.parametrize('mencoes,passa',[(3,True),(1,False)])
def test_recuperacao_real_do_cache_apos_prazo_preserva_validacao(tmp_path,monkeypatch,mencoes,passa):
 from espectro24 import synthesize as S,prosa_local as P
 from espectro24.config import LLM_MAX_TOKENS
 from espectro24.models import BucketResult,LevelResult,Review
 import hashlib
 monkeypatch.setattr(G,'OUT',tmp_path)
 monkeypatch.setattr(G,'carregar_manifesto',lambda:dict(slugs=['a'],excluidos=[]))
 monkeypatch.setattr(G.time,'time',lambda:G.PRAZO+10000)
 monkeypatch.setattr(G.F,'resposta',lambda *a,**kw:pytest.fail('nenhuma chamada paga'))
 buckets=[]
 for nome in ['negativas','medianas','positivas']:
  lvl=LevelResult(4.,150,1,0,0,0,0,0)
  lvl.validas=[Review(viewing_id=f'v{i}',rating=4.,text='O filme tem um ritmo envolvente.',truncated=False,full_text_url=None,spoiler=False,full_text='O filme tem um ritmo envolvente.') for i in range(5)]
  buckets.append(BucketResult(nome=nome,alvo=40,modo='reduzido',estado_piso='sem_quantificador',niveis=[lvl]))
 monkeypatch.setattr(P,'_buckets_do_bruto',lambda *a:buckets)
 consenso=tmp_path/'consenso.json';consenso.write_text('[]')
 pares=[dict(bucket=b.nome,system=S.build_system_prompt(b.nome),user=S.build_user_message(b),review_ids=[f'v{i}' for i in range(5)]) for b in buckets]
 G.D.salvar(tmp_path/'entradas/a.json',dict(bruto=str(tmp_path),coleta={},consenso=str(consenso),fontes_sha256={str(consenso):G.D.sha(consenso)},pares=pares))
 raw=json.dumps(dict(temas=[dict(tema='Ritmo',mencoes_aproximadas=mencoes,n_reviews_analisadas=99,exemplo_parafraseado='O grupo comenta o ritmo do filme.')],observacao_geral='O grupo destaca o ritmo do filme.'))
 base=hashlib.sha256(json.dumps([pares[0]['system'],pares[0]['user'],G.D.DS,'sintese',LLM_MAX_TOKENS],ensure_ascii=False).encode()).hexdigest()
 cache=tmp_path/'filmes/a/chamadas'/f'{base}_0.json';G.D.salvar(cache,dict(texto=raw,modelo=G.D.DS,uso={}))
 antes=cache.read_bytes()
 G.gerar_filme('a',somente_cache=True)
 estado=G.D.ler(tmp_path/'filmes/a/estado.json');saida=G.D.ler(tmp_path/'filmes/a/negativas.json')
 assert estado['estado']=='parcial_somente_cache' and estado['completo'] is False
 assert set(estado['buckets'])=={'negativas'}
 assert estado['buckets_pendentes']==dict(medianas='sem_resposta_no_cache',positivas='sem_resposta_no_cache')
 assert saida['validador']['passa_publicado'] is passa
 assert saida['saida_producao']['temas'][0]['n_reviews_analisadas']==5
 assert saida['saida_producao']['temas'][0]['mencoes_aproximadas']==mencoes
 tentativa=G.D.ler(tmp_path/'filmes/a/tentativas/negativas_1.json')
 assert tentativa['modelo']==G.D.DS and tentativa['texto']==raw
 assert tentativa['messages'][0]['content']==pares[0]['system']
 assert cache.read_bytes()==antes
 # Retomar não repete nem apaga a tentativa já recuperada.
 G.gerar_filme('a',somente_cache=True)
 assert cache.read_bytes()==antes and G.D.ler(tmp_path/'filmes/a/estado.json')['completo'] is False


def test_cache_ausente_nao_alcanca_adaptador_pago(tmp_path,monkeypatch):
 c=G.ChamadorSomenteCache(tmp_path,'a')
 monkeypatch.setattr(G.F,'resposta',lambda *a,**kw:pytest.fail('não pagar'))
 with pytest.raises(G.CacheAusente):c.chamar('system','user',G.D.DS,'sintese',3000)
 assert not list(tmp_path.rglob('*.json'))

@pytest.mark.parametrize('funcao',[G.configurar_pago,G.rodar])
def test_janela_expirada_recusa_antes_configuracao_ou_saldo(monkeypatch,funcao):
 monkeypatch.setattr(G.time,'time',lambda:G.PRAZO+1)
 monkeypatch.setattr(G.D,'config',lambda:pytest.fail('não reativar cliente fora da janela'))
 monkeypatch.setattr(G.D,'conta',lambda *a:pytest.fail('não consultar rede'))
 with pytest.raises(G.F.TetoExcedido,match='recuperar-cache'):funcao()
