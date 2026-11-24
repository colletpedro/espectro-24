"""Consolida os gates sem LLM, preservando cegueira e denominadores."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import math
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from gates_featherless import OUT, FILMES, CANDIDATOS, DEEPSEEK, estados_juiz
from espectro24.featherless import custo_nano

def ler(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def salvar(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False))
def main():
    usos=ler(OUT/'uso.jsonl')
    assert all(r.get('custo_usd') is not None for r in usos)
    assert sum(r['custo_usd'] for r in usos)<=3
    # Nenhum resultado cego, bruto ou índice publicado foi alterado.
    hashes=json.loads((OUT/'invariantes_sha256.json').read_text())
    violacoes=[f for f,h in hashes.items() if not Path(f).exists() or hashlib.sha256(Path(f).read_bytes()).hexdigest()!=h]
    assert not violacoes,violacoes
    etapas={}
    for e in sorted({r['estagio'] for r in usos}):
        rs=[r for r in usos if r['estagio']==e]
        etapas[e]=dict(chamadas=len(rs),custo_usd=sum(r['custo_usd'] for r in rs),custo_api_usd=sum(r.get('custo_api_usd') or 0 for r in rs),entrada=sum(r['prompt_tokens'] for r in rs),saida_inclui_raciocinio=sum(r['completion_tokens'] for r in rs),duracao_acumulada_s=sum(r['duracao_s'] for r in rs))
    a=json.loads((OUT/'gate_a/metricas.json').read_text())
    entrada=ler(OUT/'gate_a/local_entrada.jsonl');local=ler(OUT/'gate_a/local_saida.jsonl');host=ler(OUT/'gate_a/hospedado.jsonl')
    ids={r['id_par'] for r in local}
    for nome,rs in [('hospedado_1600',[r for r in host if r['id_par'] in ids]),('hospedado_complementado',host)]:
        es=estados_juiz(entrada,{r['id_par']:r for r in rs});c=Counter(v['estado'] for v in es.values());n=len(es)-c['indeterminado'];pend=[v for v in es.values() if v['estado']=='pendente']
        a[nome]['C1_condicional']=a[nome]['C1_sem_apoio'];a[nome]['C2_condicional']=a[nome]['C2_apoio_2']
        a[nome]['C1_limites_534']=[c['sem_apoio']/n,(c['sem_apoio']+sum(v['sims']==0 for v in pend))/n]
        a[nome]['C2_limites_534']=[c['apoio_2']/n,(c['apoio_2']+len(pend))/n]
        a[nome]['C1_sem_apoio']=None if pend else c['sem_apoio']/n
        a[nome]['C2_apoio_2']=None if pend else c['apoio_2']/n
    a['falhas_1600']=sum(not r.get('ok') for r in host if r['id_par'] in ids)
    a['falhas_complementares']=sum(not r.get('ok') for r in host if r['id_par'] not in ids)
    a['concordancia_denominador_1600']=sum(r['concorda'] is True for r in json.loads((OUT/'gate_a/pares_comparados.json').read_text()))/1600
    a['equivalencia_demonstrada']=False
    a['limitacao_respostas_cruas']='As primeiras falhas de parse não conservaram o texto bruto no replay; uso e custo de todas as chamadas estão preservados. O harness foi corrigido para futuras execuções; nenhuma chamada foi refeita para reparar essa lacuna.'
    a['runtime']=dict(local_contexto=4096,hospedado_contexto_catalogo=131072,max_tokens=1024,seed=20261019,temperatura_enviada=1,temperatura_origem='padrão publicado do gpt-oss:20b na biblioteca Ollama; o artefato histórico registra apenas padrão do modelo, sem cópia dos parâmetros efetivos',reasoning_effort_enviado='low',confirmacao_reasoning_effort_efetivo='API não ecoa; enviado no campo padrão e chat_template_kwargs',quantizacao_local='MXFP4 segundo a biblioteca Ollama; sem digest histórico do runtime no arquivo recuperado',quantizacao_hospedada='endpoint de detalhe não informa; página oficial rotula FP8, mas descrição genérica cita MXFP4. Manifesto efetivo do servidor não é exposto',schema='mesmo schema v2.2 enviado como response_format=json_schema',seed_limite='Featherless documenta que seed não é confiável entre servidores')
    salvar(OUT/'gate_a/analise.json',a)
    # O eixo livre também faz parte do conjunto exato, como no histórico.
    import votacao_3 as V
    ref={(r['slug'],r['bucket'],r['id']):r for r in ler(ROOT/'resultado/votacao-3/consenso_verificado.jsonl')}
    novos=json.loads((OUT/'gate_b/consenso_verificado.json').read_text())
    byaxis={};totalcm=Counter()
    for eixo in V.EIXOS:
        cm=Counter((int(eixo in ref[(r['slug'],r['bucket'],r['id'])]['eixos']),int(eixo in r['eixos'])) for r in novos)
        byaxis[eixo]=dict(n=sum(cm.values()),concordancia=(cm[(0,0)]+cm[(1,1)])/sum(cm.values()),matriz=[[cm[(i,j)] for j in (0,1)] for i in (0,1)])
        totalcm.update(cm)
    b=json.loads((OUT/'gate_b/metricas.json').read_text());b['por_eixo']=byaxis
    b['agregado']=dict(reviews=len(novos),eixos=len(V.EIXOS),concordancia_review_eixo=(totalcm[(0,0)]+totalcm[(1,1)])/sum(totalcm.values()),matriz=[[totalcm[(i,j)] for j in (0,1)] for i in (0,1)],conjunto_identico=sum(set(r['eixos'])==set(ref[(r['slug'],r['bucket'],r['id'])]['eixos']) for r in novos)/len(novos))
    ps=[{(r['slug'],r['bucket'],r['id']):r for r in ler(OUT/f'gate_b/passe_{n}.jsonl') if r.get('ok')} for n in (1,2,3,4)]
    common=set.intersection(*(set(p) for p in ps));ca=V._consensuar(ps[:3],sorted(common));cb=V._consensuar(ps[1:],sorted(common))
    b['agregado']['estabilidade_consenso_123_234']=sum(set(x['eixos'])==set(y['eixos']) for x,y in zip(ca,cb))/len(common)
    b['agregado']['identico_passadas_1_2']=sum(set(ps[0][k]['eixos'])==set(ps[1][k]['eixos']) for k in common)/len(common)
    b['agregado']['historico_referencia']={'passada_unica':.265,'consenso':.65,'mesma_formula_mas_corpus_e_modelo_diferentes':True}
    salvar(OUT/'gate_b/analise.json',b)
    # Custos medidos por filme. A quarta passada é custo do gate, excluída
    # do preço de classificação de um filme futuro.
    filmes={};p4total=0;tokensp4=Counter()
    class_ordenadas=[r for r in usos if r['estagio']=='classificacao']
    assert len(class_ordenadas)==4*465
    p4_usos=class_ordenadas[3*465:]
    p123_usos=class_ordenadas[:3*465]
    for slug in FILMES:
        base=[r for r in usos if r['slug']==slug and r['estagio'] in ('sintese','rotulagem')]
        classes=[r for r in usos if r['slug']==slug and r['estagio'] in ('classificacao','verificador')]
        p4=[r for r in ps[3].values() if r['slug']==slug]
        p4cost=sum(r['custo_usd'] for r in p4_usos if r['slug']==slug);p4total+=p4cost
        for r in p4:tokensp4.update({k:r['uso'][k] for k in ('prompt_tokens','completion_tokens')})
        custo_class=sum(r['custo_usd'] for r in classes)-p4cost
        tempo_class=sum(r['duracao_s']*4 for r in p123_usos if r['slug']==slug)+sum(r['duracao_s']*4 for r in classes if r['estagio']=='verificador')
        casos={}
        for modelo in CANDIDATOS:
            cs=[r for r in usos if r['estagio']=='gate_c' and r['slug']==slug and r['modelo']==modelo]
            coberto=sum(r['custo_usd'] for r in base+cs)
            unidades=sum(r['duracao_s']*(2 if r['modelo'].startswith('Qwen/') else 4) for r in base+cs)
            casos[modelo]=dict(coberto_usd=coberto,sem_consenso_usd=coberto+custo_class,condicoes_usd=sum(r['custo_usd'] for r in cs),unidades_segundos_coberto=unidades,unidades_segundos_sem_consenso=unidades+tempo_class,entrada_condicoes=sum(r['prompt_tokens'] for r in cs),saida_condicoes=sum(r['completion_tokens'] for r in cs))
        filmes[slug]=dict(sintese_rotulagem_usd=sum(r['custo_usd'] for r in base),classificacao_3_verificador_usd=custo_class,quarta_passada_usd=p4cost,casos=casos,tokens_base={'entrada':sum(r['prompt_tokens'] for r in base),'saida':sum(r['completion_tokens'] for r in base)},tokens_classificacao_3_verificador={'entrada':sum(r['prompt_tokens'] for r in classes)-sum(r['uso']['prompt_tokens'] for r in p4),'saida':sum(r['completion_tokens'] for r in classes)-sum(r['uso']['completion_tokens'] for r in p4)})
    total=sum(r['custo_usd'] for r in usos);totalapi=sum(r.get('custo_api_usd') or 0 for r in usos)
    inicial=json.loads((OUT/'saldo_inicial.json').read_text());final=json.loads((OUT/'saldo_final.json').read_text())
    c=json.loads((OUT/'gate_c/metricas.json').read_text());gc={}
    for modelo in CANDIDATOS:
        rs=[r for r in c['candidatos'] if r['modelo']==modelo];u=[r for r in usos if r['estagio']=='gate_c' and r['modelo']==modelo]
        gc[modelo]=dict(pedidos=sum(r['pedidos'] for r in rs),aprovados=sum(r['aprovados'] for r in rs),taxa_aprovacao=sum(r['aprovados'] for r in rs)/sum(r['pedidos'] for r in rs),custo_usd=sum(r['custo_usd'] for r in u),chamadas=len(u))
        arquivos=[json.loads((OUT/'gate_c'/f'{s}__{modelo.split("/")[-1]}.json').read_text()) for s in FILMES]
        candidatos=[r for arq in arquivos for r in arq['candidatos']]
        gc[modelo]['candidatos_iniciais_sem_flags']=sum(r['n_flags']==0 for r in candidatos)
        gc[modelo]['n_candidatos_iniciais']=len(candidatos)
    ceg=(OUT/'gate_c/LEITURA_CEGA.md').read_text()
    assert ceg.count('### Versão ')==12
    assert all(m not in ceg for m in CANDIDATOS)
    assert 'Gemini' not in ceg and 'None' not in ceg
    saldo=float(final['available_usd']);projecoes={}
    for modelo in CANDIDATOS:
        casos={}
        for caso in ('coberto','sem_consenso'):
            media=statistics.mean(f['casos'][modelo][caso+'_usd'] for f in filmes.values())
            unit=statistics.mean(f['casos'][modelo]['unidades_segundos_'+caso] for f in filmes.values())
            capacidade=math.floor(saldo/media)
            casos[caso]=dict(custo_medio_usd=media,filmes_saldo_conta=capacidade,filmes_parcela_20_usd=math.floor((20-total)/media),capacidade_limitada_55=min(55,capacidade),minutos_55_ideal=55*unit/100/60,minutos_saldo_todo_ideal=capacidade*unit/100/60,nota='projeção linear do trabalho LLM medido, 100 unidades; não inclui coleta, ficha, aquecimento/troca de modelo e leitura humana; não é aprovação dos gates')
        projecoes[modelo]=casos
    resumo=dict(data='2026-11-08',etapas=etapas,passos_usd={'1_catalogo':0,'2_infraestrutura_testes':0,'3_gate_a':etapas['gate_a']['custo_usd'],'4_gate_b_3_verificador':etapas['classificacao']['custo_usd']+etapas['verificador']['custo_usd']-p4total,'4_quarta_passada_estabilidade':p4total,'5_gate_c':etapas['gate_c']['custo_usd'],'6_identidade':0,'7_narrativa':0,'8_medicao_sintese_rotulagem':etapas['sintese']['custo_usd']+etapas['rotulagem']['custo_usd']},gasto_livro_usd=total,gasto_api_usage_usd=totalapi,debito_saldo_usd=float(inicial['balance_usd'])-float(final['balance_usd']),saldo_final=final,delta_arredondamento_livro_api=total-totalapi,filmes=filmes,gate_c=gc,projecoes=projecoes,checks=dict(invariantes_preservadas=True,arquivos_conferidos=len(hashes),reserva_pendente_usd=0,pacote_cego_12_versoes=True))
    salvar(OUT/'medicoes.json',resumo)
    print(json.dumps({k:resumo[k] for k in ('passos_usd','gasto_livro_usd','gasto_api_usage_usd','debito_saldo_usd','gate_c','projecoes','checks')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
