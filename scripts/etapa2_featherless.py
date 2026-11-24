"""Execução isolada e retomável das duas frentes autorizadas em 08/11/2026.

python scripts/etapa2_featherless.py preparar
python scripts/etapa2_featherless.py rodar
python scripts/etapa2_featherless.py relatorio
Nenhum comando publica. Logs de subprocessos permanecem no diretório do filme.
"""
from __future__ import annotations
import argparse
import collections
import contextlib
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import unicodedata
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from espectro24.atomico import escrever_atomico
from espectro24 import featherless as F

OUT = ROOT/'execucoes/featherless-etapa2-2026-11-08'
PREREG = ROOT.parent/'espectro-24-finetune/finetune/PREREGISTRO_C22.md'
ESCOPO = PREREG.parent/'c22/escopo.json'
PRAZO = datetime(2026, 11, 9, tzinfo=timezone.utc).timestamp()
DS = 'deepseek-ai/DeepSeek-V4.1-Flash-1017'
MODELOS = [DS, 'moonshotai/Kimi-K3.1-Pro', 'Qwen/Qwen3.8-27B']
# A sugestão de slug nunca é prova: página Letterboxd + TMDB são obrigatórios.
NOVOS = [
('The Shawshank Redemption',1994,'the-shawshank-redemption'),
('The Godfather Part II',1974,'the-godfather-part-ii'),
('The Lord of the Rings: The Fellowship of the Ring',2001,'the-lord-of-the-rings-the-fellowship-of-the-ring'),
('The Lord of the Rings: The Two Towers',2002,'the-lord-of-the-rings-the-two-towers'),
('The Lord of the Rings: The Return of the King',2003,'the-lord-of-the-rings-the-return-of-the-king'),
("Schindler's List",1993,'schindlers-list'),('Pulp Fiction',1994,'pulp-fiction'),
('Forrest Gump',1994,'forrest-gump'),('The Matrix',1999,'the-matrix'),
("One Flew Over the Cuckoo's Nest",1975,'one-flew-over-the-cuckoos-nest'),
("It's a Wonderful Life",1946,'its-a-wonderful-life'),('The Silence of the Lambs',1991,'the-silence-of-the-lambs'),
('Seven Samurai',1954,'seven-samurai'),('The Green Mile',1999,'the-green-mile'),
('Life Is Beautiful',1997,'life-is-beautiful'),('Terminator 2: Judgment Day',1991,'terminator-2-judgment-day'),
('Back to the Future',1985,'back-to-the-future'),('Star Wars: Episode IV – A New Hope',1977,'star-wars'),
('Spirited Away',2001,'spirited-away'),('The Pianist',2002,'the-pianist'),
('Grave of the Fireflies',1988,'grave-of-the-fireflies'),('Harakiri',1962,'harakiri'),
('The Lion King',1994,'the-lion-king'),('Psycho',1960,'psycho'),('The Departed',2006,'the-departed'),
('American History X',1998,'american-history-x'),('Cinema Paradiso',1988,'cinema-paradiso'),
('Léon: The Professional',1994,'leon-the-professional'),('Casablanca',1942,'casablanca'),
('The Intouchables',2011,'the-intouchables'),('The Usual Suspects',1995,'the-usual-suspects'),
('Alien',1979,'alien'),('Rear Window',1954,'rear-window'),('Modern Times',1936,'modern-times'),
('Once Upon a Time in the West',1968,'once-upon-a-time-in-the-west'),('WALL·E',2008,'wall-e'),
('City Lights',1931,'city-lights'),('Apocalypse Now',1979,'apocalypse-now'),
('Avengers: Infinity War',2018,'avengers-infinity-war'),('Raiders of the Lost Ark',1981,'raiders-of-the-lost-ark'),
('The Lives of Others',2006,'the-lives-of-others'),('The Odyssey',2026,'the-odyssey-2026'),
('Sunset Boulevard',1950,'sunset-boulevard'),('Witness for the Prosecution',1957,'witness-for-the-prosecution'),
('Paths of Glory',1957,'paths-of-glory'),('The Shining',1980,'the-shining'),
('The Great Dictator',1940,'the-great-dictator'),('Aliens',1986,'aliens'),
('Good Will Hunting',1997,'good-will-hunting'),
('Eternal Sunshine of the Spotless Mind',2004,'eternal-sunshine-of-the-spotless-mind')]


def ler(p): return json.loads(Path(p).read_text())
def linhas(p): return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()] if Path(p).exists() else []
def salvar(p, d):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    escrever_atomico(p, json.dumps(d, ensure_ascii=False, indent=2)+'\n')
def jsonl(p, rs): escrever_atomico(Path(p), ''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rs))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def config():
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    os.environ.update(FEATHERLESS_SESSION_DIR=str(OUT), FEATHERLESS_TETO_USD='15.00',
                      FEATHERLESS_ETAPA='2', FEATHERLESS_PRAZO_UTC=str(PRAZO))
def politica_sessao():
    p=OUT/'sessao_politica.json'
    return ler(p) if p.exists() else {}

def modelos_obrigatorios():
    return politica_sessao().get('condicoes_obrigatorias',MODELOS)


def fim(): return time.time() >= PRAZO
def pasta(slug):
    man = ler(OUT/'manifesto.json')
    return OUT/('lacrado_c22' if slug in man['c22_slugs'] else 'aberto')/slug

def conta(endpoint):
    import requests
    r = requests.get('https://api.featherless.ai/'+endpoint,
                     headers={'Authorization':'Bearer '+os.environ['FEATHERLESS_API_KEY']}, timeout=30)
    r.raise_for_status(); return r.json()

def preparar():
    if (OUT/'manifesto.json').exists():
        conferir(); return
    from espectro24 import eixos as E, pipeline as P
    from espectro24.lote import ler_lista_slugs
    assert PREREG.exists() and ESCOPO.exists()
    # Conferência com o hash declarado no próprio pré-registro.
    marca = next(l for l in PREREG.read_text().splitlines() if l.startswith('<!-- preregistro_c22 '))
    assert sha(ESCOPO) == json.loads(marca[len('<!-- preregistro_c22 '):-4])['escopo_sha256']
    escopo = {r['slug'] for r in ler(ESCOPO)['incluidos']}
    candidatos = ler_lista_slugs(ROOT/'dados/lote/lista-noturno-2026-09-18.txt')
    assert len(candidatos) == 55 and len(escopo) == 35
    cat = E.carregar_classificacao(ROOT/'resultado/votacao-3/consenso_verificado.jsonl')
    rows=[]
    for s in candidatos:
        am = P.ids_analisados_do_bruto(s)
        status='sem_consenso'
        if s in cat:
            try: E.checar_amostra_classificada(cat[s], am); status='coberto'
            except ValueError: status='corpus_pendente'
        rows.append(dict(slug=s, origem='candidato', c22=s in escopo, grupo=status,
                         amostra={k:len(v) for k,v in am.items()}, estado='pendente'))
    assert collections.Counter(r['grupo'] for r in rows) == dict(coberto=35, corpus_pendente=5, sem_consenso=15)
    assert {r['slug'] for r in rows if r['grupo']=='coberto'} == escopo
    protegidos=[ROOT/'dados/publicados.json', *ROOT.glob('resultado/*.json'),
                *ROOT.glob('resultado/votacao-3/*.*')]
    protegidos += [p for s in candidatos for p in (ROOT/'dados/bruto'/s).glob('*') if p.is_file()]
    OUT.mkdir(parents=True, exist_ok=True)
    salvar(OUT/'invariantes.json', {str(p):sha(p) for p in protegidos if p.is_file()})
    salvar(OUT/'plano.json', conta('v1/plan'))
    salvar(OUT/'saldo_inicial.json', conta('credits/balance'))
    salvar(OUT/'manifesto.json', dict(c22_slugs=sorted(escopo), preregistro=str(PREREG),
        preregistro_sha256=sha(PREREG), escopo_sha256=sha(ESCOPO), prazo_recife='2026-11-08T21:00:00-03:00',
        prazo_utc=PRAZO, teto_usd=15, modelos=MODELOS, candidatos=rows,
        novos=[dict(prioridade=i+1,titulo=t,ano=a,sugestao=s,c22_sugestao=s in escopo) for i,(t,a,s) in enumerate(NOVOS)]))
    F.sessao_ambiente()
    for r in rows:
        p=pasta(r['slug']); p.mkdir(parents=True,exist_ok=True); salvar(p/'estado.json',r)
    (OUT/'lacrado_c22').chmod(0o700)
    salvar(OUT/'estado.json',dict(estado='preparado', inicio_utc=datetime.now(timezone.utc).isoformat()))
    print('Preparado: 55 candidatos; C22 35; novos 50; teto US$15; parada 21h Recife.',flush=True)

def conferir():
    m=ler(OUT/'manifesto.json')
    assert m['modelos']==MODELOS and m['prazo_utc']==PRAZO and m['teto_usd']==15
    assert sha(PREREG)==m['preregistro_sha256'] and sha(ESCOPO)==m['escopo_sha256']
    alterados=[p for p,h in ler(OUT/'invariantes.json').items() if not Path(p).exists() or sha(p)!=h]
    assert not alterados, 'entradas protegidas alteradas: '+','.join(alterados)

class Chamador:
    """Checkpoint por chamada; réplicas idênticas usam ordinais distintos."""
    def __init__(self,p,slug): self.p=p; self.slug=slug; self.n=collections.Counter()
    def chamar(self,system,user,model,estagio,max_tokens):
        from espectro24 import synthesize as S
        base=hashlib.sha256(json.dumps([system,user,model,estagio,max_tokens],ensure_ascii=False).encode()).hexdigest()
        n=self.n[base]; self.n[base]+=1
        path=self.p/'chamadas'/f'{base}_{n}.json'
        if path.exists(): return ler(path)
        resp=F.resposta(system,user,model,max_tokens=max_tokens,json_mode=True,estagio=estagio,slug=self.slug)
        assert resp.model==model, 'modelo efetivo diverge do autorizado'
        d=dict(texto=resp.choices[0].message.content or '',uso=S.uso(resp,'featherless'),modelo=resp.model)
        salvar(path,d); return d
    def texto(self,estagio):
        from espectro24.config import LLM_MAX_TOKENS
        return lambda system,user,model: self.chamar(system,user,model,estagio,LLM_MAX_TOKENS)['texto']
    def condicoes(self,modelo):
        from espectro24.config import PROSA_MAX_TOKENS
        def gerar(system,user):
            t=time.monotonic();d=self.chamar(system,user,modelo,'condicoes',PROSA_MAX_TOKENS)
            return d['texto'],d['uso'],time.monotonic()-t
        return gerar


def classificar(slug,p,am):
    import votacao_3 as V
    import verificador_impacto as VI
    from espectro24.taxonomia import taxonomia_id, EIXOS
    d=p/'classificacao';d.mkdir(exist_ok=True)
    n={b:len(rs) for b,rs in am.items()}
    # A seleção atual é reconciliada inteira; nenhum voto antigo entra.
    salvar(d/'amostra.json',dict(taxonomia_id=taxonomia_id(),taxonomia=list(EIXOS),
        filmes=[dict(slug=slug,perfil='etapa2',n_por_bucket=n)],
        reviews=[dict(slug=slug,perfil='etapa2',bucket=b,id=r.id,nivel=r.nivel,n_chars=r.n_chars,texto=r.texto)
                 for b,rs in am.items() for r in rs]))
    V.SAIDA=d;V.ARQ_AMOSTRA=d/'amostra.json';V.ARQ_PASSE={i:d/f'passe_{i}.jsonl' for i in (1,2,3)}
    V.ARQ_CONSENSO=d/'consenso.jsonl';V.CONCORRENCIA=20;VI.CONCORRENCIA=20
    VI.ARQ_AMOSTRA_PRODUCAO=V.ARQ_AMOSTRA;VI.ARQ_PRODUCAO=d/'verificador.jsonl';VI.ARQ_PRODUCAO.touch(exist_ok=True)
    VI.ARQ_CONSENSO_PRODUCAO=V.ARQ_CONSENSO
    esperado={(slug,b,r.id) for b,rs in am.items() for r in rs}
    for i in (1,2,3):
        V.classificar_passe(i,slugs=[slug],provider='featherless',modelo=DS)
        for r in linhas(V.ARQ_PASSE[i]):
            if r.get('ok'): assert r['provider']=='featherless' and r['modelo']==DS and r['modelo_efetivo']==DS
    passes=[V._ler_passe(i) for i in (1,2,3)]
    assert all(set(v)==esperado for v in passes), 'classificacao_incompleta'
    cons=V._consensuar(passes,sorted(esperado));assert len(cons)==len(esperado)
    jsonl(V.ARQ_CONSENSO,cons)
    ver,man=VI.calcular_aplicacao(cons,slugs=[slug],provider='featherless',modelo=DS)
    assert man['n_falharam']==0 and not any(r.get('verificacao_pendente') for r in ver), 'verificador_incompleto'
    for r in linhas(VI.ARQ_PRODUCAO):
        if r.get('ok'): assert r['provider']=='featherless' and r['modelo']==DS
    jsonl(d/'consenso_verificado.jsonl',ver);salvar(d/'manifesto.json',man)
    return d/'consenso_verificado.jsonl'


def gerar_filme(slug):
    from espectro24 import pipeline as P, eixos as E, condicoes as C, synthesize as S
    from espectro24.prosa_local import _buckets_do_bruto
    from espectro24.render import build_output
    from espectro24.validacao_publicado import validar_publicado
    from espectro24.config import BEST_OF_N
    p=pasta(slug);estado=ler(p/'estado.json')
    if estado['estado']=='gerado': return
    if estado.get('erro'):
        estado.setdefault('erros_anteriores',[]).append(estado.pop('erro'))
    estado.update(estado='em_andamento', etapa='classificacao');salvar(p/'estado.json',estado)
    bruto=Path(estado['bruto_raiz']) if estado.get('bruto_raiz') else (ROOT/'dados/bruto' if estado['origem']=='candidato' else OUT/'bruto')
    meta=ler(bruto/slug/'meta.json');am=P.amostra_do_bruto(slug,raiz=bruto)
    estado['amostra']={k:len(v) for k,v in am.items()};salvar(p/'estado.json',estado)
    cons=ROOT/'resultado/votacao-3/consenso_verificado.jsonl'
    if estado['grupo']!='coberto': cons=classificar(slug,p,am)
    cat=E.carregar_classificacao(cons)
    E.checar_amostra_classificada(cat[slug],{b:{r.id for r in rs} for b,rs in am.items()})
    chamadas=Chamador(p,slug)
    if not (p/'bullets.json').exists():
        estado['etapa']='sintese_rotulagem';salvar(p/'estado.json',estado)
        buckets=_buckets_do_bruto(slug,meta,bruto)
        for b in buckets: S.synthesize_bucket(b,client_call=chamadas.texto('sintese'),model=DS,provider='featherless')
        ident=meta.get('identidade_letterboxd') or {}
        ficha=ler(p/'identidade.json').get('ficha') if (p/'identidade.json').exists() else dict(titulo=ident.get('titulo'),ano=ident.get('ano'),tmdb_id=ident.get('tmdb_id_letterboxd'))
        out=build_output(slug,buckets,data_coleta=meta.get('coletado_em') or '2026-11-08',origens={},
            total_observado=sum(meta.get('histograma_bruto',{}).values()),ficha=ficha,coleta=meta)
        from espectro24.models import Distribuicao
        from espectro24.render import aplicar_distribuicao
        hist={float(k):v for k,v in meta.get('histograma_bruto',{}).items()}
        dist=Distribuicao.de_histograma(hist)
        if dist: aplicar_distribuicao(out,dist)
        out['eixos']=P.montar_eixos(slug,out,{b:{r.id for r in rs} for b,rs in am.items()},consenso=cat,client_call=chamadas.texto('rotulagem'),model=DS,provider='featherless')
        out['eixos']['verificador']=dict(aplicado=True,fonte=str(cons),classificacao='existente' if estado['grupo']=='coberto' else DS)
        out['proveniencia_llm']=dict(sintese=dict(provider='featherless',modelo=DS),rotulagem=dict(provider='featherless',modelo=DS),classificacao=dict(fonte=str(cons),sha256=sha(cons)))
        salvar(p/'bullets.json',out)
    out=ler(p/'bullets.json')
    estado['degradacao']={b['bucket']:dict(n=b['n_validas'],modo=b['modo'],estado_piso=b['estado_piso']) for b in out['buckets'] if b['n_validas']<40}
    valid={b['bucket']:validar_publicado(b) if b['modo']!='sem_analise' else dict(passa_publicado=None,estado='sem_analise') for b in out['buckets']}
    estado['validadores_bullets']=valid;estado['validadores_condicoes']={}
    estado['etapa']='condicoes';salvar(p/'estado.json',estado)
    for modelo in modelos_obrigatorios():
        dest=p/'condicoes'/modelo.split('/')[-1]/'condicoes.json'
        if not dest.exists(): salvar(dest,C.gerar(out,n=BEST_OF_N,provider='featherless',model=modelo,gerar=chamadas.condicoes(modelo)))
        estado['validadores_condicoes'][modelo]=validar_condicoes(out,ler(dest))
        salvar(p/'estado.json',estado)
    estado['sem_kimi']=not (p/'condicoes/Kimi-K3.1-Pro/condicoes.json').exists()
    estado['condicoes_geradas']=[m for m in MODELOS if (p/'condicoes'/m.split('/')[-1]/'condicoes.json').exists()]
    estado.update(estado='gerado',etapa='concluido',classificacao='existente' if estado['grupo']=='coberto' else 'nova',fim_utc=datetime.now(timezone.utc).isoformat())
    salvar(p/'estado.json',estado)


def validar_condicoes(out,bloco):
    from espectro24 import condicoes as C
    idx=C.indexar(out)
    # O formato publicado deriva lado do contêiner, como o gerador faz antes de salvar.
    fs=[C.validar(dict(c,lado=lado),idx) for lado in C.LADOS for c in (bloco or {}).get(lado,[])]
    return dict(aprovadas=len(fs),flags=sum(map(len,fs)),
        descartadas=len((bloco or {}).get('descartadas',[])),
        recusas=len((bloco or {}).get('sem_condicao_publicavel',[])),
        inconsistencias_recusa=len(C.inconsistencias_de_recusa(bloco,idx)) if bloco else 0,
        pedidos=sum(len(v) for v in (bloco or {}).get('temas_pedidos',{}).values()),
        saltados=sum(len(v) for v in (bloco or {}).get('temas_saltados',{}).values()),
        recusas_invalidas=len((bloco or {}).get('recusas_invalidas',[])),
        gerou_bloco=bloco is not None)


def normal(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',s).casefold() if c.isalnum())
def identidade(fetcher,slug,titulo,ano,*,sessao_tmdb=None):
    import requests
    from espectro24.ficha import extrair_identidade_letterboxd, buscar_ficha
    from espectro24.urls import film_page_url,film_page_cache_key
    lb=extrair_identidade_letterboxd(fetcher.get(film_page_url(slug),film_page_cache_key(slug)),slug)
    if not lb or not lb.get('tmdb_id_letterboxd'): raise ValueError('sem_identidade_letterboxd')
    r=(sessao_tmdb or requests).get(f"https://api.themoviedb.org/3/movie/{lb['tmdb_id_letterboxd']}",
       params=dict(api_key=os.environ['TMDB_API_KEY'],language='en-US',append_to_response='alternative_titles'),timeout=30)
    r.raise_for_status();tm=r.json()
    titulos={tm.get('title',''),tm.get('original_title',''),*(x['title'] for x in tm.get('alternative_titles',{}).get('titles',[]))}
    # Alias do título da lista, não da identidade observada.
    aliases={'Star Wars: Episode IV – A New Hope':{'Star Wars','Star Wars: A New Hope'},'Léon: The Professional':{'Léon','Leon: The Professional'},'WALL·E':{'WALL-E'}}
    desejados={titulo}|aliases.get(titulo,set())
    if not ({normal(t) for t in desejados}&{normal(t) for t in titulos}): raise ValueError('titulo_tmdb_nao_confere')
    tm_ano=int(tm['release_date'][:4]);lb_ano=int(lb['ano'])
    if abs(lb_ano-ano)>1 or abs(tm_ano-ano)>1 or abs(lb_ano-tm_ano)>1 or (tm.get('runtime') or 0)<40:
        raise ValueError('ano_ou_duracao_nao_confere')
    if not ({normal(lb['titulo'])}&{normal(t) for t in titulos}): raise ValueError('titulo_letterboxd_nao_confere')
    ficha,_,_=buscar_ficha(lb['titulo'],lb_ano,OUT/'cache/_tmdb',identidade=lb,session=sessao_tmdb)
    if ficha is None: raise ValueError('ficha_identidade_nao_comprovada')
    return dict(letterboxd=lb,tmdb_id=tm['id'],tmdb_titulo=tm['title'],tmdb_ano=tm_ano,
                diferenca_ano=lb_ano-tm_ano,idioma_original=tm.get('original_language'),paises=[c['iso_3166_1'] for c in tm.get('production_countries',[])],generos=[g['id'] for g in tm.get('genres',[])],ficha=ficha)


def coletar():
    from espectro24.fetcher import Fetcher,AntiBotError,SobrecargaError
    from espectro24 import pipeline as P
    from espectro24.ficha import extrair_identidade_letterboxd
    from espectro24.urls import film_page_url
    from espectro24.lote import ler_lista_slugs
    m=ler(OUT/'manifesto.json');proibidos=set(ler(ROOT/'dados/publicados.json')['slugs'])|{r['slug'] for r in m['candidatos']}
    feitos=ler(OUT/'coleta.json') if (OUT/'coleta.json').exists() else []
    f=Fetcher(OUT/'cache');f.cache_dir.mkdir(parents=True,exist_ok=True)
    for item in m['novos']:
        if fim() and not politica_sessao().get('coleta_apos_prazo',False): break
        if any(x['prioridade']==item['prioridade'] for x in feitos): continue
        row=dict(item,estado='identidade_em_andamento');inicio=time.monotonic();slug=item['sugestao']
        try:
            try: ident=identidade(f,slug,item['titulo'],item['ano'])
            except (AntiBotError,SobrecargaError): raise
            except Exception:
                encontrados=P.resolve_slug(f,item['titulo'])
                possibilidades=[r.slug for r in encontrados if r.year is not None and abs(r.year-item['ano'])<=1]
                ident=None
                for s in possibilidades[:5]:
                    try: ident=identidade(f,s,item['titulo'],item['ano']);slug=s;break
                    except (AntiBotError,SobrecargaError): raise
                    except Exception: continue
                if ident is None: raise ValueError('identidade_nao_resolvida')
            row.update(slug=slug,identidade={k:v for k,v in ident.items() if k!='ficha'})
            if slug in proibidos: row['estado']='pulado_existente'
            else:
                p=pasta(slug);p.mkdir(parents=True,exist_ok=True);salvar(p/'identidade.json',ident)
                salvar(OUT/'coleta_em_andamento.json',row)
                sup,dist=P.collect_all_levels(f,slug,dados_dir=OUT/'bruto')
                # Chave nova: força uma segunda leitura HTTP da página, nunca o cache de (a).
                atual=extrair_identidade_letterboxd(f.get(film_page_url(slug),f'{slug}/film_page_pos_coleta.html'),slug)
                if not atual or atual['tmdb_id_letterboxd']!=ident['tmdb_id']:
                    q=OUT/'quarentena'/slug;q.parent.mkdir(parents=True,exist_ok=True)
                    shutil.move(str(OUT/'bruto'/slug),str(q));row['estado']='quarentena'
                else:
                    estado=dict(slug=slug,origem='novo',c22=slug in m['c22_slugs'],grupo='sem_consenso',estado='pendente',prioridade=item['prioridade'])
                    salvar(p/'estado.json',estado);row['estado']='coletado';row['amostra']={b:len(rs) for b,rs in P.amostra_do_bruto(slug,raiz=OUT/'bruto').items()}
                    proibidos.add(slug)
            row['duracao_s']=round(time.monotonic()-inicio,2)
        except (AntiBotError,SobrecargaError) as e:
            row.update(estado='coleta_bloqueada',erro=type(e).__name__);feitos.append(row);salvar(OUT/'coleta.json',feitos);break
        except Exception as e: row.update(estado='identidade_ou_coleta_falhou',erro=type(e).__name__,motivo=str(e)[:160],duracao_s=round(time.monotonic()-inicio,2))
        feitos.append(row);salvar(OUT/'coleta.json',feitos)
        tempos=[r['duracao_s'] for r in feitos if r['estado']=='coletado'][:3]
        if tempos:
            media=sum(tempos)/len(tempos)
            salvar(OUT/'projecao_coleta.json',dict(n_medido=len(tempos),primeiros_tempos_s=tempos,media_s=media,
                filmes_adicionais_ate_parada=int(max(0,PRAZO-time.time())/media),estimativa=True))
        print('Coleta',item['prioridade'],row['estado'],flush=True)
    salvar(OUT/'coleta_concluida.json',dict(concluida=True,fim_utc=datetime.now(timezone.utc).isoformat()))


def recuperar_todos():
    if politica_sessao().get('preparar_e5') is False:
        salvar(OUT/'e5_concluido.json',dict(concluido=True,desativado=True));return
    """Somente E5 no Mac: nenhum modelo juiz é carregado ou chamado."""
    import numpy as np
    import encoder_e5 as E5
    import checagem_bullets as C
    import juiz_bullets_v2 as J
    from espectro24 import pipeline as P,eixos as E
    enc=E5.Encoder.do_disco()
    class CacheEncoder:
        def _run(self,textos,tipo):
            base=OUT/'e5_cache'/tipo;base.mkdir(parents=True,exist_ok=True)
            keys=[hashlib.sha256(t.encode()).hexdigest() for t in textos]
            ausentes={k:t for k,t in zip(keys,textos) if not (base/(k+'.npy')).exists()}
            pares=list(ausentes.items())
            # Checkpoint em lotes pequenos; referência fixa compartilhada entre filmes.
            for start in range(0,len(pares),16):
                lote=pares[start:start+16];vs=getattr(enc,tipo)([t for _,t in lote])
                for (k,_),v in zip(lote,vs):
                    tmp=base/(k+'.tmp.npy');np.save(tmp,v);tmp.replace(base/(k+'.npy'))
            return np.stack([np.load(base/(k+'.npy')) for k in keys])
        def queries(self,ts): return self._run(ts,'queries')
        def passagens(self,ts): return self._run(ts,'passagens')
    encoder=CacheEncoder();referencia=C.textos_de_referencia(ROOT/'resultado')
    while True:
        for ep in sorted(OUT.glob('*/**/estado.json')):
            if ep.parent==OUT: continue
            estado=ler(ep);p=ep.parent
            if estado.get('estado')!='gerado' or (p/'juiz/preparado.json').exists() or (p/'juiz/falha.json').exists(): continue
            try:
                slug=estado['slug'];doc=ler(p/'bullets.json')
                bruto=Path(estado['bruto_raiz']) if estado.get('bruto_raiz') else (ROOT/'dados/bruto' if estado['origem']=='candidato' else OUT/'bruto')
                am=P.amostra_do_bruto(slug,raiz=bruto)
                cons=ROOT/'resultado/votacao-3/consenso_verificado.jsonl' if estado['grupo']=='coberto' else p/'classificacao/consenso_verificado.jsonl'
                cat=E.carregar_classificacao(cons)[slug];mapa=C.eixo_por_tema(doc)
                bullets=[]
                for b in C.bullets_do_doc(doc,'local'):
                    eixo=mapa.get((b['bucket'],b['tema']));ids=C.com_eixo(cat[b['bucket']],eixo)
                    bullets.append(dict(b,eixo=eixo,ids_com_eixo=ids,n_com_eixo=len(ids),de_n=len(am[b['bucket']])))
                grupos={(slug,b):rs for b,rs in am.items()}
                rec=C.recuperar(bullets,grupos,encoder,referencia) if bullets else []
                pares=C.montar_entrada(bullets,rec,{(slug,b,r.id):r for b,rs in am.items() for r in rs})
                for par in pares:
                    par['chars_prompt']=J.chars_do_prompt(par)
                    par['cota_tokens']=math.ceil(J.RAZAO_TOKENS_POR_CHAR*par['chars_prompt'])
                    par['julgavel_estimado']=par['cota_tokens']+J.NUM_PREDICT<=J.num_ctx(J.CONGELADA)
                d=p/'juiz';salvar(d/C.ARQ_EIXO,dict(meta=dict(filmes=[slug]),bullets=bullets))
                salvar(d/C.ARQ_RECUP,dict(recuperacao=rec))
                jsonl(d/C.ARQ_ENTRADA,pares)
                salvar(d/'juiz_v2'/f'config_{J.CONGELADA}.json',dict(config_sha256=J.config_sha256(),**J.config()))
                salvar(d/'preparado.json',dict(pares=len(pares),bullets=len(bullets),
                     nao_julgaveis_estimados=sum(not r['julgavel_estimado'] for r in pares),
                     modelo_encoder=E5.MODELO_ID,config_sha256=J.config_sha256(),juiz_executado=False))
                print('E5 preparado',slug,len(pares),'pares',flush=True)
            except Exception as e:
                salvar(p/'juiz/falha.json',dict(erro=type(e).__name__))
        if (OUT/'llm_concluido.json').exists(): break
        time.sleep(5)
    salvar(OUT/'e5_concluido.json',dict(concluido=True))
    relatorio(final=True)


def comandos_windows():
    # Tudo, inclusive C22, vai a arquivo lacrado no Windows; nenhum conteúdo na tela.
    return r'''$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
python scripts/juiz_etapa2_windows.py --base execucoes/featherless-etapa2-2026-11-08
if ($LASTEXITCODE -ne 0) { throw "pacote invalido; consulte log lacrado" }
python scripts/juiz_etapa2_windows.py --base execucoes/featherless-etapa2-2026-11-08 --executar
if ($LASTEXITCODE -ne 0) { throw "juiz interrompido; consulte log lacrado e retome" }
'''



def projetar_coleta(coleta,restantes,agora=None):
    primeiras=[r for r in sorted(coleta,key=lambda r:r['prioridade']) if r.get('duracao_s') is not None and r['estado']!='pulado_existente'][:3]
    if not primeiras:return None
    tempos=[r['duracao_s'] for r in primeiras];media=sum(tempos)/len(tempos)
    cap=int(max(0,PRAZO-(time.time() if agora is None else agora))/media)
    return dict(n_medido=len(tempos),primeiros_tempos_s=tempos,media_s=media,
        coletas_concluidas_na_medicao=sum(r['estado']=='coletado' for r in primeiras),
        falhas_na_medicao=sum(r['estado']!='coletado' for r in primeiras),
        capacidade_temporal_tentativas=cap,itens_restantes_lista=restantes,
        filmes_adicionais_ate_parada=min(cap,restantes),estimativa=True,
        nota='Tempo por tentativa inclui identidade e falhas de transporte; capacidade de tentar, sem garantia de coleta concluída.')


def relatorio(final=False):
    if politica_sessao().get('preparar_e5') is False and (OUT/'lista3/manifesto.json').exists():
        import lista3_featherless as L
        return L.relatorio(final=final and (L.OUT/'encerrado.json').exists())
    m=ler(OUT/'manifesto.json');estados=[]
    for r in m['candidatos']: estados.append(ler(pasta(r['slug'])/'estado.json'))
    coleta=ler(OUT/'coleta.json') if (OUT/'coleta.json').exists() else []
    for r in coleta:
        if r['estado']=='coletado' and (pasta(r['slug'])/'estado.json').exists(): estados.append(ler(pasta(r['slug'])/'estado.json'))
    slugs_gerados={r['slug'] for r in estados}
    for item in m['novos']:
        registro=next((r for r in coleta if r['prioridade']==item['prioridade']),None)
        slug=(registro or {}).get('slug',item['sugestao'])
        if slug not in slugs_gerados:
            estados.append(dict(slug=slug,origem='novo',c22=slug in m['c22_slugs'],grupo='sem_consenso',
                estado=(registro or {}).get('estado','nao_coletado'),amostra={},classificacao='não executada'))
    for r in estados:
        if r['estado']=='gerado':
            p=pasta(r['slug']);doc=ler(p/'bullets.json')
            r['validadores_condicoes']={mo:validar_condicoes(doc,ler(p/'condicoes'/mo.split('/')[-1]/'condicoes.json')) for mo in MODELOS if (p/'condicoes'/mo.split('/')[-1]/'condicoes.json').exists()}
            r['degradacao']={b['bucket']:dict(n=b['n_validas'],modo=b['modo'],estado_piso=b['estado_piso']) for b in doc['buckets'] if b['n_validas']<40}
            if r.get('erro'):r.setdefault('erros_anteriores',[]).append(r.pop('erro'))
            salvar(p/'estado.json',r)
    usos=linhas(OUT/'uso.jsonl');custos=collections.defaultdict(float)
    for r in usos: custos[r.get('slug')]+=r.get('custo_usd') or 0
    resumo=F.sessao_ambiente().resumo()
    for r in estados:
        r['custo_usd']=round(custos[r['slug']],9)
        jp=pasta(r['slug'])/'juiz/preparado.json';r['juiz']=ler(jp) if jp.exists() else dict(estado='pendente')
    saldo=None
    try: saldo=conta('credits/balance');salvar(OUT/('saldo_final.json' if final else 'saldo_atual.json'),saldo)
    except Exception: pass
    ini=ler(OUT/'saldo_inicial.json');debito=float(ini['balance_usd'])-float(saldo['balance_usd']) if saldo else None
    gerados=sum(r['estado']=='gerado' for r in estados)
    nao=[x for x in m['novos'] if not any(c['prioridade']==x['prioridade'] and c['estado'] in ('coletado','pulado_existente') for c in coleta)]
    ident=[r for r in coleta if r['estado'] not in ('coletado','pulado_existente')]
    invariantes_ok=True
    try: conferir()
    except AssertionError: invariantes_ok=False
    report=dict(final=final,filmes=estados,coleta=coleta,nao_coletados=nao,identidade_quarentena=ident,
        caixa=resumo,saldo=saldo,debito_conta_usd=debito,
        delta_debito_livro_usd=debito-resumo['custo_usd'] if debito is not None else None,
        gerados=gerados,juiz_estimativa_h=gerados/4.36,invariantes_preservadas=invariantes_ok,
        commits=ler(OUT/'commits.json') if (OUT/'commits.json').exists() else [],
        projecao_coleta=projetar_coleta(coleta,len(m['novos'])-len(coleta)))
    salvar(OUT/'relatorio.json',report)
    md=['# Etapa 2 — '+('final' if final else 'progresso'),'',
        f"Gerados: {gerados}. Livro: US$ {resumo['custo_usd']:.6f}; reservas pendentes US$ {resumo['reservas_pendentes_usd']:.6f}.",
        f"Débito da conta: {debito}; diferença débito − livro: {report['delta_debito_livro_usd']}.",
        f"Invariantes preservadas: {invariantes_ok}. Juiz não executado. Estimativa histórica: {gerados/4.36:.2f} h a 4,36 filmes/h.",
        '', 'C22: '+', '.join(m['c22_slugs']), '',
        '|Filme|Origem|C22|H/M/F|Classificação|Bullets aprovados/avaliados|Condições DS / Kimi / Qwen (aprovadas; flags; descartadas)|US$|Pendências|',
        '|---|---|---|---|---|---|---|---:|---|']
    for r in estados:
        val=list(r.get('validadores_bullets',{}).values());aval=[v for v in val if v.get('passa_publicado') is not None]
        cond=r.get('validadores_condicoes',{})
        cs=[';'.join(str(cond[mo][k]) for k in ('aprovadas','flags','descartadas')) if mo in cond else 'pendente' for mo in MODELOS]
        am=r.get('amostra',{})
        pend=r['estado']+(' / amostra reduzida '+','.join(r['degradacao']) if r.get('degradacao') else '')+(' / '+r['erro'] if r.get('erro') else '')+(' / E5 pendente' if r['juiz'].get('estado')=='pendente' else '')
        md.append('|'+ '|'.join([r['slug'],r['origem'],'s' if r['c22'] else 'n','/'.join(str(am.get(b,'—')) for b in ('negativas','medianas','positivas')),
            r.get('classificacao','existente' if r['grupo']=='coberto' else 'nova pendente'),
            f"{sum(v['passa_publicado'] for v in aval)}/{len(aval)}",' / '.join(cs),f"{r['custo_usd']:.6f}",pend])+'|')
    md+=['','Casos de identidade, quarentena e falhas de coleta:']+[f"- {r.get('slug',r['sugestao'])}: {r['estado']} {r.get('erro','')} {r.get('motivo','')}" for r in ident]
    md+=['','Lista sem coleta concluída:']+[f"- {r['prioridade']}. {r['titulo']} ({r['ano']})" for r in nao]
    if report['projecao_coleta']: md+=['','Projeção HTTP: '+json.dumps(report['projecao_coleta'],ensure_ascii=False)]
    md+=['','Commits de código: '+str(report['commits']),'',
        'Ao encerrar, o finalizador cria lacrado_c22/juiz_windows.zip com código e entradas, sem bruto nem cache HTTP. Extraia na raiz do repositório Windows. Comandos PowerShell:','```powershell',comandos_windows(),'```',
        'Os comandos preservam a configuração v2.2 e medem contexto antes de julgar. Logs ficam no lacrado. Reexecutar retoma os pares concluídos.']
    escrever_atomico(OUT/'RELATORIO.md','\n'.join(md)+'\n')
    escrever_atomico(OUT/'rodar_juiz_windows.ps1',comandos_windows())
    return report


def iniciar(modo,slug=None,log=None):
    args=[sys.executable,str(Path(__file__).resolve()),modo]+(['--slug',slug] if slug else [])
    if modo in ('recuperar','finalizar'):
        args=['/usr/bin/caffeinate','-i','-s',*args]
    fh=open(log or OUT/(modo+'.log'),'a')
    try: return subprocess.Popen(args,cwd=ROOT,stdout=fh,stderr=subprocess.STDOUT,start_new_session=True)
    finally: fh.close()

def encerrar(proc):
    if proc and proc.poll() is None:
        os.killpg(proc.pid,signal.SIGTERM)
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL);proc.wait()


def rodar():
    conferir()
    with (OUT/'driver.lock').open('w') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise SystemExit('driver já está rodando')
        (OUT/'llm_concluido.json').unlink(missing_ok=True)
        salvar(OUT/'pid.json',dict(pid=os.getpid(),inicio_utc=datetime.now(timezone.utc).isoformat()))
        iniciar('vigiar')
        coletor=None if (OUT/'coleta_concluida.json').exists() else iniciar('coletar')
        e5=iniciar('recuperar');worker=None;razao='fila_concluida'
        try:
            candidatos=ler(OUT/'manifesto.json')['candidatos'];visitados=set()
            while not fim():
                resumo=F.sessao_ambiente().resumo()
                if resumo['custo_usd']+resumo['reservas_pendentes_usd']>=15:
                    razao='teto';break
                fila=[r['slug'] for r in candidatos]
                if (OUT/'coleta.json').exists(): fila += [r['slug'] for r in ler(OUT/'coleta.json') if r['estado']=='coletado']
                pend=[s for s in fila if s not in visitados and ler(pasta(s)/'estado.json')['estado']!='gerado']
                if not pend:
                    if coletor and coletor.poll() is None: time.sleep(5);continue
                    break
                slug=pend[0];visitados.add(slug);p=pasta(slug)
                worker=iniciar('gerar',slug,log=p/'execucao.log')
                while worker.poll() is None:
                    if fim(): encerrar(worker);razao='prazo';break
                    time.sleep(2)
                estado=ler(p/'estado.json')
                if fim():
                    if estado['estado']!='gerado': estado.update(estado='interrompido',erro='prazo');salvar(p/'estado.json',estado)
                    break
                if estado.get('erro')=='TetoExcedido': razao='teto_ou_prazo_reserva';break
                r=relatorio();salvar(OUT/'estado.json',dict(estado='rodando',gerados=r['gerados'],ultimo_slug=slug,caixa=r['caixa']))
                print('Progresso',r['gerados'],'gerados;',slug,estado['estado'],'US$',round(r['caixa']['custo_usd'],5),flush=True)
            if fim(): razao='prazo'
        finally:
            encerrar(worker);encerrar(coletor)
            salvar(OUT/'llm_concluido.json',dict(motivo=razao,fim_utc=datetime.now(timezone.utc).isoformat()))
            # Recuperação não é paga; termina mesmo depois da parada LLM.
            while e5.poll() is None:
                time.sleep(5)
            r=relatorio(final=True)
            empacotar_juiz()
            salvar(OUT/'estado.json',dict(estado='encerrado',motivo=razao,gerados=r['gerados'],caixa=r['caixa']))
            print('Encerrado',razao,r['gerados'],'gerados',r['caixa'],flush=True)


@contextlib.contextmanager
def trava(caminho):
    caminho.parent.mkdir(parents=True,exist_ok=True)
    with caminho.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        yield


def vigiar():
    # Independente do supervisor e das bibliotecas HTTP; nunca chama API.
    while not fim() and not (OUT/'llm_concluido.json').exists():
        time.sleep(min(1,max(0,PRAZO-time.time())))
    if not fim(): return
    for pidfile in OUT.glob('*/**/processo_pago.json'):
        d=ler(pidfile);pid=d['pid']
        cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
        if 'etapa2_featherless.py gerar --slug '+d['slug'] not in cmd: continue
        try: os.kill(pid,signal.SIGKILL)
        except ProcessLookupError: pass
    salvar(OUT/'parada_rigida.json',dict(utc=datetime.now(timezone.utc).isoformat()))


def empacotar_juiz():
    if politica_sessao().get('preparar_e5') is False: return 0
    import zipfile
    arquivos=[]
    for meta in sorted(OUT.glob('*/**/juiz/preparado.json')):
        d=meta.parent;m=ler(meta);m['entrada_sha256']=sha(d/'juiz_entrada.jsonl');salvar(meta,m)
        arquivos += [p for p in d.rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl')]
    arquivos += list((ROOT/'scripts').glob('*.py'))
    arquivos += [p for p in (ROOT/'src/espectro24').iterdir() if p.is_file() and p.suffix in ('.py','.txt')]
    arquivos += [ROOT/'pyproject.toml',OUT/'rodar_juiz_windows.ps1']
    tmp=OUT/'lacrado_c22/juiz_windows.tmp.zip'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(arquivos)):z.write(p,p.relative_to(ROOT))
    tmp.replace(OUT/'lacrado_c22/juiz_windows.zip')
    return len(arquivos)


def finalizar():
    # Processo livre de chamadas pagas: relatório definitivo depois das duas filas.
    while not ((OUT/'llm_concluido.json').exists() and (OUT/'e5_concluido.json').exists()):
        time.sleep(5)
    # Espera os escritores do supervisor/E5 e a liberação das reservas da conta.
    time.sleep(35)
    r=relatorio(final=True)
    n=empacotar_juiz()
    salvar(OUT/'relatorio_final_concluido.json',dict(gerados=r['gerados'],caixa=r['caixa'],arquivos_pacote_juiz=n,
        fim_utc=datetime.now(timezone.utc).isoformat()))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('modo',choices=['preparar','rodar','gerar','coletar','recuperar','relatorio','finalizar','vigiar']);ap.add_argument('--slug');a=ap.parse_args()
    config()
    if a.modo=='preparar': preparar()
    elif a.modo=='rodar': rodar()
    elif a.modo=='coletar':
        with trava(OUT/'coletor.lock'): coletar()
    elif a.modo=='recuperar':
        with trava(OUT/'e5.lock'): recuperar_todos()
    elif a.modo=='vigiar': vigiar()
    elif a.modo=='finalizar': finalizar()
    elif a.modo=='relatorio': relatorio(final=(OUT/'llm_concluido.json').exists())
    elif a.modo=='gerar':
        try:
            with trava(pasta(a.slug)/'geracao.lock'):
                salvar(pasta(a.slug)/'processo_pago.json',dict(pid=os.getpid(),slug=a.slug))
                try: gerar_filme(a.slug)
                finally: (pasta(a.slug)/'processo_pago.json').unlink(missing_ok=True)
        except BaseException as e:
            p=pasta(a.slug);estado=ler(p/'estado.json')
            estado.update(estado='interrompido' if isinstance(e,F.TetoExcedido) else 'falha',erro=type(e).__name__)
            salvar(p/'estado.json',estado)
            import traceback
            traceback.print_exc()  # exclusivamente no arquivo próprio, lacrado quando C22
            raise SystemExit(1)

if __name__=='__main__': main()
