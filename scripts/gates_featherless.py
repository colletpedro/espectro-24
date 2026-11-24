"""Etapa 1 Featherless: medições isoladas, teto compartilhado de US$3.
Nunca publica; não modifica os arquivos de votação de produção.
"""
from pathlib import Path
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import random
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'), str(ROOT/'scripts'),str(ROOT/'scripts/finetune')]
from dotenv import load_dotenv
from espectro24 import featherless as F
from espectro24 import synthesize as S
OUT=ROOT/'resultado/featherless-etapa1-2026-11-08'
DEEPSEEK='deepseek-ai/DeepSeek-V4.1-Flash-1017'
FILMES=['cats-2019','aftersun','parasite-2019']
CANDIDATOS=[DEEPSEEK,'moonshotai/Kimi-K3.1-Pro','Qwen/Qwen3.8-27B']
HASH_JUIZ='44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669'

def ler(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []

def gravar(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2))

def config():
    load_dotenv(ROOT/'.env')
    os.environ['FEATHERLESS_SESSION_DIR']=str(OUT)
    os.environ['FEATHERLESS_TETO_USD']='3.00'


def estados_juiz(entrada, regs):
    """Parada no 2º sim, igual a avaliar_c1_c4.estado_do_bullet.

    A avaliação pura é conferida em teste contra a implementação original;
    importar seu harness offline num processo pago instala _guarda global.
    """
    import juiz_bullets_v2 as J
    from collections import defaultdict
    grupos=defaultdict(list)
    for p in entrada:grupos[p['id_bullet']].append(p)
    saida={}
    for bid,ps in grupos.items():
        sims=julgados=pulados=0;proximo=None
        for p in sorted(ps,key=lambda p:p['rank']):
            if not p['julgavel_estimado']:pulados+=1;continue
            r=regs.get(p['id_par'])
            if not r or not r.get('ok') or r.get('config_sha256')!=HASH_JUIZ:
                proximo=p;break
            julgados+=1;sims+=J.motivo_da_versao(r,p['texto']) is None
            if sims>=2:break
        estado=('pendente' if proximo else 'indeterminado' if julgados==0 else 'apoio_2' if sims>=2 else 'apoio_1' if sims==1 else 'sem_apoio')
        saida[bid]=dict(estado=estado,sims=sims,julgados=julgados,pulados=pulados,proximo=proximo,slug=ps[0]['slug'],bucket=ps[0]['bucket'])
    return saida


def gate_a():
    import juiz_bullets_v2 as J
    assert J.config_sha256()==HASH_JUIZ
    pasta=OUT/'gate_a';entrada=ler(pasta/'local_entrada.jsonl');local=ler(pasta/'local_saida.jsonl')
    assert len(local)==1600
    assert all(r['config_sha256']==HASH_JUIZ for r in local)
    byid={p['id_par']:p for p in entrada}
    alvo=[byid[r['id_par']] for r in local]
    saida=pasta/'hospedado.jsonl';lock=threading.Lock();client=F.client()
    feitas={r['id_par'] for r in ler(saida)}
    t0=time.monotonic()
    def tarefa(p):
        if p['id_par'] in feitas:return
        reg=dict(id_par=p['id_par'],config_sha256=HASH_JUIZ,versao=J.CONGELADA)
        inicio=time.monotonic()
        try:
            resp=F.resposta(J.system(),J.user(p),'openai/gpt-oss-20b',max_tokens=1024,json_mode=True,client=client,
                           estagio='gate_a',slug=p['slug'],bucket=p['bucket'],reasoning_effort='low',temperature=1,seed=J.SEED,response_schema=J.schema())
            text=resp.choices[0].message.content or ''
            reg.update(resposta_crua=text,finish_reason=resp.choices[0].finish_reason,uso=S.uso(resp,'featherless'))
            data=J.ler_resposta_v2_2(text)
            motivo=J.motivo_da_versao(data,p['texto'])
            reg.update(data,ok=True,motivo_sem_apoio=motivo,modelo_efetivo=resp.model,
                       finish_reason=resp.choices[0].finish_reason,uso=S.uso(resp,'featherless'),resposta_crua=text)
            if resp.choices[0].finish_reason=='length':reg.update(ok=False,erro='saida_truncada')
        except Exception as e:
            reg.update(ok=False,erro=f'{type(e).__name__}: {e}'[:500])
        reg['latencia_s']=round(time.monotonic()-inicio,3)
        with lock:
            with saida.open('a') as f:f.write(json.dumps(reg,ensure_ascii=False)+'\n')
            feitas.add(p['id_par'])
            if len(feitas)%100==0:print('Gate A',len(feitas),'pares',flush=True)
        return reg
    # A primeira chamada pertence aos 1600; erro de protocolo para o gate cedo.
    pend=[p for p in alvo if p['id_par'] not in feitas]
    if pend:
        piloto=tarefa(pend[0])
        if not piloto.get('ok'):
            gravar(pasta/'bloqueio.json',piloto);print('Gate A: piloto falhou',piloto.get('erro'));return
        with ThreadPoolExecutor(max_workers=32) as ex:list(ex.map(tarefa,pend[1:]))
    hosted={r['id_par']:r for r in ler(saida)}
    cm=Counter();porpar=[]
    for p in alvo:
        l=next(r for r in local if r['id_par']==p['id_par']);h=hosted.get(p['id_par'])
        def apoio(r):
            return None if not r or not r.get('ok') else J.motivo_da_versao(r,p['texto']) is None
        a,b=apoio(l),apoio(h)
        porpar.append(dict(id_par=p['id_par'],local=a,hospedado=b,concorda=None if a is None or b is None else a==b))
        if a is not None and b is not None:cm[(int(a),int(b))]+=1
    n=sum(cm.values());po=(cm[(0,0)]+cm[(1,1)])/n if n else 0
    pe=sum(sum(v for (a,b),v in cm.items() if a==k)*sum(v for (a,b),v in cm.items() if b==k) for k in (0,1))/n**2 if n else 1
    # A mesma parada no segundo SIM; pares adicionais só para fechar C1/C2.
    estados_fixos=estados_juiz(entrada,hosted)
    n_extra=0
    for rodada in range(5):
        est=estados_juiz(entrada,hosted)
        extras=[v['proximo'] for v in est.values() if v['estado']=='pendente' and v['proximo']['id_par'] not in hosted]
        if not extras:break
        with ThreadPoolExecutor(max_workers=24) as ex:list(ex.map(tarefa,extras))
        n_extra+=len(extras);hosted={r['id_par']:r for r in ler(saida)}
    def metricas(regs):
        est=estados_juiz(entrada,regs);cont=Counter(e['estado'] for e in est.values())
        den=sum(cont[k] for k in ('sem_apoio','apoio_1','apoio_2'))
        return dict(estados=dict(cont),bullets_julgados=den,C1_sem_apoio=cont['sem_apoio']/den if den else None,C2_apoio_2=cont['apoio_2']/den if den else None,completo=not cont['pendente'])
    result=dict(hash_juiz=HASH_JUIZ,pares_comuns=n,concordancia=po,kappa=(po-pe)/(1-pe) if pe<1 else None,
                matriz_local_linhas_hospedado_colunas=[[cm[(a,b)] for b in (0,1)] for a in (0,1)],
                local=metricas({r['id_par']:r for r in local}),hospedado_1600=metricas({k:v for k,v in hosted.items() if k in {p['id_par'] for p in alvo}}),
                hospedado_complementado=metricas(hosted),chamadas_complementares=n_extra,parede_s=time.monotonic()-t0)
    gravar(pasta/'pares_comparados.json',porpar);gravar(pasta/'metricas.json',result)
    print('Gate A concluído',json.dumps(result),flush=True)


def gate_b():
    import votacao_3 as V
    import verificador_impacto as VI
    pasta=OUT/'gate_b';pasta.mkdir(exist_ok=True)
    # Reaproveita toda a amostra publicada: comparar review×eixo exige o
    # mesmo universo, inclusive revisões anteriores com mais de 120 reviews.
    am=json.loads((ROOT/'resultado/votacao-3/amostra.json').read_text())
    am['reviews']=[r for r in am['reviews'] if r['slug'] in FILMES]
    am['filmes']=[r for r in am['filmes'] if (r if isinstance(r,str) else r['slug']) in FILMES]
    gravar(pasta/'amostra.json',am)
    V.SAIDA=pasta;V.ARQ_AMOSTRA=pasta/'amostra.json';V.ARQ_PASSE={n:pasta/f'passe_{n}.jsonl' for n in (1,2,3,4)}
    V.ARQ_CONSENSO=pasta/'consenso.jsonl'
    V.CONCORRENCIA=24;VI.CONCORRENCIA=24
    VI.ARQ_AMOSTRA_PRODUCAO=V.ARQ_AMOSTRA;VI.ARQ_PRODUCAO=pasta/'verificador.jsonl'
    VI.ARQ_CONSENSO_PRODUCAO=V.ARQ_CONSENSO
    original=ler(ROOT/'resultado/votacao-3/consenso_verificado.jsonl')
    assert all(not r.get('verificacao_pendente') for r in original if r['slug'] in FILMES)
    t0=time.monotonic()
    for n in (1,2,3):V.classificar_passe(n,slugs=FILMES,provider='featherless',modelo=DEEPSEEK)
    passes=[V._ler_passe(n) for n in (1,2,3)]
    chaves=sorted(set.intersection(*(set(p) for p in passes)))
    consenso=V._consensuar(passes,chaves)
    with V.ARQ_CONSENSO.open('w') as f:
        for r in consenso:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    if consenso:
        verificado,manifesto=VI.calcular_aplicacao(consenso,slugs=FILMES,provider='featherless',modelo=DEEPSEEK)
        gravar(pasta/'consenso_verificado.json',verificado);gravar(pasta/'manifesto.json',manifesto)
    else:verificado=[]
    # A métrica histórica de 65% exige a quarta passada: A=(1,2,3), B=(2,3,4).
    V.classificar_passe(4,slugs=FILMES,provider='featherless',modelo=DEEPSEEK)
    p4=V._ler_passe(4)
    common=sorted(set(chaves)&set(p4));a=V._consensuar(passes,common);b=V._consensuar([passes[1],passes[2],p4],common)
    old={(r['slug'],r['bucket'],r['id']):r for r in original}
    results={}
    for slug in FILMES:
        rs=[r for r in verificado if r['slug']==slug];cm=Counter();exact=0
        for r in rs:
            chave=(r['slug'],r['bucket'],r['id']);ref=old.get(chave)
            if ref is None:continue
            exact+=set(r['eixos'])==set(ref['eixos'])
            for eixo in V.EIXOS:cm[(int(eixo in ref['eixos']),int(eixo in r['eixos']))]+=1
        stab=[set(x['eixos'])==set(y['eixos']) for x,y in zip(a,b) if x['slug']==slug]
        regs=[r for n in (1,2,3) for r in ler(V.ARQ_PASSE[n]) if r['slug']==slug]
        results[slug]=dict(reviews_comparadas=len(rs),reviews_amostra=sum(r['slug']==slug for r in am['reviews']),
            concordancia_review_eixo=(cm[(0,0)]+cm[(1,1)])/sum(cm.values()) if cm else None,
            conjunto_identico=exact/len(rs) if rs else None,matriz=[[cm[(i,j)] for j in (0,1)] for i in (0,1)],
            estabilidade_consenso_123_vs_234=sum(stab)/len(stab) if stab else None,n_estabilidade=len(stab),
            falhas=sum(not r.get('ok') for r in regs),chamadas=len(regs),
            falhas_detalhe=dict(Counter(r.get('erro','').split(':')[0] for r in regs if not r.get('ok'))))
    gravar(pasta/'metricas.json',dict(filmes=results,parede_s=time.monotonic()-t0));print('Gate B concluído',flush=True)


def gate_c():
    from espectro24 import condicoes as C
    from espectro24.config import BEST_OF_N
    pasta=OUT/'gate_c';pasta.mkdir(exist_ok=True)
    # Só a chave separada conserva a identidade de cada versão.
    rng=random.Random(int.from_bytes(os.urandom(16),'big'))
    chave={};cego=['# Condições — leitura cega','', 'Quatro versões por filme, apresentadas na mesma formatação. Identifique fidelidade, clareza e utilidade; a aprovação mecânica não substitui a leitura.','']
    metricas=[];t0=time.monotonic()
    for slug in FILMES:
        pub=json.loads((ROOT/'resultado'/f'{slug}.json').read_text());assert pub.get('condicoes')
        versoes=[]
        for modelo in CANDIDATOS:
            destino=pasta/(slug+'__'+modelo.split('/')[-1]+'.json')
            if destino.exists():bloco=json.loads(destino.read_text())
            else:
                with F.contexto('gate_c',slug):
                    bloco=C.gerar(pub,n=BEST_OF_N,provider='featherless',model=modelo)
                gravar(destino,bloco)
            versoes.append((modelo,bloco))
            b=bloco or {};ped=sum(len(v) for v in (b.get('temas_pedidos') or {}).values())
            limpos=len(b.get('vale_a_pena') or [])+len(b.get('talvez_evite') or [])
            metricas.append(dict(slug=slug,modelo=modelo,pedidos=ped,aprovados=limpos,descartadas=len(b.get('descartadas') or []),recusas=len(b.get('sem_condicao_publicavel') or []),taxa_aprovacao=limpos/ped if ped else None))
        versoes.append(('Gemini_publicada',pub['condicoes']));rng.shuffle(versoes)
        chave[slug]={};cego+=['## '+slug,'']
        for label,(origem,b) in zip('ABCD',versoes):
            chave[slug][label]=origem
            cego+=['### Versão '+label,'']
            for campo,titulo in [('vale_a_pena','Vale a pena se'),('talvez_evite','Talvez evite se')]:
                cego += ['**'+titulo+'**','']
                for item in (b or {}).get(campo,[]):
                    texto=item.get('condicao') or item.get('texto') or item.get('frase') if isinstance(item,dict) else str(item)
                    cego += ['- '+str(texto)]
                if not (b or {}).get(campo):cego += ['Nenhuma condição aprovada.']
                cego += ['']
    gravar(pasta/'CHAVE_NAO_ABRIR.json',chave)
    (pasta/'LEITURA_CEGA.md').write_text('\n'.join(cego)+'\n')
    gravar(pasta/'metricas.json',dict(candidatos=metricas,parede_s=time.monotonic()-t0))
    print('Gate C concluído; chave omitida da saída',flush=True)

def custo_prosa():
    from espectro24.prosa_local import _buckets_do_bruto
    from espectro24.pipeline import ids_analisados_do_bruto, montar_eixos
    from espectro24.render import build_output
    from espectro24.config import LLM_MAX_TOKENS
    pasta=OUT/'custo_prosa';pasta.mkdir(exist_ok=True)
    client=F.client()
    for slug in FILMES:
        dest=pasta/(slug+'.json')
        if dest.exists():continue
        pub=json.loads((ROOT/'resultado'/f'{slug}.json').read_text())
        buckets=_buckets_do_bruto(slug,pub['coleta'],ROOT/'dados/bruto')
        for bucket in buckets:
            def chamar(system,user,model):
                resp=F.resposta(system,user,model,max_tokens=LLM_MAX_TOKENS,json_mode=True,client=client,estagio='sintese',slug=slug,bucket=bucket.nome)
                return resp.choices[0].message.content or ''
            S.synthesize_bucket(bucket,client_call=chamar,model=DEEPSEEK)
        out=build_output(slug,buckets,data_coleta=pub['data_coleta'],origens=pub['origem_paginas'],total_observado=pub['total_reviews_observadas'],ficha=pub['ficha'],distribuicao=None,coleta=pub['coleta'])
        out['distribuicao']=pub['distribuicao']
        analisadas=ids_analisados_do_bruto(slug,coleta=pub['coleta'],raiz=ROOT/'dados/bruto')
        def rotular(system,user,model):
            import re
            match=re.search(r'negativas|medianas|positivas',user)
            resp=F.resposta(system,user,model,max_tokens=LLM_MAX_TOKENS,json_mode=True,client=client,estagio='rotulagem',slug=slug,bucket=match.group() if match else None)
            return resp.choices[0].message.content or ''
        out['eixos']=montar_eixos(slug,out,analisadas,client_call=rotular,model=DEEPSEEK)
        assert 'narrativa' not in out and 'veredito' not in out
        gravar(dest,out)
        print('Medição de síntese/rotulagem',slug,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('gate',choices=['a','b','c','custos']);args=ap.parse_args();config()
    {'a':gate_a,'b':gate_b,'c':gate_c,'custos':custo_prosa}[args.gate]()
    print(F.sessao_ambiente().resumo())
