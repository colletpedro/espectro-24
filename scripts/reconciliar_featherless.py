"""Recalcula o livro pelo cache medido, sem chamada/estimativa de desconto.
Preserva a auditoria sem cache. Só roda com a sessão inteira encerrada.
"""
from pathlib import Path
import json
import sys
from decimal import Decimal, ROUND_CEILING
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from espectro24.featherless import Sessao,custo_nano
from espectro24.atomico import escrever_atomico
P=Path(__file__).resolve().parents[1]/'resultado/featherless-etapa1-2026-11-08'

def main():
    sessao=Sessao(P)
    anterior=(P/'uso.jsonl').read_text()
    novas=[]
    for linha in anterior.splitlines():
        r=json.loads(linha);u=r.get('uso') or {}
        cache=int(u.get('cached_tokens') or (u.get('prompt_tokens_details') or {}).get('cached_tokens') or 0)
        c=custo_nano(r['modelo_efetivo'],r['prompt_tokens'],r['completion_tokens'],cache)
        api=Decimal(str(r['custo_api_usd']))*1_000_000_000
        assert abs(Decimal(c)-api)<=1, (r['reserva_id'],c,str(api))
        r.setdefault('custo_sem_cache_usd',r['custo_usd'])
        r['custo_usd']=max(c,int(api.to_integral_value(rounding=ROUND_CEILING)))/1e9
        r['cache_tokens']=cache
        novas.append(r)
    if not (P/'uso_sem_cache_original.jsonl').exists():
        (P/'uso_sem_cache_original.jsonl').write_text(anterior)
    with sessao.db() as db:
        db.execute('BEGIN IMMEDIATE')
        assert db.execute("select count(*) from chamadas where estado!='concluida'").fetchone()[0]==0
        assert len(novas)==db.execute('select count(*) from chamadas').fetchone()[0]
        for r in novas:
            db.execute('update chamadas set custo=?,registro=? where id=?', (round(r['custo_usd']*1e9),json.dumps(r,ensure_ascii=False),r['reserva_id']))
    # exporta a fonte durável inteira: nova execução repara uma queda nesta fronteira
    escrever_atomico(P/'uso.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in novas))
    print(sessao.resumo())

if __name__=='__main__':main()
