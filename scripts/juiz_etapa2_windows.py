"""Windows/Ollama: consome entradas E5 da Etapa 2 com juiz v2.2, parada no 2º sim.

Não importa o driver pago. Sem --executar, só valida o pacote (zero inferência).
"""
from __future__ import annotations
import argparse
import contextlib
from datetime import datetime,timezone
import json
import hashlib
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import juiz_bullets_v2 as J
import checagem_bullets as C
from espectro24.atomico import escrever_atomico
HASH='44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669'


def estados(pares,regs):
    grupos={}
    for p in pares: grupos.setdefault(p['id_bullet'],[]).append(p)
    saida={}
    for bid,ps in grupos.items():
        sims=julgados=pulados=0;proximo=None
        for p in sorted(ps,key=lambda p:p['rank']):
            if not p['julgavel_estimado']: pulados+=1;continue
            r=regs.get(p['id_par'])
            if not r or not r.get('ok') or r.get('config_sha256')!=HASH: proximo=p;break
            julgados+=1;sims+=J.motivo_da_versao(r,p['texto'],J.CONGELADA) is None
            if sims>=2: break
        estado='pendente' if proximo else 'indeterminado' if julgados==0 else 'apoio_2' if sims>=2 else 'apoio_1' if sims==1 else 'sem_apoio'
        saida[bid]=dict(estado=estado,sims=sims,julgados=julgados,pulados=pulados,proximo=proximo)
    return saida


def validar(d):
    assert J.CONGELADA=='v2.2' and J.config_sha256()==HASH
    m=json.loads((d/'preparado.json').read_text(encoding='utf-8'))
    assert m['config_sha256']==HASH
    if m.get('entrada_sha256'):
        assert hashlib.sha256((d/C.ARQ_ENTRADA).read_bytes()).hexdigest()==m['entrada_sha256']
    pares=C._ler_jsonl(d/C.ARQ_ENTRADA)
    assert len(pares)==m['pares'] and len({p['id_par'] for p in pares})==len(pares)
    assert all('julgavel_estimado' in p for p in pares)
    return pares


def executar(d):
    pares=validar(d);julgaveis=[p for p in pares if p['julgavel_estimado']]
    pasta=d/'juiz_v2';pasta.mkdir(exist_ok=True)
    contexto=pasta/'contexto_v2.2.json'
    if not julgaveis:
        es=estados(pares,{})
        resumo={k:sum(v['estado']==k for v in es.values()) for k in ('pendente','indeterminado','apoio_2','apoio_1','sem_apoio')}
        escrever_atomico(pasta/'estado.json',json.dumps(dict(config_sha256=HASH,estados=resumo,
            concluido=True,sem_pares_julgaveis=True),ensure_ascii=False,indent=2))
        return resumo
    J._exigir_ambiente();J._exigir_modelo()
    if not contexto.exists():
        chamar=J._chamador(num_ctx=J.MEDICAO_NUM_CTX,num_predict=1,schema=J.schema(J.CONGELADA))
        medidos=[]
        for p in J.maiores_pares(julgaveis,versao=J.CONGELADA):
            r=chamar(J.system(J.CONGELADA),J.user(p,J.CONGELADA))
            assert r.get('think')==J.THINK
            medidos.append(dict(id_par=p['id_par'],chars_prompt=J.chars_do_prompt(p),prompt_eval_count=r['prompt_eval_count']))
        med=dict(config_sha256=HASH,medidos=medidos,**J.julgar_medicao(medidos,J.CONGELADA))
        escrever_atomico(contexto,json.dumps(med,ensure_ascii=False,indent=2))
    med=json.loads(contexto.read_text(encoding='utf-8'))
    assert med['config_sha256']==HASH and med['cabe'], 'contexto_nao_cabe'
    saida=pasta/'saida_v2.2.jsonl'
    chamar=J._chamador(num_ctx=J.num_ctx(J.CONGELADA),num_predict=J.NUM_PREDICT,schema=J.schema(J.CONGELADA))
    for _ in range(5):
        regs={r['id_par']:r for r in C._ler_jsonl(saida)}
        es=estados(pares,regs);lote=[v['proximo'] for v in es.values() if v['estado']=='pendente']
        if not lote: break
        lote.sort(key=lambda p:(p['slug'],p['bucket'],p['review_id'],p['i']))
        J.rodar(lote,saida,chamar,versao=J.CONGELADA,progresso_a_cada=50)
        atuais={r['id_par']:r for r in C._ler_jsonl(saida)}
        if any(not atuais.get(p['id_par'],{}).get('ok') for p in lote): break
    es=estados(pares,{r['id_par']:r for r in C._ler_jsonl(saida)})
    resumo={k:sum(v['estado']==k for v in es.values()) for k in ('pendente','indeterminado','apoio_2','apoio_1','sem_apoio')}
    escrever_atomico(pasta/'estado.json',json.dumps(dict(config_sha256=HASH,estados=resumo,concluido=not resumo['pendente']),ensure_ascii=False,indent=2))
    return resumo


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--executar',action='store_true');a=ap.parse_args()
    base=a.base.resolve();log=base/'lacrado_c22/juiz_windows.log';log.parent.mkdir(parents=True,exist_ok=True)
    dirs=sorted(p.parent for p in base.rglob('preparado.json') if p.parent.name=='juiz')
    n=falhas=0
    # Também os erros de contexto ficam no lacrado, sem temas ou reviews na tela.
    with log.open('a',encoding='utf-8') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
        for d in dirs:
            try:
                if a.executar: executar(d)
                else: validar(d)
                n+=1
            except Exception as e:
                falhas+=1;print(datetime.now(timezone.utc).isoformat(),d.parent.name,type(e).__name__,flush=True)
    print(f'{n} pacotes '+('processados' if a.executar else 'validados')+f'; {falhas} falhas. Detalhes no log lacrado.')
    if falhas: raise SystemExit(1)

if __name__=='__main__':main()
