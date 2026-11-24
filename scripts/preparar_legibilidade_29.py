"""Amplia a medição da home com garantia conservadora para os 29 novos.

As caixas históricas dos 98 filmes são preservadas. Nos novos, a caixa
registrada é a imagem inteira, e o véu também precisa passar contra branco
puro: isso garante contraste >=4,5 em qualquer caixa e recorte possível.
Não confunde o limite conservador com caixas medidas no navegador.
"""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preparar_publicacao_29 as P
import medir_legibilidade as M
from espectro24.still_hash import baixar

def preparar():
 old=P.D.ler(P.ROOT/'dados/legibilidade_manchete.json')
 t=(P.STAGE/'frontend/js/indice.js').read_text();indice=json.loads(t[t.index('=')+1:].strip().rstrip(';'))['filmes']
 alfa=max(old['alfa'],M.menor_alfa([np.ones((1,3))]))
 registros={};casos=[]
 for f in indice:
  slug=f['slug']
  if slug in M.EXCLUIDOS:continue
  caixas=old['filmes'][slug]['caixas'] if slug not in P.SLUGS else {str(w):[0,0,1,1] for w in M.LARGURAS}
  path=f['imagens']['backdrop_path']
  with Image.open(baixar(path)) as im:img=np.asarray(im.convert('RGB'),dtype=np.float64)/255
  r=dict(backdrop_path=path,caixas=caixas,luminancia_sem_veu={},contraste_com_veu={})
  if slug in P.SLUGS:r['caixas_metodo']='limite conservador: imagem inteira; garantia adicional contra branco puro para qualquer caixa'
  for w,c in caixas.items():
   pixels=M.regiao(img,c);l0=M.luminancia_do_fundo(pixels,0);contraste=M.contraste(M.luminancia_do_fundo(pixels,alfa))
   assert contraste>=4.5
   r['luminancia_sem_veu'][w]=round(l0,4);r['contraste_com_veu'][w]=round(contraste,3);casos.append((contraste,slug,int(w),l0))
  registros[slug]=r
 pior=min(casos);claro=max(casos,key=lambda x:x[3])
 old.update(alfa=alfa,filmes=registros,pior_caso=dict(slug=pior[1],largura=pior[2],contraste=round(pior[0],3),luminancia_sem_veu=round(pior[3],4),contraste_sem_veu=round(M.contraste(pior[3]),3)),fundo_mais_claro=dict(slug=claro[1],largura=claro[2],luminancia_sem_veu=round(claro[3],4)))
 old['garantia_novos']=dict(filmes=29,metodo='Contraste >=4,5 contra branco puro; cobre qualquer região de qualquer imagem, sem afirmar medição de caixas no navegador.',contraste= M.contraste(M.luminancia_do_fundo(np.ones((1,3)),alfa)))
 P.D.salvar(P.STAGE/'dados/legibilidade_manchete.json',old)
 css=P.STAGE/'frontend/css/styles.css';s=css.read_text();assert s.count(f'--ed-veu: {M.json.loads((P.ROOT/"dados/legibilidade_manchete.json").read_text())["alfa"]}')==1
 s=s.replace(f'--ed-veu: {P.D.ler(P.ROOT/"dados/legibilidade_manchete.json")["alfa"]}',f'--ed-veu: {alfa}');css.write_text(s)
 print(f'Contraste >=4,5 validado em {len(registros)} filmes; véu {alfa}; novos cobertos pelo limite de branco puro.')
if __name__=='__main__':preparar()
