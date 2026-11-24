"""Autorização pontual de 08/11: só dois verificadores e geração, até 23:30 Recife.

Mantém intacta a política anterior para os demais drivers. O caixa, o teto
US$19, as reservas incertas e os triggers continuam sendo os compartilhados.
Nenhuma coleta, publicação ou preparação E5; logs nunca vão ao console.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json,os,signal,subprocess,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import etapa2_featherless as D
import lista3_featherless as L
F=D.F
ALVOS=('logan-2017','how-to-make-millions-before-grandma-dies')
PRAZO=datetime(2026,11,9,2,30,tzinfo=timezone.utc).timestamp()
MODELOS=(D.DS,'Qwen/Qwen3.8-27B','moonshotai/Kimi-K3.1-Pro')
OUT=D.OUT/'retomada_dois_2330'
BASE_SESSAO=F.sessao_ambiente
BASE_RESPOSTA=F.resposta

def agora():return datetime.now(timezone.utc).isoformat()
def log(s):print(agora(),s,flush=True)
def estado(**kw):
 p=OUT/'estado.json';d=D.ler(p) if p.exists() else {};d.update(kw,atualizado_utc=agora());D.salvar(p,d)

def conferir_autorizacao():
 a=D.ler(OUT/'autorizacao.json')
 assert a['slugs']==list(ALVOS) and a['modelos']==list(MODELOS)
 assert a['prazo_utc']==PRAZO and a['teto_sessao_usd']==19 and a['letterboxd'] is False and a['publicar'] is False
 return a

class SessaoPontual:
 """Proxy com reserva atômica no mesmo livro, restrito à nova autorização.

 A política antiga e seu CHECK não são alterados. Só este processo pode
 usar a janela pontual; o wrapper de resposta confere slug/modelo/estágio.
 """
 def __init__(self):
  conferir_autorizacao();self.base=BASE_SESSAO()
  assert self.base.pasta.resolve()==D.OUT.resolve()
  self.prazo_utc=PRAZO
 def __getattr__(self,k):return getattr(self.base,k)
 def reservar(self,valor,unidades):
  from espectro24.synthesize import LLM_PRAZO_PAREDE_S
  assert valor>0 and 0<unidades<=self.unidades
  inicio=time.monotonic()
  while True:
   if time.time()+LLM_PRAZO_PAREDE_S>=PRAZO:raise F.TetoExcedido('prazo pontual atingido, incluindo margem da chamada')
   with self.db() as db:
    db.execute('BEGIN IMMEDIATE')
    from espectro24.sessao_featherless import politica
    pol=politica(db);assert pol and pol[0]==19_000_000_000
    if pol[2]:raise F.TetoExcedido('sessão bloqueada por cobrança fora do contrato')
    gasto,ativas=db.execute("SELECT coalesce(sum(coalesce(custo,reservado)),0),coalesce(sum(CASE WHEN estado IN ('ativa','incerta') THEN unidades ELSE 0 END),0) FROM chamadas").fetchone()
    if gasto+valor>pol[0]:raise F.TetoExcedido('reserva excederia teto compartilhado US$19')
    if ativas+unidades<=self.unidades:
     rid=uuid.uuid4().hex;db.execute('INSERT INTO chamadas VALUES(?,?,NULL,?,?,NULL)',(rid,valor,unidades,'ativa'));return rid
   if time.monotonic()-inicio>60:raise TimeoutError('concorrência indisponível por 60s')
   time.sleep(.05)

def resposta_restrita(system,user,model,**kw):
 meta={**F.metadados(),**{k:v for k,v in kw.items() if k in ('slug','estagio') and v is not None}}
 assert meta.get('slug') in ALVOS,'filme fora da autorização pontual'
 estagio=meta.get('estagio');assert estagio in ('verificador','sintese','rotulagem','condicoes'),'estágio não autorizado'
 assert model in (MODELOS if estagio=='condicoes' else (D.DS,)),'modelo fora do estágio autorizado'
 # Retentativa autorizada: as duas respostas truncaram em 300 tokens.
 # Mantém prompt/modelo e validação JSON; só aumenta a janela de saída.
 if estagio=='verificador':kw['max_tokens']=2048
 return BASE_RESPOSTA(system,user,model,**kw)

def hashes_passes(slug):
 d=D.pasta(slug)/'classificacao';am=D.ler(d/'amostra.json')
 esperado={(r['slug'],r['bucket'],r['id']) for r in am['reviews']};assert esperado and {s for s,b,i in esperado}=={slug}
 for n in (1,2,3):
  regs=[r for r in D.linhas(d/f'passe_{n}.jsonl') if r.get('ok')]
  assert {(r['slug'],r['bucket'],r['id']) for r in regs}==esperado
  assert all(r['provider']=='featherless' and r['modelo']==D.DS and r['modelo_efetivo']==D.DS for r in regs)
 return {str(d/f'passe_{n}.jsonl'):D.sha(d/f'passe_{n}.jsonl') for n in (1,2,3)}

def consenso_pronto(slug,p,am):
 hashes_passes(slug);d=p/'classificacao';ver=D.linhas(d/'consenso_verificado.jsonl')
 assert ver and not any(r.get('verificacao_pendente') for r in ver)
 assert len(ver)==sum(map(len,am.values()))
 assert D.ler(d/'manifesto.json')['n_falharam']==0
 return d/'consenso_verificado.jsonl'

def bloquear_coleta():
 from espectro24.fetcher import Fetcher
 def proibido(*a,**kw):raise RuntimeError('Letterboxd/coleta proibidos nesta retomada')
 Fetcher.get=proibido
 import requests
 from urllib.parse import urlparse
 original=requests.sessions.Session.request
 def request(self,method,url,*a,**kw):
  assert not (urlparse(url).hostname or '').endswith('letterboxd.com'),'Letterboxd proibido'
  return original(self,method,url,*a,**kw)
 requests.sessions.Session.request=request

def worker(slug,modo):
 assert slug in ALVOS;conferir_autorizacao();D.config();bloquear_coleta()
 F.sessao_ambiente=SessaoPontual;F.resposta=resposta_restrita
 antes=hashes_passes(slug);D.PRAZO=PRAZO
 try:
  if modo=='verificar':
   assert L.verificar_pendente(slug),'verificador_ainda_pendente'
  else:
   D.classificar=consenso_pronto;D.modelos_obrigatorios=lambda:list(MODELOS)
   D.gerar_filme(slug)
 finally:
  assert all(D.sha(p)==h for p,h in antes.items()),'passadas pagas alteradas'

def executar(slug,modo):
 if time.time()>=PRAZO-95:return 'prazo'
 p=D.pasta(slug);arq=p/f'retomada_2330_{modo}.log'
 with arq.open('a') as f:
  os.chmod(arq,0o600)
  proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'worker','--slug',slug,'--etapa',modo],cwd=D.ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 estado(worker_pid=proc.pid,worker_slug=slug,worker_etapa=modo)
 try:
  while proc.poll() is None:
   if time.time()>=PRAZO-6:D.encerrar(proc);return 'prazo'
   time.sleep(.2)
  return proc.returncode
 finally:
  D.encerrar(proc);estado(worker_pid=None)

def vigiar():
 while time.time()<PRAZO-3:
  if (OUT/'concluido.json').exists():return
  time.sleep(.5)
 p=OUT/'estado.json'
 if p.exists():
  e=D.ler(p);pid=e.get('worker_pid')
  if pid:
   cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
   if 'retomar_dois_2330.py worker' in cmd:
    try:os.killpg(pid,signal.SIGKILL)
    except ProcessLookupError:pass
 D.salvar(OUT/'parada_rigida.json',dict(utc=agora(),prazo_utc=PRAZO))

def relatorio(resultados):
 D.config();caixa=BASE_SESSAO().resumo();saldo=D.conta('credits/balance');D.salvar(OUT/'saldo_final.json',saldo)
 ini=D.ler(OUT/'inicio.json');delta=float(ini['saldo']['balance_usd'])-float(saldo['balance_usd']);rows=[]
 for slug in ALVOS:
  p=D.pasta(slug);es=D.ler(p/'estado.json');r=dict(slug=slug,c22=es['c22'],estado=es['estado'],etapa=es.get('etapa'),amostra=es.get('amostra'),execucoes=resultados.get(slug,{}))
  d=p/'classificacao';regs=D.linhas(d/'verificador.jsonl');oks={x['id'] for x in regs if x.get('ok')}
  r['verificador']=dict(completos=len(oks),falhas_pendentes=sum(not x.get('ok') and x['id'] not in oks for x in regs),consenso_verificado=(d/'consenso_verificado.jsonl').exists())
  r['passadas_preservadas']=all(D.sha(path)==h for path,h in ini['passadas'][slug].items())
  r['validadores_bullets']=es.get('validadores_bullets');r['validadores_condicoes']=es.get('validadores_condicoes');r['condicoes_geradas']=es.get('condicoes_geradas',[])
  if (p/'bullets.json').exists():
   import publicar_condicoes as PC
   from espectro24 import condicoes as C
   doc=D.ler(p/'bullets.json');r['validadores_publicacao_condicoes']={}
   for m in MODELOS:
    path=p/'condicoes'/m.split('/')[-1]/'condicoes.json'
    if not path.exists():continue
    try:
     b,n=PC.aplicar_retiradas(slug,D.ler(path),doc);PC.validar_bloco(slug,b,C.indexar(doc));v=dict(passa=True,retidas_R13=n)
    except Exception as e:v=dict(passa=False,categoria=type(e).__name__)
    r['validadores_publicacao_condicoes'][m]=v
  with BASE_SESSAO().db() as db:
   chamadas=[json.loads(x[0]) for x in db.execute('SELECT registro FROM chamadas WHERE registro IS NOT NULL')]
  r['custo_acumulado_filme_usd']=sum(x.get('custo_usd') or 0 for x in chamadas if x.get('slug')==slug)
  rows.append(r)
 rep=dict(utc=agora(),prazo_recife='2026-11-08T23:30:00-03:00',filmes=rows,caixa_sessao=caixa,saldo_final=saldo,debito_retomada_usd=delta,custo_retomada_livro_usd=caixa['custo_usd']-ini['caixa']['custo_usd'],reservas_anteriores_usd=ini['caixa']['reservas_pendentes_usd'],publicado=False,letterboxd_requisicoes=0)
 D.salvar(OUT/'relatorio.json',rep)
 md=['# Retomada de dois filmes até 23:30','', 'Sem conteúdo gerado, sem publicação e sem Letterboxd.','', '|Slug|C22|Estado|Verificador completo|Passadas preservadas|','|---|---|---|---|---|']
 for r in rows:md.append(f"|{r['slug']}|{'s' if r['c22'] else 'n'}|{r['estado']}|{r['verificador']['consenso_verificado']}|{r['passadas_preservadas']}|")
 md+=['',f"Saldo final: US$ {saldo['balance_usd']}; débito nesta retomada: US$ {delta:.9f}.",f"Caixa total da sessão: US$ {caixa['custo_usd']:.9f}; reservas pendentes: US$ {caixa['reservas_pendentes_usd']:.9f}; teto: US$ 19.",'','Validadores mecânicos e custos por filme: relatorio.json.']
 D.escrever_atomico(OUT/'RELATORIO.md','\n'.join(md)+'\n');return rep

def rodar():
 D.config();D.conferir();OUT.mkdir(parents=True,exist_ok=True);OUT.chmod(0o700)
 with D.trava(OUT/'driver.lock'):
  if not (OUT/'autorizacao.json').exists():D.salvar(OUT/'autorizacao.json',dict(slugs=list(ALVOS),modelos=list(MODELOS),prazo_utc=PRAZO,teto_sessao_usd=19,letterboxd=False,publicar=False,autorizado_utc=agora()))
  conferir_autorizacao()
  # O vigia não pode herdar um marcador de conclusão de uma tentativa anterior.
  if (OUT/'concluido.json').exists():
   D.salvar(OUT/f'concluido_anterior_{int(time.time())}.json',D.ler(OUT/'concluido.json'));(OUT/'concluido.json').unlink()
  if not (OUT/'inicio.json').exists():D.salvar(OUT/'inicio.json',dict(utc=agora(),caixa=BASE_SESSAO().resumo(),saldo=D.conta('credits/balance'),passadas={s:hashes_passes(s) for s in ALVOS},publicados_sha256=D.sha(D.ROOT/'dados/publicados.json')))
  vigia=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'vigiar'],cwd=D.ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
  estado(estado='rodando',pid=os.getpid(),vigia_pid=vigia.pid,prazo_utc=PRAZO)
  resultados={s:{} for s in ALVOS};prontos=[]
  try:
   for slug in ALVOS:
    log(f'{slug}: retomando apenas verificador pendente')
    rc=executar(slug,'verificar');resultados[slug]['verificador_rc']=rc
    if rc==0:prontos.append(slug);log(f'{slug}: verificador completo')
    else:log(f'{slug}: verificador não concluído; código {rc}')
   for slug in prontos:
    log(f'{slug}: gerando síntese, rotulagem e condições DeepSeek/Qwen/Kimi')
    rc=executar(slug,'gerar');resultados[slug]['geracao_rc']=rc
    if rc!=0:
     p=D.pasta(slug)/'estado.json';e=D.ler(p);e.update(estado='interrompido' if rc=='prazo' else 'falha',erro='parada_2330' if rc=='prazo' else 'worker_falhou',retomavel=True);D.salvar(p,e)
    log(f'{slug}: geração encerrada; código {rc}')
  finally:
   assert D.sha(D.ROOT/'dados/publicados.json')==D.ler(OUT/'inicio.json')['publicados_sha256']
   rep=relatorio(resultados);D.salvar(OUT/'concluido.json',dict(utc=agora(),gerados=sum(r['estado']=='gerado' for r in rep['filmes'])));estado(estado='encerrado',worker_pid=None)
   D.encerrar(vigia);log('Encerrado; relatório sem conteúdo gravado.')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('modo',choices=['rodar','worker','vigiar']);ap.add_argument('--slug',choices=ALVOS);ap.add_argument('--etapa',choices=['verificar','gerar']);a=ap.parse_args()
 if a.modo=='rodar':rodar()
 elif a.modo=='vigiar':vigiar()
 else:worker(a.slug,a.etapa)
