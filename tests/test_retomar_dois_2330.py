import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import retomar_dois_2330 as R

def sessao(tmp_path,monkeypatch):
 R.D.salvar(tmp_path/'plano.json',dict(concurrency=100))
 base=R.F.Sessao(tmp_path,teto_usd=15,etapa='2',prazo_utc=1794182400.)
 with base.db() as db:
  db.execute('CREATE TABLE session_budget(id INTEGER PRIMARY KEY,teto INTEGER,prazo REAL,bloqueado INTEGER)')
  db.execute('INSERT INTO session_budget VALUES(1,19000000000,1794182400,0)')
 monkeypatch.setattr(R.D,'OUT',tmp_path);monkeypatch.setattr(R,'OUT',tmp_path/'urgente');monkeypatch.setattr(R,'BASE_SESSAO',lambda:base)
 R.D.salvar(R.OUT/'autorizacao.json',dict(slugs=list(R.ALVOS),modelos=list(R.MODELOS),prazo_utc=R.PRAZO,teto_sessao_usd=19,letterboxd=False,publicar=False))
 return R.SessaoPontual()

def test_prazo_inclui_margem_e_recusa_antes_de_reservar(tmp_path,monkeypatch):
 s=sessao(tmp_path,monkeypatch);monkeypatch.setattr(R.time,'time',lambda:R.PRAZO-89)
 with pytest.raises(R.F.TetoExcedido):s.reservar(1,1)
 assert s.resumo()['chamadas']==0

def test_teto_compartilhado_atomico_preserva_politica_antiga(tmp_path,monkeypatch):
 from concurrent.futures import ThreadPoolExecutor
 s=sessao(tmp_path,monkeypatch);monkeypatch.setattr(R.time,'time',lambda:R.PRAZO-10000)
 def reservar(_):
  try:return s.reservar(1_000_000_000,1)
  except R.F.TetoExcedido:return None
 with ThreadPoolExecutor(max_workers=8) as ex:rs=list(ex.map(reservar,range(22)))
 assert sum(x is not None for x in rs)==19
 assert s.resumo()['reservas_pendentes_usd']==19
 with s.db() as db:assert db.execute('SELECT prazo FROM session_budget').fetchone()==(1794182400.,)

def test_bloqueio_por_cobranca_nao_e_afrouxado(tmp_path,monkeypatch):
 s=sessao(tmp_path,monkeypatch);monkeypatch.setattr(R.time,'time',lambda:R.PRAZO-10000)
 with s.db() as db:db.execute('UPDATE session_budget SET bloqueado=1')
 with pytest.raises(R.F.TetoExcedido):s.reservar(1,1)
 assert s.resumo()['chamadas']==0

@pytest.mark.parametrize('slug,estagio,modelo',[('outro','verificador',R.D.DS),(R.ALVOS[0],'classificacao',R.D.DS),(R.ALVOS[0],'verificador',R.MODELOS[-1]),(R.ALVOS[0],'sintese','outro')])
def test_escopo_recusa_antes_da_rede(slug,estagio,modelo,monkeypatch):
 monkeypatch.setattr(R,'BASE_RESPOSTA',lambda *a,**kw:pytest.fail('rede não autorizada'))
 with pytest.raises(AssertionError):R.resposta_restrita('s','u',modelo,slug=slug,estagio=estagio)

def test_nao_inicia_worker_na_margem_do_prazo(monkeypatch):
 monkeypatch.setattr(R.time,'time',lambda:R.PRAZO-94)
 monkeypatch.setattr(R.subprocess,'Popen',lambda *a,**kw:pytest.fail('não iniciar worker'))
 assert R.executar(R.ALVOS[0],'verificar')=='prazo'

def test_aumento_tecnico_so_no_verificador_sem_mudar_prompt(monkeypatch):
 calls=[]
 monkeypatch.setattr(R,'BASE_RESPOSTA',lambda *a,**kw:calls.append((a,kw)))
 R.resposta_restrita('system idêntico','review idêntica',R.D.DS,slug=R.ALVOS[0],estagio='verificador',max_tokens=300)
 assert calls==[(('system idêntico','review idêntica',R.D.DS),dict(slug=R.ALVOS[0],estagio='verificador',max_tokens=2048))]
 R.resposta_restrita('s','u',R.MODELOS[-1],slug=R.ALVOS[1],estagio='condicoes',max_tokens=900)
 assert calls[-1][1]['max_tokens']==900
