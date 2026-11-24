"""Sínteses candidatas isoladas; autorização pontual até 23:50 de Recife.

Não altera treino, split, pré-registro, publicado ou consenso. Sem coleta.
"""
from __future__ import annotations
import argparse,collections,concurrent.futures,contextlib,hashlib,json,os,signal,subprocess,sys,threading,time
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import retomar_dois_2330 as R
D=R.D;F=D.F
ROOT=D.ROOT
OUT=ROOT/'finetune/dados_candidatos/featherless-2026-11-08'
FT=ROOT.parent/'espectro-24-finetune/finetune'
PRAZO=datetime(2026,11,9,2,50,tzinfo=timezone.utc).timestamp()
STOP=threading.Event()
BASE_RESPOSTA=F.resposta

class CacheAusente(RuntimeError):
 """A recuperação offline nunca substitui uma resposta ausente por rede."""

class ChamadorSomenteCache(D.Chamador):
 def chamar(self,system,user,model,estagio,max_tokens):
  base=hashlib.sha256(json.dumps([system,user,model,estagio,max_tokens],ensure_ascii=False).encode()).hexdigest()
  n=self.n[base];self.n[base]+=1
  path=self.p/'chamadas'/f'{base}_{n}.json'
  if not path.exists():raise CacheAusente('resposta paga ausente do cache')
  d=D.ler(path);assert d['modelo']==model,'modelo do cache diverge'
  return d

@contextlib.contextmanager
def sem_rede():
 import requests
 original_request=requests.sessions.Session.request;original_resposta=F.resposta
 def negar(*a,**kw):raise RuntimeError('rede proibida na recuperação offline')
 requests.sessions.Session.request=negar;F.resposta=negar
 try:yield
 finally:requests.sessions.Session.request=original_request;F.resposta=original_resposta

def log(s):print(R.agora(),s,flush=True)
def carregar_manifesto():
 m=D.ler(OUT/'manifesto.json');assert m['prazo_utc']==PRAZO and m['modelo']==D.DS and m['incorporado_ao_treino'] is False
 for p,h in m['fontes_exclusao_sha256'].items():assert D.sha(p)==h,'escopo/split alterado'
 assert not set(m['slugs'])&set(m['excluidos'])
 return m

def exclusoes():
 prereg=FT/'PREREGISTRO_C22.md';escopo=FT/'c22/escopo.json';split=FT/'split.json'
 marca=next(l for l in prereg.read_text().splitlines() if l.startswith('<!-- preregistro_c22 '))
 assert D.sha(escopo)==json.loads(marca[len('<!-- preregistro_c22 '):-4])['escopo_sha256']
 sp=D.ler(split);fontes=[prereg,escopo,split,FT/'PREREGISTRO_AVALIACAO.md']
 motivos=collections.defaultdict(list)
 for r in D.ler(escopo)['incluidos']:motivos[r['slug']].append('C22')
 for conjunto in ['teste','validacao','fixos_no_teste']:
  for s in sp[conjunto]:motivos[s].append('split:'+conjunto)
 # Avaliações auxiliares também ficam protegidas, no nível do filme.
 for nome in ['especificidade/mapa/validacao_v2_mapa.json','guarda/fluencia_mapa.json']:
  p=FT/nome;fontes.append(p)
  for s in {r['slug'] for r in D.ler(p)['itens']}:motivos[s].append('avaliacao:'+nome)
 for s in sp['excluidos']:motivos[s].append('exclusao_existente_do_split')
 return dict(motivos),{str(p):D.sha(p) for p in fontes}

def fonte(slug):
 p=D.pasta(slug);es=D.ler(p/'estado.json') if (p/'estado.json').exists() else {}
 pub=ROOT/'resultado'/f'{slug}.json';docpath=pub if pub.exists() else p/'bullets.json';doc=D.ler(docpath)
 bruto=Path(es['bruto_raiz']) if es.get('bruto_raiz') else (D.OUT/'bruto' if es.get('origem')=='novo' else ROOT/'dados/bruto')
 cons=p/'classificacao/consenso_verificado.jsonl'
 if not cons.exists():cons=ROOT/'resultado/votacao-3/consenso_verificado.jsonl'
 return docpath,doc,bruto,cons

def preparar():
 from espectro24 import synthesize as S,eixos as E
 from espectro24.prosa_local import _buckets_do_bruto
 OUT.mkdir(parents=True,exist_ok=True);OUT.chmod(0o700)
 if (OUT/'manifesto.json').exists():return carregar_manifesto()
 excluidos,hashes=exclusoes();pub=D.ler(ROOT/'dados/publicados.json')['slugs'];cand=[r['slug'] for r in D.ler(D.OUT/'manifesto.json')['candidatos']]
 universo=list(dict.fromkeys(pub+cand));elegiveis=[s for s in universo if s not in excluidos];slugs=[];falhas=[]
 for slug in elegiveis:
  try:
   path,doc,bruto,cons=fonte(slug);meta=doc.get('coleta') or D.ler(bruto/slug/'meta.json');buckets=_buckets_do_bruto(slug,meta,bruto)
   am={b.nome:{r.viewing_id for r in b.reviews_analisadas} for b in buckets}
   cat=E.carregar_classificacao(cons);E.checar_amostra_classificada(cat[slug],am)
   linhas=[r for r in D.linhas(cons) if r['slug']==slug and r['id'] in set().union(*am.values())]
   assert linhas and not any(r.get('verificacao_pendente') for r in linhas),'verificador_pendente'
   pares=[]
   for b in buckets:
    system=S.build_system_prompt(b.nome);user=S.build_user_message(b)
    pares.append(dict(bucket=b.nome,system=system,user=user,system_sha256=__import__('hashlib').sha256(system.encode()).hexdigest(),user_sha256=__import__('hashlib').sha256(user.encode()).hexdigest(),review_ids=sorted(am[b.nome]),n=b.n_validas,modo=b.modo,estado_piso=b.estado_piso))
   entrada=dict(slug=slug,origem='publicado' if slug in pub else 'candidato',documento=str(path),bruto=str(bruto),consenso=str(cons),coleta=meta,fontes_sha256={str(p):D.sha(p) for p in [path,cons,bruto/slug/'meta.json']},pares=pares)
   D.salvar(OUT/'entradas'/f'{slug}.json',entrada);slugs.append(slug)
  except Exception as e:falhas.append(dict(slug=slug,categoria=type(e).__name__,motivo='amostra_consenso_ou_fonte_nao_reproduzivel'))
 m=dict(utc=R.agora(),modelo=D.DS,prazo_utc=PRAZO,prazo_recife='2026-11-08T23:50:00-03:00',teto_sessao_usd=19,universo=universo,slugs=slugs,excluidos={s:excluidos[s] for s in universo if s in excluidos},falhas_preflight=falhas,fontes_exclusao_sha256=hashes,incorporado_ao_treino=False,alterou_preregistro=False,publicar=False)
 D.salvar(OUT/'manifesto.json',m);D.escrever_atomico(OUT/'slugs.txt','\n'.join(slugs)+'\n')
 D.salvar(OUT/'autorizacao.json',dict(slugs=slugs,modelos=[D.DS],prazo_utc=PRAZO,teto_sessao_usd=19,letterboxd=False,publicar=False,estagios=['sintese']))
 log(f'Pré-checagem: {len(universo)} filmes; {len(m["excluidos"])} excluídos; {len(slugs)} aptos; {len(falhas)} falhas de fonte.')
 return m

def configurar_pago():
 if time.time()>=PRAZO-95:raise F.TetoExcedido('janela paga encerrada; use recuperar-cache')
 D.config();m=carregar_manifesto();R.OUT=OUT;R.PRAZO=PRAZO;R.ALVOS=tuple(m['slugs']);R.MODELOS=(D.DS,)
 R.bloquear_coleta();F.sessao_ambiente=R.SessaoPontual
 def restrita(system,user,model,**kw):
  meta={**F.metadados(),**{k:v for k,v in kw.items() if k in ['slug','estagio']}}
  assert meta.get('slug') in m['slugs'] and meta.get('estagio')=='sintese' and model==D.DS
  if STOP.is_set():raise F.TetoExcedido('fila encerrada')
  return BASE_RESPOSTA(system,user,model,**kw)
 F.resposta=restrita
 return m

def gerar_filme(slug,*,somente_cache=False):
 from espectro24 import synthesize as S
 from espectro24.prosa_local import _buckets_do_bruto
 from espectro24.render import build_output
 from espectro24.config import LLM_MAX_TOKENS
 from espectro24.validacao_publicado import validar_publicado
 m=carregar_manifesto();assert slug in m['slugs'] and slug not in m['excluidos']
 p=OUT/'filmes'/slug;p.mkdir(parents=True,exist_ok=True)
 if (p/'estado.json').exists() and D.ler(p/'estado.json').get('completo'):return
 if not somente_cache and (STOP.is_set() or time.time()>=PRAZO-95):return
 estado=dict(slug=slug,estado='em_andamento',completo=False,inicio_utc=R.agora(),buckets={},buckets_pendentes={},somente_cache=somente_cache);D.salvar(p/'estado.json',estado)
 try:
  entrada=D.ler(OUT/'entradas'/f'{slug}.json')
  assert all(D.sha(path)==h for path,h in entrada['fontes_sha256'].items()),'fonte alterada'
  buckets=_buckets_do_bruto(slug,entrada['coleta'],Path(entrada['bruto']));esperados={r['bucket']:r for r in entrada['pares']}
  chamadas=ChamadorSomenteCache(p,slug) if somente_cache else D.Chamador(p,slug)
  for b in buckets:
   base=esperados[b.nome];system=S.build_system_prompt(b.nome);user=S.build_user_message(b)
   assert system==base['system'] and user==base['user'],'prompt ou amostra alterado'
   path=p/f'{b.nome}.json'
   if path.exists():estado['buckets'][b.nome]=D.ler(path)['validador'];continue
   if not somente_cache and (STOP.is_set() or time.time()>=PRAZO-95):raise F.TetoExcedido('prazo ou teto')
   tentativas=[]
   def call(system,user,model):
    assert model==D.DS
    n=len(tentativas)+1;meta=dict(slug=slug,bucket=b.nome,ordem=n,messages=[dict(role='system',content=system),dict(role='user',content=user)],modelo=model,incorporado_ao_treino=False)
    D.salvar(p/'prompts'/f'{b.nome}_{n}.json',meta)
    with F.contexto('sintese',slug,b.nome):resp=chamadas.chamar(system,user,model,'sintese',LLM_MAX_TOKENS)
    registro={**meta,**resp};D.salvar(p/'tentativas'/f'{b.nome}_{n}.json',registro);tentativas.append(registro)
    return resp['texto']
   try:S.synthesize_bucket(b,client_call=call,model=D.DS,provider='featherless')
   except CacheAusente:
    assert somente_cache
    estado['buckets_pendentes'][b.nome]='sem_resposta_no_cache' if not tentativas else 'retentativa_de_producao_ausente_no_cache'
    D.salvar(p/'estado.json',estado)
    continue
   bp=build_output(slug,[b],data_coleta=entrada['coleta'].get('coletado_em','2026-11-08'),origens={},total_observado=0,coleta=entrada['coleta'])['buckets'][0]
   val=validar_publicado(bp) if b.modo!='sem_analise' else dict(passa_publicado=None,estado='sem_analise')
   D.salvar(path,dict(slug=slug,bucket=b.nome,modelo=D.DS,messages=[dict(role='system',content=base['system']),dict(role='user',content=base['user'])],saida_producao=bp,validador=val,tentativas=len(tentativas),consenso_sha256=entrada['fontes_sha256'][entrada['consenso']],review_ids=base['review_ids'],incorporado_ao_treino=False))
   estado['buckets'][b.nome]=val;D.salvar(p/'estado.json',estado)
  if somente_cache and estado['buckets_pendentes']:
   estado.update(completo=False,estado='parcial_somente_cache',fim_utc=R.agora())
  else:
   assert set(estado['buckets'])=={'negativas','medianas','positivas'}
   estado.update(completo=True,estado='gerado_validado' if all(v.get('passa_publicado') is True for v in estado['buckets'].values()) else 'gerado_com_falha_validador',fim_utc=R.agora())
 except F.TetoExcedido:STOP.set();estado.update(estado='interrompido_teto_ou_prazo',completo=False)
 except Exception as e:estado.update(estado='falha',categoria=type(e).__name__,completo=False)
 D.salvar(p/'estado.json',estado);log(f'{slug}: {estado["estado"]}')

def recuperar_cache():
 """Pós-processa respostas já cobradas, mesmo após o prazo, sem rede."""
 import shutil
 m=carregar_manifesto()
 for nome in ['RELATORIO.json','RELATORIO.md']:
  origem=OUT/nome;dest=OUT/nome.replace('RELATORIO','RELATORIO_EXECUCAO_PAGA_2026-11-08')
  if origem.exists() and not dest.exists():shutil.copy2(origem,dest)
 original=D.ler(OUT/'RELATORIO_EXECUCAO_PAGA_2026-11-08.json')
 guardados={p:D.sha(p) for p in (D.OUT/'caixa.sqlite3',ROOT/'dados/publicados.json')}
 with sem_rede():
  for slug in m['slugs']:
   path=OUT/'filmes'/slug/'estado.json'
   backup=path.with_name('estado_antes_recuperacao.json')
   if path.exists() and not backup.exists():shutil.copy2(path,backup)
   gerar_filme(slug,somente_cache=True)
 assert all(D.sha(p)==h for p,h in guardados.items()),'caixa ou publicação alterados'
 filmes=[D.ler(OUT/'filmes'/s/'estado.json') for s in m['slugs']]
 custos={f['slug']:f.get('custo_usd',0) for f in original['filmes']}
 for filme in filmes:filme['custo_usd']=custos[filme['slug']]
 pares=[]
 for slug in m['slugs']:
  for bucket in ('negativas','medianas','positivas'):
   path=OUT/'filmes'/slug/f'{bucket}.json'
   if path.exists():pares.append(D.ler(path))
 assert all(p['slug'] in m['slugs'] and p['slug'] not in m['excluidos'] for p in pares)
 rep={**original,'utc':R.agora(),'modo':'recuperacao_offline','chamadas_novas_na_recuperacao':0,
      'filmes':filmes,'filmes_completos':sum(f['completo'] for f in filmes),
      'filmes_validados':sum(f['estado']=='gerado_validado' for f in filmes),
      'buckets_completos':len(pares),'buckets_validados':sum(p['validador']['passa_publicado'] is True for p in pares),
      'respostas_pagas_em_cache':len(list((OUT/'filmes').glob('*/chamadas/*.json'))),
      'buckets_pendentes':sum(len(f.get('buckets_pendentes',{})) for f in filmes),
      'falhas_preflight':m['falhas_preflight'],'saldo_final_referente_a':'2026-11-08 (execução paga)',
      'recuperacao_custo_usd':0,'caixa_inalterado':True}
 D.jsonl(OUT/'pares_candidatos_recuperados.jsonl',pares)
 D.salvar(OUT/'RELATORIO.json',rep)
 D.salvar(OUT/'pendencias.json',[dict(slug=f['slug'],estado=f['estado'],buckets_pendentes=f.get('buckets_pendentes',{}),categoria=f.get('categoria')) for f in filmes if not f['completo']])
 slugs_recuperados=sorted({p['slug'] for p in pares})
 D.escrever_atomico(OUT/'slugs_recuperados.txt','\n'.join(slugs_recuperados)+'\n')
 D.escrever_atomico(OUT/'RELATORIO.md',f'''# Sínteses candidatas — recuperação offline

Filmes completos: **{rep['filmes_completos']} de {len(m['slugs'])}**. O erro de gravação de telemetria interrompeu cada filme depois da primeira resposta. Nenhum filme parcial foi marcado como completo.

Respostas pagas preservadas: {rep['respostas_pagas_em_cache']}. Buckets recuperados pelo pipeline de produção: {rep['buckets_completos']}; validadores passando: {rep['buckets_validados']}; buckets pendentes: {rep['buckets_pendentes']}. Outros {len(m['falhas_preflight'])} filmes ficaram fora da geração por verificador pendente no consenso existente.

Custo pago em 08/11: **US$ {rep['custo_lote_usd']:.9f}**, conciliado com o débito da conta. Recuperação offline: **US$ 0** e nenhuma chamada de rede. O saldo histórico registrado no encerramento era US$ {original['saldo_final']['balance_usd']}; ele não representa saldo disponível após o vencimento do crédito.

Nenhum dado foi incorporado ao treino, ao split ou ao pré-registro. Sem publicação ou commit. C22, teste, validação e avaliações auxiliares ficaram excluídos.

Lista planejada: slugs.txt. Slugs com saídas recuperadas: slugs_recuperados.txt. Pares candidatos: pares_candidatos_recuperados.jsonl. Proveniência e exclusões: manifesto.json. Pendências: pendencias.json. Detalhes dos validadores: RELATORIO.json. Relatório original preservado em RELATORIO_EXECUCAO_PAGA_2026-11-08.json.
''')
 D.salvar(OUT/'recuperacao_offline.json',dict(utc=R.agora(),completos=rep['filmes_completos'],buckets_recuperados=len(pares),custo_usd=0,chamadas_rede=0))
 return rep

def gerar():
 m=configurar_pago()
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(gerar_filme,m['slugs']))

def vigiar():
 while time.time()<PRAZO-3:
  if (OUT/'concluido.json').exists():return
  time.sleep(.5)
 if (OUT/'estado.json').exists():
  pid=D.ler(OUT/'estado.json').get('worker_pid')
  if pid:
   cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
   if 'gerar_candidatos_sintese_featherless.py gerar' in cmd:
    try:os.killpg(pid,signal.SIGKILL)
    except ProcessLookupError:pass
 D.salvar(OUT/'parada_rigida.json',dict(utc=R.agora()))

def relatorio():
 D.config();m=carregar_manifesto();ini=D.ler(OUT/'inicio.json');saldo=D.conta('credits/balance');caixa=R.BASE_SESSAO().resumo();filmes=[]
 for s in m['slugs']:
  p=OUT/'filmes'/s/'estado.json';e=D.ler(p) if p.exists() else dict(slug=s,estado='nao_iniciado',completo=False)
  if e['estado']=='em_andamento':e.update(estado='interrompido',completo=False);D.salvar(p,e)
  filmes.append(e)
 with R.BASE_SESSAO().db() as db:regs=[json.loads(r[0]) for r in db.execute('SELECT registro FROM chamadas WHERE registro IS NOT NULL')]
 regs=[r for r in regs if r.get('ts') and datetime.fromisoformat(r['ts'])>=datetime.fromisoformat(ini['utc'])]
 assert all(r['slug'] in m['slugs'] and r['estagio']=='sintese' and r['modelo']==D.DS for r in regs)
 for r in filmes:r['custo_usd']=sum(x.get('custo_usd') or 0 for x in regs if x['slug']==r['slug'])
 rep=dict(utc=R.agora(),filmes_completos=sum(r['completo'] for r in filmes),filmes_validados=sum(r['estado']=='gerado_validado' for r in filmes),buckets_completos=sum(len(r.get('buckets',{})) for r in filmes),filmes=filmes,custo_lote_usd=caixa['custo_usd']-ini['caixa']['custo_usd'],debito_conta_usd=float(ini['saldo']['balance_usd'])-float(saldo['balance_usd']),saldo_final=saldo,caixa_sessao=caixa,chamadas=len(regs),incorporado_ao_treino=False,preregistro_inalterado=True,publicado=False)
 D.salvar(OUT/'telemetria.json',regs);D.salvar(OUT/'RELATORIO.json',rep)
 D.escrever_atomico(OUT/'RELATORIO.md',f'# Sínteses candidatas — não incorporadas ao treino\n\nFilmes completos: {rep["filmes_completos"]}/{len(m["slugs"])}. Todos os validadores passando: {rep["filmes_validados"]}. Buckets: {rep["buckets_completos"]}.\n\nCusto do lote: US$ {rep["custo_lote_usd"]:.9f}. Débito da conta: US$ {rep["debito_conta_usd"]:.9f}. Saldo final: US$ {saldo["balance_usd"]}.\n\nSem publicação, commit ou alteração do treino/pré-registro. Lista: slugs.txt. Exclusões e proveniência: manifesto.json. Validação por filme e bucket: RELATORIO.json.\n')
 return rep

def rodar():
 if time.time()>=PRAZO-95:raise F.TetoExcedido('janela paga encerrada; use recuperar-cache')
 D.config();D.conferir();m=preparar()
 with D.trava(OUT/'driver.lock'):
  if (OUT/'concluido.json').exists():(OUT/'concluido.json').unlink()
  if not (OUT/'inicio.json').exists():D.salvar(OUT/'inicio.json',dict(utc=R.agora(),saldo=D.conta('credits/balance'),caixa=R.BASE_SESSAO().resumo(),publicados_sha256=D.sha(ROOT/'dados/publicados.json'),resultado_sha256={str(p):D.sha(p) for p in (ROOT/'resultado').glob('*.json')}))
  vigia=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'vigiar'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
  with (OUT/'worker.log').open('a') as f:proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'gerar'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  D.salvar(OUT/'estado.json',dict(estado='rodando',pid=os.getpid(),worker_pid=proc.pid,vigia_pid=vigia.pid,prazo_utc=PRAZO))
  try:
   while proc.poll() is None:
    if time.time()>=PRAZO-6:D.encerrar(proc);break
    time.sleep(.2)
  finally:
   D.encerrar(proc);ini=D.ler(OUT/'inicio.json');assert D.sha(ROOT/'dados/publicados.json')==ini['publicados_sha256']
   assert all(D.sha(p)==h for p,h in ini['resultado_sha256'].items())
   rep=relatorio();D.salvar(OUT/'concluido.json',dict(utc=R.agora(),completos=rep['filmes_completos']));D.salvar(OUT/'estado.json',dict(estado='encerrado',worker_pid=None,utc=R.agora()));D.encerrar(vigia)
   log(f'Encerrado: {rep["filmes_completos"]} filmes completos; custo US$ {rep["custo_lote_usd"]:.9f}.')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('modo',choices=['preparar','rodar','gerar','vigiar','relatorio','recuperar-cache']);a=ap.parse_args()
 if a.modo=='preparar':preparar()
 elif a.modo=='rodar':rodar()
 elif a.modo=='gerar':gerar()
 elif a.modo=='vigiar':vigiar()
 elif a.modo=='recuperar-cache':recuperar_cache()
 else:relatorio()
