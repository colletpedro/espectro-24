"""Encadeia Lista 3 ao driver existente, sem interrompê-lo.

python scripts/lista3_featherless.py preparar
nohup caffeinate -i -s venv/bin/python scripts/lista3_featherless.py rodar > execucoes/featherless-etapa2-2026-11-08/lista3/driver.log 2>&1 &
O caixa é o SQLite da Etapa 2, com a Etapa 1 importada e teto global de US$19.
"""
from __future__ import annotations
import argparse
import collections
from datetime import datetime,timezone,timedelta
import json
import math
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import etapa2_featherless as D
from lista3_catalogo import lista
from espectro24 import featherless as F
from espectro24.sessao_featherless import politica as politica_db
BASE=D.OUT
OUT=BASE/'lista3'
KIMI='moonshotai/Kimi-K3.1-Pro'
QWEN='Qwen/Qwen3.8-27B'


def log(*args): print(datetime.now(timezone.utc).isoformat(timespec='seconds'),*args,flush=True)
def vivo(pid,trecho):
    if not pid:return False
    r=subprocess.run(['ps','-p',str(pid),'-o','stat=','-o','command='],capture_output=True,text=True)
    return r.returncode==0 and not r.stdout.lstrip().startswith('Z') and trecho in r.stdout

def preparar():
    D.conferir();m=D.ler(BASE/'manifesto.json');rows=lista();esc=set(m['c22_slugs'])
    OUT.mkdir(parents=True,exist_ok=True)
    if not (OUT/'manifesto.json').exists():
        D.salvar(OUT/'manifesto.json',dict(lista=rows,quantidade=len(rows),c22_slugs=sorted(esc),
            cruzamento_c22_sugestoes=[r['sugestao'] for r in rows if r['sugestao'] in esc],
            supervisor_legado=D.ler(BASE/'pid.json')['pid'],coletor_legado=D.ler(BASE/'servicos.json')['coletor'],
            preregistro_sha256=D.sha(D.PREREG),escopo_sha256=D.sha(D.ESCOPO)))
    else: assert D.ler(OUT/'manifesto.json')['lista']==rows
    if not (OUT/'saldo_sessao_inicial.json').exists():D.salvar(OUT/'saldo_sessao_inicial.json',D.ler(ROOT/'resultado/featherless-etapa1-2026-11-08/saldo_inicial.json'))
    D.salvar(OUT/'estado.json',dict(estado='agendado',disparo='fim da coleta da Frente 2',preparacao_e5=False))
    diagnosticar_verificadores()
    log('Lista 3 preparada:',len(rows),'filmes; cruzamento inicial C22:',len(D.ler(OUT/'manifesto.json')['cruzamento_c22_sugestoes']))


def categoria_erro(erro):
    if any(s in erro for s in ('JSONDecodeError','json_invalido','ValueError','TypeError')):return 'JSON',False
    if any(s in erro.lower() for s in ('content exists risk','recusa','content_filter')):return 'recusa',False
    if any(s in erro for s in ('TetoExcedido','LLMSaldoEsgotado')):return 'teto',False
    if any(s in erro for s in ('Timeout','Connection','LLMIndisponivel','HTTP 5','InternalServerError','ServiceUnavailable')):return 'transporte',True
    return 'outro',False


def diagnosticar_verificadores():
    rows=[]
    for slug in ('logan-2017','how-to-make-millions-before-grandma-dies'):
        p=D.pasta(slug);es=D.ler(p/'estado.json');regs=D.linhas(p/'classificacao/verificador.jsonl')
        oks={r['id'] for r in regs if r.get('ok')};pend={r['id']:r for r in regs if not r.get('ok') and r['id'] not in oks}
        falhas=[]
        for r in pend.values():
            cat,trans=categoria_erro(r.get('erro',''))
            falhas.append(dict(categoria=cat,transitoria=trans,erro_tecnico=r.get('erro','').split(':')[0]))
        rows.append(dict(slug=slug,c22=es['c22'],estado=es['estado'],pendentes=len(pend),falhas=falhas,
                         acao='verificador pendente ao fim da Frente 2' if falhas and all(r['transitoria'] for r in falhas) else 'registrado; sem retentativa de conteúdo'))
    D.salvar(OUT/'diagnostico_verificadores.json',rows)
    return rows


def requisitos_identidade(item,ident):
    if item['ano'] not in {ident['letterboxd']['ano'],ident['tmdb_ano']}:raise ValueError('ano_da_lista_nao_confirmado')
    req=item.get('requisitos',{})
    if req.get('idioma') and ident.get('idioma_original')!=req['idioma']:raise ValueError('idioma_original_diverge_da_lista')
    if req.get('pais') and req['pais'] not in ident.get('paises',[]):raise ValueError('pais_diverge_da_lista')
    if req.get('genero') and req['genero'] not in ident.get('generos',[]):raise ValueError('genero_musical_nao_confirmado')


def resolver(fetcher,item):
    from espectro24 import pipeline as P
    from espectro24.fetcher import AntiBotError,SobrecargaError
    titulos=[item['titulo'],*item.get('aliases',[])]
    slugs=[item['sugestao']]
    for passo in (0,1):
        if passo:
            encontrados=P.resolve_slug(fetcher,item['titulo'])
            slugs += [r.slug for r in encontrados if r.year is not None and abs(r.year-item['ano'])<=1 and r.slug not in slugs]
        for slug in slugs[:6]:
            for titulo in titulos:
                try:
                    ident=D.identidade(fetcher,slug,titulo,item['ano']);requisitos_identidade(item,ident)
                    return slug,ident
                except (AntiBotError,SobrecargaError):raise
                except Exception:continue
    raise ValueError('identidade_nao_resolvida')


def proibidos():
    m=D.ler(BASE/'manifesto.json')
    s=set(D.ler(ROOT/'dados/publicados.json')['slugs'])|{r['slug'] for r in m['candidatos']}|{r['sugestao'] for r in m['novos']}
    s |= {r['slug'] for r in D.linhas(OUT/'resolvidos.jsonl') if r.get('slug')}
    s |= {r['slug'] for r in (D.ler(BASE/'coleta.json') if (BASE/'coleta.json').exists() else []) if r.get('slug')}
    s |= {r['slug'] for r in (D.ler(OUT/'coleta.json') if (OUT/'coleta.json').exists() else []) if r.get('slug')}
    return s


def conferir_pos_coleta(fetcher,slug,ident,bruto):
    from espectro24.ficha import extrair_identidade_letterboxd
    from espectro24.urls import film_page_url
    import shutil
    atual=extrair_identidade_letterboxd(fetcher.get(film_page_url(slug),f'{slug}/pos_lista3_{time.time_ns()}.html'),slug)
    if not atual or atual['tmdb_id_letterboxd']!=ident['tmdb_id']:
        q=OUT/'quarentena'/slug;q.parent.mkdir(parents=True,exist_ok=True)
        if q.exists():q=q.with_name(slug+'_'+str(time.time_ns()))
        shutil.move(str(bruto/slug),str(q))
        return False
    return True


def coletar_lista3():
    from espectro24.fetcher import Fetcher,AntiBotError,SobrecargaError
    from espectro24 import pipeline as P
    m=D.ler(OUT/'manifesto.json');pid=m['coletor_legado']
    log('Coleta Lista 3 aguardando PID da Frente 2:',pid)
    while vivo(pid,'etapa2_featherless.py coletar'):time.sleep(3)
    # O coletor legado não tinha este lock carregado; só o adquirimos após seu PID sair.
    with D.trava(BASE/'letterboxd_global.lock'):
        feitos2=D.ler(BASE/'coleta.json') if (BASE/'coleta.json').exists() else []
        if len(feitos2)<50 and not any(r['estado']=='coleta_bloqueada' for r in feitos2):
            log('Completando itens não tentados da coleta da Frente 2')
            D.coletar()
        elif any(r['estado']=='coleta_bloqueada' for r in feitos2):
            D.salvar(OUT/'coleta_concluida.json',dict(concluida=True,bloqueio_herdado=True))
            log('Lista 3 não coleta: bloqueio/sobrecarga sinalizado pela Frente 2');return
        D.salvar(OUT/'frente2_coleta_concluida.json',dict(concluida=True))
        log('Coleta da Frente 2 terminou; iniciando Lista 3')
        feitos=D.ler(OUT/'coleta.json') if (OUT/'coleta.json').exists() else []
        f=Fetcher(OUT/'cache',delay=2);f.cache_dir.mkdir(parents=True,exist_ok=True)
        for item in m['lista']:
            if any(r['prioridade']==item['prioridade'] for r in feitos):continue
            t=time.monotonic();row=dict(item,origem='lista3',estado='identidade_em_andamento')
            D.salvar(OUT/'coleta_em_andamento.json',row)
            try:
                slug,ident=resolver(f,item);row.update(slug=slug,c22=slug in m['c22_slugs'],identidade={k:v for k,v in ident.items() if k!='ficha'})
                if slug in proibidos():row['estado']='pulado_duplicidade'
                else:
                    p=D.pasta(slug);p.mkdir(parents=True,exist_ok=True);D.salvar(p/'identidade.json',ident)
                    bruto=OUT/'bruto';P.collect_all_levels(f,slug,dados_dir=bruto)
                    if not conferir_pos_coleta(f,slug,ident,bruto):row['estado']='quarentena'
                    else:
                        am={b:len(rs) for b,rs in P.amostra_do_bruto(slug,raiz=bruto).items()}
                        meta=D.ler(bruto/slug/'meta.json')
                        D.salvar(p/'estado.json',dict(slug=slug,origem='lista3',c22=row['c22'],grupo='sem_consenso',
                            estado='coletado_nao_gerado' if D.fim() else 'pendente',prioridade=item['prioridade'],
                            bruto_raiz=str(bruto),amostra=am,sem_kimi=True,coleta=meta.get('coletado_em')))
                        row.update(estado='coletado',amostra=am)
            except (AntiBotError,SobrecargaError) as e:
                row.update(estado='coleta_bloqueada',erro_tecnico=type(e).__name__,duracao_s=round(time.monotonic()-t,2))
                feitos.append(row);D.salvar(OUT/'coleta.json',feitos);log('Coleta',item['prioridade'],row.get('slug',item['sugestao']),row['estado'],row['erro_tecnico']);break
            except Exception as e:
                row.update(estado='falha_coleta' if row.get('identidade') else 'identidade_nao_resolvida',erro_tecnico=type(e).__name__)
            row['duracao_s']=round(time.monotonic()-t,2);feitos.append(row);D.salvar(OUT/'coleta.json',feitos)
            log('Coleta',item['prioridade'],row.get('slug',item['sugestao']),row['estado'],'segundos',row['duracao_s'])
        D.salvar(OUT/'coleta_concluida.json',dict(concluida=True,utc=datetime.now(timezone.utc).isoformat()))
        log('Coleta Lista 3 encerrada:',len(feitos),'itens processados')


def fila_ordenada():
    m=D.ler(BASE/'manifesto.json');result=[r['slug'] for r in m['candidatos']]
    for arq,originais in [(BASE/'coleta.json',m['novos']),(OUT/'coleta.json',D.ler(OUT/'manifesto.json')['lista'])]:
        co=D.ler(arq) if arq.exists() else []
        por={r['prioridade']:r for r in co if r['estado']=='coletado'}
        result += [por[r['prioridade']]['slug'] for r in originais if r['prioridade'] in por]
    return list(dict.fromkeys(result))


def estado_falha_nao_transitoria(s):
    es=D.ler(D.pasta(s)/'estado.json')
    if es.get('estado')!='falha':return False
    if (D.pasta(s)/'classificacao/verificador.jsonl').exists():
        regs=D.linhas(D.pasta(s)/'classificacao/verificador.jsonl');ok={r['id'] for r in regs if r.get('ok')}
        erros=[r.get('erro','') for r in regs if not r.get('ok') and r['id'] not in ok]
        if erros and any(not categoria_erro(e)[1] for e in erros):return True
    for f in (D.pasta(s)/'classificacao').glob('passe_*.jsonl'):
        regs=D.linhas(f);ok={r['id'] for r in regs if r.get('ok')}
        if any(not categoria_erro(r.get('erro',''))[1] for r in regs if not r.get('ok') and r['id'] not in ok):return True
    return False


def verificar_pendente(slug):
    # Só o verificador: nenhuma função de classificação é chamada aqui.
    import verificador_impacto as VI
    d=D.pasta(slug)/'classificacao'
    VI.ARQ_AMOSTRA_PRODUCAO=d/'amostra.json';VI.ARQ_PRODUCAO=d/'verificador.jsonl';VI.ARQ_CONSENSO_PRODUCAO=d/'consenso.jsonl'
    VI.CONCORRENCIA=20
    ver,man=VI.calcular_aplicacao(D.linhas(d/'consenso.jsonl'),slugs=[slug],provider='featherless',modelo=D.DS)
    if man['n_falharam']:return False
    assert not any(r.get('verificacao_pendente') for r in ver)
    D.jsonl(d/'consenso_verificado.jsonl',ver);D.salvar(d/'manifesto.json',man)
    es=D.ler(D.pasta(slug)/'estado.json');es.update(estado='verificador_concluido_aguarda_frente2',verificador_retificado=True)
    es.pop('erro',None);D.salvar(D.pasta(slug)/'estado.json',es)
    return True


def executar_worker(modo,slug):
    p=D.pasta(slug)
    if modo=='gerar':args=[sys.executable,str(ROOT/'scripts/etapa2_featherless.py'),'gerar','--slug',slug]
    else:args=[sys.executable,str(Path(__file__).resolve()),modo,'--slug',slug]
    with (p/'execucao.log').open('a') as f:
        proc=subprocess.Popen(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    while proc.poll() is None:
        if D.fim():D.encerrar(proc);return 'prazo'
        time.sleep(1)
    return proc.returncode


def projetar_kimi():
    with F.sessao_ambiente().db() as db:
        registros=[json.loads(r[0]) for r in db.execute('SELECT registro FROM chamadas WHERE registro IS NOT NULL')]
    custos=collections.defaultdict(float)
    for r in registros:
        if r.get('estagio')=='condicoes' and r.get('modelo')==KIMI and r.get('custo_usd') is not None: custos[r['slug']]+=r['custo_usd']
    valores=sorted(v for v in custos.values() if v>0)
    unit=valores[min(len(valores)-1,math.ceil(.95*len(valores))-1)] if valores else 0.20
    # Reserva de segurança de 50% sobre o p95 medido, sem estimar desconto de cache.
    unit*=1.5
    caixa=F.sessao_ambiente().resumo();livre=max(0,19-caixa['custo_usd']-caixa['reservas_pendentes_usd'])
    faltam=[s for s in fila_ordenada() if D.ler(D.pasta(s)/'estado.json')['estado']=='gerado' and not (D.pasta(s)/'condicoes/Kimi-K3.1-Pro/condicoes.json').exists()]
    plano=dict(custo_projetado_unitario_usd=unit,saldo_livre_usd=livre,pendentes=len(faltam),quantidade_projetada=min(len(faltam),int(livre/unit)) if unit else 0)
    D.salvar(OUT/'plano_kimi.json',plano)
    return faltam[:plano['quantidade_projetada']]


def gerar_kimi(slug):
    from espectro24 import condicoes as C
    from espectro24.config import BEST_OF_N
    p=D.pasta(slug)
    with D.trava(p/'geracao.lock'):
        estado=D.ler(p/'estado.json');assert estado['estado']=='gerado'
        dest=p/'condicoes/Kimi-K3.1-Pro/condicoes.json'
        if not dest.exists():
            doc=D.ler(p/'bullets.json');ch=D.Chamador(p,slug)
            D.salvar(dest,C.gerar(doc,n=BEST_OF_N,provider='featherless',model=KIMI,gerar=ch.condicoes(KIMI)))
        estado['validadores_condicoes'][KIMI]=D.validar_condicoes(D.ler(p/'bullets.json'),D.ler(dest))
        estado['sem_kimi']=False;estado['condicoes_geradas']=[m for m in D.MODELOS if (p/'condicoes'/m.split('/')[-1]/'condicoes.json').exists()]
        D.salvar(p/'estado.json',estado)


def situacao_coletas():
    m2=D.ler(BASE/'manifesto.json');m3=D.ler(OUT/'manifesto.json')
    r2=D.ler(BASE/'coleta.json') if (BASE/'coleta.json').exists() else []
    r3=D.ler(OUT/'coleta.json') if (OUT/'coleta.json').exists() else []
    marco=D.ler(OUT/'coleta_concluida.json') if (OUT/'coleta_concluida.json').exists() else {}
    bloqueio=bool(marco.get('bloqueio_herdado')) or any(r['estado']=='coleta_bloqueada' for r in r2+r3)
    completas=(BASE/'coleta_concluida.json').exists() and (OUT/'coleta_concluida.json').exists() and not bloqueio
    completas=completas and {r['prioridade'] for r in r2}=={r['prioridade'] for r in m2['novos']} and {r['prioridade'] for r in r3}=={r['prioridade'] for r in m3['lista']}
    return dict(bloqueio=bloqueio,frente2_tentados=len(r2),frente2_total=len(m2['novos']),lista3_tentados=len(r3),lista3_total=len(m3['lista']),coletas_completas=bool(completas))


def fila_llm():
    legado=D.ler(OUT/'manifesto.json')['supervisor_legado'];log('Fila LLM aguardando supervisor atual PID',legado)
    while vivo(legado,'etapa2_featherless.py rodar') and not D.fim():time.sleep(3)
    log('Supervisor atual terminou; assumindo fila restante na ordem Frente 1 → Frente 2 → Lista 3')
    feitos=set(D.ler(OUT/'tentados_llm.json')) if (OUT/'tentados_llm.json').exists() else set()
    # Reparos transitórios ficam depois de toda a Frente 2, conforme autorização.
    reparos=[]
    for r in diagnosticar_verificadores():
        if r['pendentes'] and r['falhas'] and all(f['transitoria'] for f in r['falhas']):reparos.append(r['slug'])
    while not D.fim():
        caixa=F.sessao_ambiente().resumo()
        if caixa['custo_usd']+caixa['reservas_pendentes_usd']>=19:break
        fila=fila_ordenada()
        pend=[s for s in fila if s not in feitos and s not in reparos and D.ler(D.pasta(s)/'estado.json')['estado']!='gerado' and not estado_falha_nao_transitoria(s)]
        # Não permitir Lista 3 à frente de um reparo transitório da Frente 1 já postergado ao fim da Frente 2.
        frente2_fim=(OUT/'frente2_coleta_concluida.json').exists() and not any(D.ler(D.pasta(s)/'estado.json').get('origem')=='novo' for s in pend)
        if reparos and frente2_fim:
            s=reparos.pop(0);rc=executar_worker('verificar',s)
            if rc==0:pend.insert(0,s)
            else:feitos.add(s)
        if not pend:
            if (OUT/'coleta_concluida.json').exists():break
            time.sleep(3);continue
        s=pend[0];rc=executar_worker('gerar',s)
        if rc=='prazo':break
        feitos.add(s);D.salvar(OUT/'tentados_llm.json',sorted(feitos))
        es=D.ler(D.pasta(s)/'estado.json');log('LLM',s,es['estado'],'sem Kimi',es.get('sem_kimi',False))
        if es.get('erro')=='TetoExcedido':break
    # Kimi só depois de concluir a coleta e a fila base, nunca disputa com DS/Qwen.
    base_pendente=[s for s in fila_ordenada() if D.ler(D.pasta(s)/'estado.json')['estado'] not in ('gerado','falha')]
    if not D.fim() and situacao_coletas()['coletas_completas'] and not base_pendente:
        for s in projetar_kimi():
            if D.fim():break
            rc=executar_worker('kimi',s)
            if rc=='prazo' or rc!=0:break
            log('Kimi final',s,'concluído')
    for s in fila_ordenada():
        p=D.pasta(s);es=D.ler(p/'estado.json')
        if es['estado'] in ('pendente','em_andamento','interrompido'):
            es['estado']='coletado_nao_gerado' if es['origem']!='candidato' else 'nao_gerado';D.salvar(p/'estado.json',es)
    try:D.salvar(OUT/'saldo_ao_parar_llm.json',D.conta('credits/balance'))
    except Exception:pass
    D.salvar(OUT/'llm_concluido.json',dict(concluido=True,motivo='bloqueio_letterboxd' if situacao_coletas()['bloqueio'] else 'fila_paga_encerrada',utc=datetime.now(timezone.utc).isoformat(),caixa=F.sessao_ambiente().resumo()))
    log('Fila paga encerrada; coleta HTTP pode continuar')


def registros_caixa():
    with F.sessao_ambiente().db() as db:return [json.loads(r[0]) for r in db.execute('SELECT registro FROM chamadas WHERE registro IS NOT NULL')]


def linhas_relatorio():
    m=D.ler(BASE/'manifesto.json');metas=[('frente1',m['candidatos'],None),('frente2',m['novos'],BASE/'coleta.json'),('lista3',D.ler(OUT/'manifesto.json')['lista'],OUT/'coleta.json')]
    rows=[]
    for origem,itens,arq in metas:
        co=D.ler(arq) if arq and arq.exists() else []
        por={r['prioridade']:r for r in co}
        for item in itens:
            c=por.get(item.get('prioridade'),{}) if arq else {}
            slug=c.get('slug') or item.get('slug') or item['sugestao'];p=D.pasta(slug)
            es=D.ler(p/'estado.json') if (p/'estado.json').exists() and c.get('estado') not in ('pulado_duplicidade','pulado_existente') else {}
            row=dict(slug=slug,origem=origem,c22=slug in m['c22_slugs'],amostra=es.get('amostra',c.get('amostra',{})),
                estado=es.get('estado',c.get('estado','nao_coletado')),classificacao=es.get('classificacao','existente' if es.get('grupo')=='coberto' else 'nova' if es.get('grupo') else 'não executada'),
                validadores_bullets=es.get('validadores_bullets',{}),validadores_condicoes=es.get('validadores_condicoes',{}),
                sem_kimi=not (p/'condicoes/Kimi-K3.1-Pro/condicoes.json').exists(),erro=es.get('erro') or c.get('erro_tecnico') or c.get('erro'),
                degradacao=es.get('degradacao',{}))
            if row['estado'] in ('pendente','interrompido') and (OUT/'llm_concluido.json').exists() and origem!='frente1':row['estado']='coletado_nao_gerado'
            rows.append(row)
    return rows


def relatorio(final=False):
    rows=linhas_relatorio();regs=registros_caixa();custos=collections.defaultdict(float)
    for r in regs: custos[r.get('slug')]+=r.get('custo_usd') or 0
    for r in rows:r['custo_usd']=0 if r['estado'] in ('pulado_duplicidade','pulado_existente') else custos[r['slug']]
    caixa=F.sessao_ambiente().resumo()
    saldo=None
    try:saldo=D.conta('credits/balance');D.salvar(OUT/'saldo_atual.json',saldo)
    except Exception:pass
    fim_pago=D.ler(OUT/'saldo_ao_parar_llm.json') if (OUT/'saldo_ao_parar_llm.json').exists() else saldo
    ini=D.ler(OUT/'saldo_sessao_inicial.json');debito=float(ini['balance_usd'])-float(fim_pago['balance_usd']) if fim_pago else None
    co2=D.ler(BASE/'coleta.json') if (BASE/'coleta.json').exists() else []
    ts=[r['duracao_s'] for r in co2 if r.get('duracao_s') is not None and r['estado']!='pulado_existente'];media=sum(ts)/len(ts) if ts else None
    proj=dict(tentativas_medidas=len(ts),tempos_por_filme=[dict(prioridade=r['prioridade'],slug=r.get('slug',r['sugestao']),estado=r['estado'],segundos=r.get('duracao_s')) for r in co2],media_s=media,
        restantes=50-len(co2),cabem_tentar_ate_parada=min(50-len(co2),int(max(0,D.PRAZO-time.time())/media)) if media else None,
        fim_estimado_recife=(datetime.now(timezone.utc)+timedelta(seconds=media*(50-len(co2)))).astimezone(timezone(timedelta(hours=-3))).isoformat() if media else None)
    coletas=situacao_coletas()
    if coletas['bloqueio']:
        proj.update(situacao='bloqueada',cabem_tentar_ate_parada=0,fim_estimado_recife=None,projecao_suspensa=True)
    try:D.conferir();invariantes=True
    except AssertionError:invariantes=False
    rep=dict(final=final,motivo_encerramento='bloqueio_letterboxd' if coletas['bloqueio'] else None,situacao_coletas=coletas,desvios=D.ler(OUT/'desvios.json') if (OUT/'desvios.json').exists() else [],gerados=sum(r['estado']=='gerado' for r in rows),filmes=rows,caixa=caixa,debito_sessao_usd=debito,delta_conta_livro_usd=debito-caixa['custo_usd'] if debito is not None else None,
        reservas_incertas_incluidas=True,saldo=saldo,projecao_frente2=proj,
        diagnostico_verificadores=D.ler(OUT/'diagnostico_verificadores.json'),
        nao_coletados=[r for r in rows if r['estado'] in ('nao_coletado','identidade_nao_resolvida','identidade_ou_coleta_falhou','falha_coleta','quarentena','coleta_bloqueada')],
        coletados_nao_gerados=[r for r in rows if r['origem']!='frente1' and r['estado'] in ('coletado_nao_gerado','pendente','em_andamento','interrompido','falha')],
        duplicidades=[r for r in rows if r['estado'] in ('pulado_duplicidade','pulado_existente')],invariantes_preservadas=invariantes,
        commits=D.ler(BASE/'commits.json') if (BASE/'commits.json').exists() else [])
    D.salvar(OUT/'relatorio_sessao.json',rep)
    md=['# Sessão Featherless — '+('final' if final else 'andamento'),'',
        f"Gerados: {sum(r['estado']=='gerado' for r in rows)}. Caixa total Etapas 1 + 2 + Lista 3: US$ {caixa['custo_usd']:.6f}; reservas US$ {caixa['reservas_pendentes_usd']:.6f}; teto US$ 19.",
        f"Débito medido da conta: {debito}. Diferença conta − livro confirmado: {rep['delta_conta_livro_usd']}. Cobranças incertas continuam reservadas; a diferença não é apagada nem atribuída sem evidência.",
        f"Invariantes preservadas: {invariantes}. Parada paga: 08/11/2026 às 21h Recife. Coleta HTTP pode continuar.",
        '', 'Situação das coletas: '+json.dumps(coletas,ensure_ascii=False),
        'Parada por detecção de bloqueio anti-bot; as listas não foram integralmente tentadas.' if coletas['bloqueio'] else '',
        'Desvios registrados: '+json.dumps(rep['desvios'],ensure_ascii=False),
        '', 'Escopo C22: '+', '.join(D.ler(BASE/'manifesto.json')['c22_slugs']), '',
        '|Filme|Origem|C22|H/M/F|Classificação|Bullets passam/avaliados|DS / Qwen / Kimi: condições; flags; descartadas|US$ confirmado|Estado e pendências|',
        '|---|---|---|---|---|---|---|---:|---|']
    for r in rows:
        vs=[v for v in r['validadores_bullets'].values() if v.get('passa_publicado') is not None];conds=r['validadores_condicoes']
        cs=[';'.join(str(conds[m][k]) for k in ('aprovadas','flags','descartadas')) if m in conds else ('sem Kimi' if m==KIMI else 'pendente') for m in (D.DS,QWEN,KIMI)]
        am=r['amostra'];pend=r['estado']+(' / sem Kimi' if r['sem_kimi'] else '')+(' / '+r['erro'] if r['erro'] else '')+(' / amostra reduzida: '+','.join(r['degradacao']) if r['degradacao'] else '')
        md.append('|'+ '|'.join([r['slug'],r['origem'],'s' if r['c22'] else 'n','/'.join(str(am.get(b,'—')) for b in ('negativas','medianas','positivas')),r['classificacao'],f"{sum(v['passa_publicado'] for v in vs)}/{len(vs)}",' / '.join(cs),f"{r['custo_usd']:.6f}",pend])+'|')
    md += ['', 'Verificadores pendentes: '+json.dumps(rep['diagnostico_verificadores'],ensure_ascii=False), '', 'Projeção Frente 2: '+json.dumps(proj,ensure_ascii=False), '', 'Commits de código: '+str(rep['commits'])]
    for campo,titulo in [('duplicidades','Pulados por duplicidade'),('nao_coletados','Sem coleta concluída / identidade / quarentena'),('coletados_nao_gerados','Coletados, não gerados')]:
        md+=['',titulo+':']+[f"- {r['origem']}: {r['slug']} — {r['estado']} {r.get('erro') or ''}" for r in rep[campo]]
    D.escrever_atomico(BASE/'RELATORIO_SESSAO.md','\n'.join(md)+'\n')
    return rep


def spawn(modo,slug=None):
    args=[sys.executable,str(Path(__file__).resolve()),modo]+(['--slug',slug] if slug else [])
    with (OUT/'driver.log').open('a') as f:return subprocess.Popen(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)


def rodar():
    with D.trava(OUT/'encadeador.lock'):
        D.salvar(OUT/'pid.json',dict(pid=os.getpid(),utc=datetime.now(timezone.utc).isoformat()))
        co=spawn('coletar');llm=spawn('llm')
        D.salvar(OUT/'processos.json',dict(encadeador=os.getpid(),coletor=co.pid,llm=llm.pid))
        ultimo=0
        while co.poll() is None or llm.poll() is None:
            if time.monotonic()-ultimo>60:
                try:rep=relatorio();D.salvar(OUT/'estado.json',dict(estado='rodando',gerados=sum(r['estado']=='gerado' for r in rep['filmes']),caixa=rep['caixa'],coleta_pid=co.pid,llm_pid=llm.pid))
                except Exception as e:log('Relatório provisório:',type(e).__name__)
                ultimo=time.monotonic()
            time.sleep(2)
        # Deixa o supervisor legado concluir seus últimos arquivos antes do relatório final.
        while vivo(D.ler(OUT/'manifesto.json')['supervisor_legado'],'etapa2_featherless.py rodar'):time.sleep(2)
        rep=relatorio(final=True)
        (BASE/'rodar_juiz_windows.ps1').unlink(missing_ok=True)
        D.salvar(OUT/'encerrado.json',dict(motivo=rep['motivo_encerramento'],utc=datetime.now(timezone.utc).isoformat(),coleta_rc=co.returncode,llm_rc=llm.returncode,caixa=rep['caixa']))
        D.salvar(OUT/'estado.json',dict(estado='encerrado_por_bloqueio' if rep['motivo_encerramento']=='bloqueio_letterboxd' else 'encerrado',motivo=rep['motivo_encerramento'],caixa=rep['caixa']))
        log('Sessão interrompida por bloqueio. Relatório:' if rep['motivo_encerramento']=='bloqueio_letterboxd' else 'Sessão encerrada. Relatório final:',str(BASE/'RELATORIO_SESSAO.md'))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('modo',choices=['preparar','rodar','coletar','llm','kimi','verificar','relatorio']);ap.add_argument('--slug');a=ap.parse_args();D.config()
    if a.modo=='preparar':preparar()
    elif a.modo=='rodar':rodar()
    elif a.modo=='coletar':coletar_lista3()
    elif a.modo=='llm':fila_llm()
    elif a.modo=='relatorio':relatorio(final=(OUT/'encerrado.json').exists())
    else:
        try:
            if a.modo=='kimi':gerar_kimi(a.slug)
            elif not verificar_pendente(a.slug):raise RuntimeError('verificador_ainda_pendente')
        except Exception as e:
            log(a.modo,a.slug,'falhou',type(e).__name__);raise SystemExit(1)

if __name__=='__main__':main()
