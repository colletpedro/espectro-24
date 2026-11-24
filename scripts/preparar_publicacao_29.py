"""Prepara offline o lote de 29 autorizado em 08/11/2026, sem deploy/commit.

A origem gerada permanece intacta. Somente DeepSeek é incorporado; as
retiradas R13 e os validadores são os mesmos do publicador existente.
"""
from __future__ import annotations
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import etapa2_featherless as D
import publicar_condicoes as P
from espectro24 import condicoes as C
from espectro24.validacao_publicado import validar_publicado

OUT=D.OUT/'publicacao29'
STAGE=OUT/'staging'
BASE_URL='https://espectro-24-eu6z.vercel.app'
SLUGS=(
 'the-shawshank-redemption','the-godfather-part-ii','the-lord-of-the-rings-the-two-towers',
 'schindlers-list','pulp-fiction','one-flew-over-the-cuckoos-nest','its-a-wonderful-life',
 'the-silence-of-the-lambs','seven-samurai','the-green-mile','life-is-beautiful',
 'terminator-2-judgment-day','star-wars','the-pianist','harakiri','the-lion-king',
 'psycho','the-departed','american-history-x','cinema-paradiso','leon-the-professional',
 'casablanca','the-intouchables','the-usual-suspects','alien','rear-window','modern-times',
 'once-upon-a-time-in-the-west','wall-e',
)


def carregar(slug):
    assert slug in SLUGS
    p=D.pasta(slug);es=D.ler(p/'estado.json');assert es['estado']=='gerado' and es['origem']=='novo' and not es['c22']
    doc=copy.deepcopy(D.ler(p/'bullets.json'))
    assert doc['slug']==slug
    for b in doc['buckets']:
        if b['modo']!='sem_analise':assert validar_publicado(b)['passa_publicado'],(slug,b['bucket'])
    fi=doc['ficha'];ident=fi.get('identidade') or {}
    assert ident.get('status')=='validada' and fi.get('tmdb_id') and ident['tmdb_id_letterboxd']==fi['tmdb_id']
    assert fi.get('poster_path') and fi.get('sinopse_oficial') and fi.get('generos')
    assert doc['eixos']['verificador']['aplicado']
    bloco,n=P.aplicar_retiradas(slug,D.ler(p/'condicoes/DeepSeek-V4.1-Flash-1017/condicoes.json'),doc)
    P.validar_bloco(slug,bloco,C.indexar(doc))
    assert bloco['modelo']==D.DS
    detalhe=D.ler(OUT/'metadados_tmdb'/f"{fi['tmdb_id']}.json")
    assert detalhe['id']==fi['tmdb_id'] and abs(int(detalhe['release_date'][:4])-fi['ano'])<=1
    assert D.normal(detalhe['title']) in {D.normal(ident.get('titulo_tmdb_correspondente','')),D.normal(D.ler(p/'identidade.json')['tmdb_titulo'])}
    fi['paises']=[c['iso_3166_1'] for c in detalhe['production_countries']]
    assert fi['paises']
    doc['condicoes']=bloco
    # Referências operacionais usam caminhos relativos, sem diretório pessoal.
    for obj in [doc['eixos'].get('verificador',{}),*list((doc.get('proveniencia_llm') or {}).values())]:
        if isinstance(obj,dict) and isinstance(obj.get('fonte'),str):
            try:obj['fonte']=str(Path(obj['fonte']).relative_to(ROOT))
            except ValueError:pass
    return doc,n


def preparar():
    assert len(SLUGS)==len(set(SLUGS))==29
    atuais=D.ler(ROOT/'dados/publicados.json');assert len(atuais['slugs'])==99
    assert not (set(SLUGS)&set(atuais['slugs']))
    assert not (set(SLUGS)&set(D.ler(D.OUT/'manifesto.json')['c22_slugs']))
    OUT.mkdir(parents=True,exist_ok=True);STAGE.mkdir(exist_ok=True)
    # Cópia isolada do frontend rastreado; nenhum bruto, segredo ou C22 é enviado.
    rastreados=subprocess.run(['git','ls-files','frontend'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    for nome in rastreados:
        origem=ROOT/nome;dest=STAGE/nome;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origem,dest)
    shutil.copytree(ROOT/'src/espectro24',STAGE/'src/espectro24',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    for nome in ['logos.json','logos_override.json']:
        dest=STAGE/'dados'/nome;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'dados'/nome,dest)
    for slug in atuais['slugs']:
        dest=STAGE/'resultado'/f'{slug}.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'resultado'/f'{slug}.json',dest)
    publicados=[]
    for slug in SLUGS:
        doc,n=carregar(slug);D.salvar(STAGE/'resultado'/f'{slug}.json',doc)
        ident=(doc['ficha'].get('identidade') or {})
        publicados.append(dict(slug=slug,titulo=ident.get('titulo_letterboxd') or doc['ficha']['titulo'],ano=ident.get('ano_letterboxd') or doc['ficha']['ano'],
            titulo_pt=doc['ficha']['titulo'],url=BASE_URL+'/filme.html?slug='+slug,condicoes_modelo=D.DS,retidas_R13=n))
    novos=copy.deepcopy(atuais);novos['slugs']=sorted(atuais['slugs']+list(SLUGS));assert len(novos['slugs'])==128
    D.salvar(STAGE/'dados/publicados.json',novos)
    # Data de entrada aprovada, independente da data de um deploy posterior.
    registro=D.ler(STAGE/'frontend/entrada_no_catalogo.json');hoje=datetime.now(ZoneInfo('America/Fortaleza')).date().isoformat()
    for slug in SLUGS:registro['entradas'][slug]='2026-11-08'
    D.salvar(STAGE/'frontend/entrada_no_catalogo.json',registro)
    r=subprocess.run([sys.executable,str(STAGE/'frontend/build_data.py')],cwd=STAGE,capture_output=True,text=True,check=True)
    (OUT/'build.log').write_text(r.stdout+r.stderr)
    dados=(STAGE/'frontend/js/data.js').read_text();dados=json.loads(dados[dados.index('=')+1:].strip().rstrip(';'))
    assert set(dados['catalogo'])==set(novos['slugs'])
    assert not set(D.ler(D.OUT/'manifesto.json')['c22_slugs'])&set(dados['catalogo'])
    for slug in SLUGS:assert dados['filmes'][slug]['condicoes']['modelo']==D.DS
    # Os 99 documentos existentes publicados permanecem semanticamente idênticos.
    for slug in atuais['slugs']:
        assert D.ler(ROOT/'frontend/data'/f'{slug}.json')==D.ler(STAGE/'frontend/data'/f'{slug}.json'),slug
    hashes={str(p.relative_to(STAGE/'frontend')):D.sha(p) for p in (STAGE/'frontend').rglob('*') if p.is_file()}
    D.salvar(OUT/'manifesto.json',dict(estado='preparado',catalogo_anterior=99,catalogo_novo=128,modelo_condicoes=D.DS,
        filmes=publicados,frontend_sha256=hashes,source_commit=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip(),
        dados_commitados=False,fonte_C22_incluida=False))
    listar_pendentes()
    print('Preparados 29 filmes; catálogo 128; 99 existentes preservados; sem C22 e sem novas chamadas LLM.')


def listar_pendentes():
    import lista3_featherless as L
    rep=D.ler(L.OUT/'relatorio_sessao.json');m2=D.ler(D.OUT/'manifesto.json');m3=D.ler(L.OUT/'manifesto.json')
    ident2={r['slug']:r for r in D.ler(D.OUT/'coleta.json') if r.get('slug')}
    itens2={r['sugestao']:r for r in m2['novos']};itens3={r['sugestao']:r for r in m3['lista']}
    linhas=[]
    for r in rep['filmes']:
        slug=r['slug']
        if slug in SLUGS:continue
        if r['origem']=='frente1':
            meta=D.ler(ROOT/'dados/bruto'/slug/'meta.json');title=(meta.get('identidade_letterboxd') or {}).get('titulo') or slug;ano=meta.get('ano_lancamento')
            if r['estado']=='gerado':pend=['Completar a ficha e comprovar identidade Letterboxd × TMDB (título, ano e ID; imagens, sinopse, gêneros e países); validar o pacote final.']
            else:pend=['Concluir apenas o verificador V4.1 pendente (JSON inválido); preservar as três passadas completas do mesmo modelo.','Gerar e validar síntese, rotulagem e condições.','Completar e validar a ficha técnica.']
            if r['c22']:
                title=slug
                pend.insert(0,'Escopo C22 lacrado; precisa de liberação explícita para publicação.')
            if slug=='moneyball':pend.append('Resolver o bloqueio R13: condição com tema sem eixo; sem correção manual do texto.')
        else:
            it=ident2.get(slug) or itens2.get(slug) or itens3.get(slug) or {}
            title=it.get('titulo') or slug;ano=it.get('ano')
            if r['estado']=='identidade_ou_coleta_falhou':pend=['Retomar coleta após timeout HTTP (ReadTimeout), preservando o cache.','Reconfirmar identidade após a coleta.','Classificar em três passadas + verificador V4.1; gerar síntese, rotulagem e condições; validar ficha e publicação.']
            elif r['estado']=='coleta_bloqueada':pend=['Coleta parada por AntiBotError; exige retomada autorizada após o bloqueio.','Concluir coleta e conferência de identidade; classificação e geração completas; validadores e ficha.']
            else:pend=['Resolver e confirmar identidade Letterboxd × TMDB pelo título, ano e ID.','Coletar após liberação do bloqueio, respeitando delay e cotas.','Classificar em três passadas + verificador V4.1; gerar síntese, rotulagem e condições; validar ficha e publicação.']
        linhas.append(dict(filme=title,ano=ano,slug=slug,origem=r['origem'],c22=r['c22'],estado=r['estado'],pendencias=pend))
    assert len(linhas)==220
    D.salvar(OUT/'nao_publicados.json',linhas)
    md=['# Filmes fora do lote autorizado de 29','',f'{len(linhas)} filmes. O juiz de fidelidade não é requisito desta leva. As saídas C22 permanecem lacradas.','',
        '|Filme|Ano|Origem|C22|O que falta|','|---|---:|---|---|---|']
    for r in linhas:md.append('|'+ '|'.join([r['filme'],str(r['ano'] or '—'),r['origem'],'s' if r['c22'] else 'n',' '.join(r['pendencias'])])+'|')
    D.escrever_atomico(OUT/'NAO_PUBLICADOS.md','\n'.join(md)+'\n')

if __name__=='__main__':preparar()
