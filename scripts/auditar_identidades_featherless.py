"""Auditoria somente leitura dos candidatos: rede serial com Fetcher/delay vigente."""
from pathlib import Path
import json
import sys
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from espectro24.fetcher import Fetcher, AntiBotError, SobrecargaError
from espectro24.ficha import extrair_identidade_letterboxd
from espectro24.urls import film_page_url, film_page_cache_key
from espectro24.lote import ler_lista_slugs

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'resultado/featherless-etapa1-2026-11-08'

def auditar():
    candidatos=ler_lista_slugs(ROOT/'dados/lote/lista-noturno-2026-09-18.txt')
    assert len(candidatos)==55
    fetcher=Fetcher(OUT/'identidade_cache');fetcher.cache_dir.mkdir(parents=True,exist_ok=True)
    cache={}
    for pasta in (ROOT/'dados/cache/_tmdb', ROOT/'resultado/cache/_tmdb'):
        if pasta.exists():
            for f in pasta.glob('*.json'):
                try:
                    d=json.loads(f.read_text());cache.setdefault(f.stem,[]).append((str(f.relative_to(ROOT)),d))
                except (ValueError,OSError): pass
    rows=[];parado=None
    for slug in candidatos:
        meta=json.loads((ROOT/'dados/bruto'/slug/'meta.json').read_text())
        ident=meta.get('identidade_letterboxd')
        ficha=None;fonte=None
        pub=ROOT/'resultado'/f'{slug}.json'
        if pub.exists(): ficha=json.loads(pub.read_text()).get('ficha');fonte=str(pub.relative_to(ROOT))
        if not ficha:
            for pares in cache.values():
                for arq,d in pares:
                    if (d.get('identidade') or {}).get('slug')==slug:
                        ficha=d;fonte=arq
        if not ficha:
            import re,unicodedata
            title=(ident or {}).get('titulo')
            title=title or slug
            normal=unicodedata.normalize('NFKD',title).encode('ascii','ignore').decode().lower()
            key=re.sub(r'[^a-z0-9]+','_',normal).strip('_')+'_'+str(meta.get('ano_lancamento'))
            pares=cache.get(key,[])
            if pares: fonte,ficha=pares[-1]
        row=dict(slug=slug,ts=datetime.now(timezone.utc).isoformat(),persistida=ident,ano_bruto=meta.get('ano_lancamento'),ficha_tmdb_id=(ficha or {}).get('tmdb_id'),ficha_ano=(ficha or {}).get('ano'),ficha_fonte=fonte)
        if parado:
            row.update(status='nao_consultado',erro=parado)
        else:
            try:
                html=fetcher.get(film_page_url(slug),film_page_cache_key(slug))
                atual=extrair_identidade_letterboxd(html,slug)
                row['atual']=atual
                problemas=[]
                if atual is None: problemas.append('sem_identidade_atual')
                if ident is None: problemas.append('sem_identidade_persistida')
                if not ficha: problemas.append('sem_ficha_persistida')
                if atual:
                    if ident and atual['tmdb_id_letterboxd']!=ident.get('tmdb_id_letterboxd'):problemas.append('id_persistido_diverge')
                    if ficha and atual['tmdb_id_letterboxd']!=ficha.get('tmdb_id'):problemas.append('id_ficha_diverge')
                    if atual.get('ano')!=meta.get('ano_lancamento'):problemas.append('ano_bruto_diverge')
                    if ficha and atual.get('ano')!=ficha.get('ano'):problemas.append('ano_ficha_diverge')
                row.update(status='divergencia_ou_ausencia' if problemas else 'confere',problemas=problemas)
            except (AntiBotError,SobrecargaError) as e:
                parado=type(e).__name__;row.update(status='bloqueado',erro=str(e))
            except Exception as e:
                row.update(status='erro_consulta',erro=f'{type(e).__name__}: {e}')
        rows.append(row)
        (OUT/'identidades.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
        print(slug,row['status'],flush=True)
    from collections import Counter
    print(dict(Counter(r['status'] for r in rows)))

if __name__=='__main__':auditar()
