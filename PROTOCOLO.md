# Protocolo — como fazer

Este arquivo responde *"como eu faço X?"*. É carregado sob demanda, quando a
sessão vai **medir, testar, ler à cega ou publicar** — não a cada implementação.

A LEI (o que vale agora) está em `SPEC.md`. O *por quê* de cada regra está nos
`HISTORICO_*.md`. O que ainda é decisão está em `ABERTO.md`.

---

<!-- SPEC.md linhas 461–469 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **A regra prática que fica:** ao escrever ou revisar um exemplo dentro de
> um prompt deste projeto, ele precisa ser verificado contra a MESMA lista de
> proibições que se aplica ao texto que o modelo vai gerar — um exemplo não é
> prosa de apoio, é a regra que o modelo mais copia.
>
> ---
>
> ### PENDÊNCIA EDITORIAL NOMEADA — o eixo `expectativa` e o bloco de condições
>

<!-- SPEC.md linhas 1245–1268 · origem: O critério "cerca de um terço do catálogo" está APOSENTADO -->

#### O critério "cerca de um terço do catálogo" está APOSENTADO

A v1.9.15 registrou como critério de sucesso: *"20pp entrega contraste em cerca
de um terço dos filmes sem publicar listas majoritariamente ruidosas"*, e
celebrou 18/35 por estar mais perto de um terço que 13/35. **Esse critério sai
de vigor nesta versão, e a razão é medida, não estética.**

Ele é um alvo de **COBERTURA**, e foi fixado quando `valorativo` era o estado
fraco — o defeito da v1.9.20 era o veredito publicar a MESMA frase em 20 de 35
filmes. **`valorativo` não é mais o estado fraco. MEDIDO
(`docs/arquivo-de-estudos/margem-de-lift/ESTUDO_MARGEM_20PP.md` §5.2):**

- os 17 vereditos `valorativo` publicados são **17 textos distintos**, com
  **zero frases de mais de 25 caracteres repetidas** entre dois filmes
  quaisquer — a reescrita da v1.9.21 e o ataque estrutural da v1.9.22 mataram o
  defeito;
- o ramo `valorativo` **nomeia o `assunto_compartilhado`**, que é uma afirmação
  de conteúdo real e vem de **FREQUÊNCIA**, não de lift;
- e frequência é a estatística estável do sistema: no evento real de cobertura
  70,7% → 100%, o eixo nomeado pelo ramo `valorativo` mudou em **8 de 35**
  filmes, contra **16 de 35** do eixo de maior lift que o ramo `tematico`
  nomeia. **Mover um filme para `valorativo` move a afirmação publicada da
  estatística MENOS estável do sistema para a MAIS estável.**


<!-- SPEC.md linhas 1463–1475 · origem: Estado `contraste`: `tematico` | `valorativo` | **ausente** (v1.9.34) -->

> **NOTA DE MÉTODO, porque o modo de falha se repete.** O número errado
> atravessou o estudo, esta spec, o changelog e três mensagens do dono **sem
> ninguém somar 6 + 28 + 1**. A razão é a forma: ele viveu sempre **dentro de
> uma frase** ("6 `tematico` / 29 `valorativo` / 1 sem estado"), nunca numa
> tabela com uma linha de total. Numa tabela, o total é uma célula que alguém
> escreve; numa frase, é uma conta que ninguém faz. **A conferência mais
> simples disponível foi a única não feita**, e ela sobreviveu a várias
> revisões cuidadosas de coisas muito mais difíceis.
>
> **Regra prática:** partição de população vai em TABELA com linha de total, e
> o total é conferido contra o N conhecido. Vale para qualquer contagem que
> particione os 35 filmes, as 105 células de bucket ou as 30 células de eixo.


<!-- SPEC.md linhas 1705–1777 · origem: 2.7 AVISO — o gabarito de contagem à mão dos 5 casos SUBESTIMA (2026-08-30) -->

**ATUALIZAÇÃO (2026-08-31): os outros três casos foram refeitos sob o
protocolo P1–P7 completo, com resolução humana onde o modelo divergiu. Os
cinco casos estão todos refeitos agora.**

| caso | gabarito §12 | valor refeito (P1–P7) | fonte |
|---|---:|---:|---|
| `wonka` neg — *Fotografia e efeitos visuais criticados* | 1 | **sustenta 3, contradiz 1** | leitura integral direta pelo dono (32/32), sem estágio reduzido |
| `talk-to-me-2022` neg — *Diálogos e tom juvenil artificiais* | 2 | **sustenta 2, contradiz 0** | leitura em duas etapas, resolução humana — ver §"Confiabilidade medida..." abaixo |
| `napoleon-2023` med — *Batalhas visualmente impressionantes* | 13 | **sustenta 12, contradiz 1** | idem |

`talk-to-me-2022` fechou no MESMO valor do gabarito antigo (2). **Isto é
coincidência de destino, não validação do protocolo antigo** — os dois
métodos chegaram lá por caminhos diferentes: um por casamento de
palavra-chave numa subamostra do bucket (o método que §2.7 mediu subcontar
`cats-2019` em −8 e `interstellar` em −6, sem garantia nenhuma de acerto por
método, só por sorte de amostra); o outro por leitura completa das 40
reviews com frase literal registrada e resolução humana em cada
discordância. Concordarem no número não dá crédito ao protocolo antigo.

**Consequência para as duas reprovações, medida:** recomputando as mesmas
tabelas com os dois casos corrigidos e os três outros inalterados, o erro
absoluto médio contra o gabarito vira

| | gabarito §12 | gabarito com 2 de 5 corrigidos |
|---|---:|---:|
| `mencoes_aproximadas` | 3,00 | **3,80** |
| contagem por eixo | 3,60 | **2,80** |
| verificação binária | 5,20 | **2,40** |

**As duas reprovações se invertem sob a correção parcial**, e a direção do erro
residual é conhecida: os três casos não relidos estão, pelo mesmo mecanismo,
provavelmente baixos também — e corrigi-los para cima favorece ainda mais os
métodos que contam mais alto. **Nenhuma das duas reprovações deve ser tratada
como estabelecida enquanto os cinco não forem relidos por inteiro.**

**O que continua de pé sem depender do gabarito:** o argumento conceitual contra
a contagem por eixo (o eixo é **superconjunto** do tema, então trocar o número
do tema pelo do eixo é erro de categoria, não de calibração), a colisão de
barras em 28% dos bullets, os dois bullets com barra zero; e, contra a
verificação binária, a reprodutibilidade entre execuções idênticas
(Jaccard 0,70; `wonka` de 4 para 1), o recall de `contradiz` de 1 em 5, e o
custo real medido de US$ 23,82 em 300 filmes com 3 votos.

**Protocolo exigido para qualquer refação (P1–P7):** leitura **integral** do
bucket (todas as 32–40 reviews), **sem** casamento por palavra-chave, julgando
no idioma original, contra o **tema E a paráfrase publicada** (ver a revisão de
P4 abaixo), com três valores (`sustenta`/`não sustenta`/`contradiz`) e a frase
literal de cada review contada. Ver `docs/arquivo-de-estudos/classificacao/AUDITORIA_POPULACAO_E_GABARITO.md`
§Entrega 4.

### P4 REVISADO (2026-08-31) — julgar contra o tema E contra a paráfrase

A versão anterior de P4 dizia *"contando no nível do **tema** (não do
exemplo)"*. **Está errada, e a calibração mostrou como.**

O que o leitor vê na tela é o par tema + `exemplo_parafraseado`, e é a
paráfrase que carrega a afirmação específica. Julgar só contra a formulação
curta do tema perde reviews que sustentam o que o produto de fato afirma.

**O caso que forçou a correção.** Em `wonka`/negativas, a paráfrase publicada
diz literalmente *"cenários artificiais"*, e a review [11] (alemão) diz *"Alles
ist mir einen Ticken zu künstlich"* com um exemplo visual concreto — o
chocolate que "não tem mais nada a ver com chocolate". Julgando só contra o
título *"Fotografia e efeitos visuais criticados"*, isso sai como `não
sustenta`; julgando contra a paráfrase, é `sustenta`. O dono contou `sustenta`;
a leitura por modelo contou `não sustenta`.

**P4 passa a ser:** o julgamento é contra o tema **e** contra o
`exemplo_parafraseado` publicado. Uma review que sustenta o que a paráfrase
afirma sustenta o bullet, mesmo que a formulação curta do tema não capture
aquilo. O quantificador da paráfrase continua **não** sendo testado (P3): se
ela diz "para a maioria", a pergunta segue sendo se ESTA review afirma a coisa.


<!-- SPEC.md linhas 1845–1864 · origem: Achado novo — o modelo nunca usa "não sei julgar", mesmo devendo -->

**Recomendação para os próximos gabaritos da expansão:** reforçar a
instrução de abstenção no prompt com este caso como exemplo concreto —
"uma review em árabe/idioma pouco comum não é candidata automática a
`não sustenta`; se a confiança de tradução for baixa, declare `não sei
julgar`" — em vez de deixar a regra genérica ("é preferível a chutar")
sem um exemplo que mostre a falha real já observada.

**Consequência de desenho, registrada:** gabarito não deve ser produzido por
modelo sozinho. O desenho adotado é de duas etapas — o modelo lê o bucket
inteiro; o humano lê uma folha reduzida contendo (i) tudo que o modelo marcou
`sustenta`/`contradiz`, (ii) tudo que ele marcou `não sustenta` **com** o
assunto tocado, e (iii) uma amostra cega de controle das `não sustenta` que nem
tocaram o assunto, misturada sem marcação (semente registrada). **Onde houver
divergência, o veredito humano vale** — o gabarito existe para julgar saída de
modelo, e deixá-lo ser decidido por modelo onde há divergência com o humano é
a circularidade que a calibração existe para quebrar. A confiabilidade
variável por tipo de julgamento (acima) é o motivo estrutural de a decisão
final ser sempre humana: um fator de correção fixo não existe para aplicar
no lugar da leitura.


<!-- SPEC.md linhas 2111–2211 · origem: 2.10 Regras de TESTE e de AMBIENTE (v1.9.34) -->

## 2.10 Regras de TESTE e de AMBIENTE (v1.9.34)

Saíram de defeitos reais desta versão, e entram como **regra do projeto**, não
como nota de sessão — as três primeiras porque um trap que passa pelo motivo
errado é pior que trap nenhum (ele dá garantia falsa), e a quarta porque é a
segunda reincidência no mesmo arco.

### Traps de escopo — as três regras

O projeto trava escopo de harness **por teste**, envenenando pontos de entrada
com `pytest.fail` e rodando o harness de verdade (v1.9.21, v1.9.29). Ao
escrever o trap da v1.9.34, dois dos alvos estavam errados e o teste passava
assim mesmo. As regras que evitam isso:

1. **Trap vazio é pior que trap ausente — `assert hasattr` ANTES de
   envenenar.** A lista da v1.9.34 tinha `synthesize.build_output`, que **não
   existe**, e um `continue` de conveniência escondia isso: a entrada dava
   impressão de cobertura e não cobria nada. Um nome que some num refactor
   transforma o trap em decoração silenciosa. O `assert` faz o teste reprovar e
   pedir correção do nome.
2. **`from x import y` faz o poison em `x.y` NUNCA interceptar.** O alvo passa a
   ter duas ligações: `x.y` e `modulo_que_importou.y`. Envenenar o módulo de
   origem não toca a segunda. **Quem escreve um trap tem de verificar COMO o
   alvo é importado** por quem o chama — `grep "import <alvo>"` antes de
   confiar no `monkeypatch`.
3. **Alvo "proibido" que na verdade é chamada LEGÍTIMA vira teste que afirma o
   contrário.** `selecao.selecionar` estava na lista de proibidos da v1.9.34 e
   não deveria: `pipeline.amostra_do_bruto` PRECISA chamá-la para saber quais
   reviews a síntese leu (zero rede, tudo do disco). Remover a entrada em
   silêncio convida a próxima pessoa a "consertar" o trap reintroduzindo-a. A
   saída é um teste NOMEADO que afirma que a chamada acontece e diz por quê
   (`test_a_selecao_E_chamada_e_isso_e_CORRETO`).

### Ambiente — função de biblioteca não altera o ambiente do processo

**REGRA: carregar `.env` (ou qualquer mutação de `os.environ`) é
responsabilidade do `main`, nunca de uma função de biblioteca.**

**Segunda reincidência no mesmo arco.** A primeira foi em
`classificar()`/`classificar_passe()`, registrada como dívida e **não corrigida
aqui** (fora de escopo — fica como está, com a regra escrita ao lado). A
segunda foi `aplicar_lei_margem.aplicar()`, que chamava `load_dotenv` e
**poluía a suíte**: as chaves de API entravam no ambiente do processo e três
testes de `test_provider.py` (auto-detecção de provider por chave presente)
**passavam isolados e falhavam no conjunto**. Corrigida movendo a chamada para
`main()`.

O sintoma é sempre o mesmo e é caro de diagnosticar: teste verde sozinho,
vermelho na suíte, sem relação aparente com o que mudou. A fronteira do efeito
colateral é o `main` porque é o único lugar onde ele é uma decisão do usuário
e não um efeito surpresa de um import.

### [v1.9.37] Frontend — constante de módulo lida por `render()` vai no TOPO

**REGRA: em `frontend/js/filme.js`, toda constante de módulo que o `render()`
alcança declara-se no topo do arquivo, junto das demais, NUNCA depois da
chamada `render(film)`.**

`var` hoista a **declaração** e não a **atribuição**. Uma constante declarada
abaixo da chamada chega `undefined` dentro das funções que o render aciona — e
o sintoma **não** é `ReferenceError`, é um `undefined` silencioso que só
estoura quando alguém o indexa. Funções não têm o problema: declarações de
função hoistam inteiras, e foi por isso que nos dois casos o render *quase*
funcionou.

**Duas ocorrências no mesmo arquivo neste arco, as duas achadas só por olhar a
tela, com a suíte verde:**

| versão | constante | como apareceu |
|---|---|---|
| v1.9.26 | o veredito | reordenação da página |
| v1.9.37 | `ABERTURA_DA_COLUNA` | bloco de condições estourava inteiro |

**TRAVADA POR TESTE, e a trava foi verificada contra o defeito real:**
`tests/test_frontend_constantes_hoisted.py`. Ela lê a fonte, acha a linha de
`render(film)` e reprova qualquer `  var NOME_MAIUSCULO =` declarado depois
dela **e lido em outro ponto do arquivo**. Reintroduzir o defeito da v1.9.37 a
faz falhar com a linha exata; desfazer a reintrodução a faz passar.

**O escopo está declarado no próprio teste, para que a trava não seja lida
como mais forte do que é:** é varredura textual, não parser de JS. Cobre a
convenção que o arquivo usa (`var` maiúsculo no nível do IIFE); não cobre
`let`/`const` (o arquivo é ES5 por compatibilidade) nem constantes internas a
funções, que não têm o problema.

**Ela tem guarda de TRAP VAZIO** (a regra 1 desta mesma §2.10, v1.9.34 —
*"trap vazio é pior que trap ausente"*; **o texto dizia "lição da v1.9.25", e
a atribuição estava errada:** conferido em
`tests/test_frontend_constantes_hoisted.py`, o docstring da guarda repete o
mesmo "v1.9.25", então a divergência está no código e na spec ao mesmo tempo —
a regra é da v1.9.34, que é onde ela está enunciada): um teste à parte falha
alto se o arquivo sumir ou se a chamada `render(film)` mudar de forma — sem
ele, a trava passaria a verificar nada e continuaria verde.

**Achado de passagem, registrado e NÃO corrigido:** a mesma varredura
encontrou `BANDAS_QUANTIFICADOR` declarada e **nunca lida** — código morto. Fica
como dívida conhecida (`xfail` nomeado no teste), fora do escopo da sessão de
publicação.

---


<!-- SPEC.md linhas 8681–8691 · origem: 5. Critérios de aceite da v1 -->

## 5. Critérios de aceite da v1

1. Filme popular (ex: `oppenheimer-2023`): **os três buckets em `estado_piso: completa` com os 40 preenchidos** (v1.9.0; era "10 níveis completos, 10 válidas cada"), temas coerentes, zero spoilers na saída (verificação manual).
2. Filme de fanbase "review curta" (ex: `cidade-de-deus`): o filtro de comprimento descarta reviews curtas em volume, a coleta fecha os níveis dentro do teto de paginação, e a análise permanece útil com observações corretamente escopadas. *(Reescrito em v1.1.4 — ver nota abaixo; o critério original presumia cascata de relaxamento/modo degradado, que `cidade-de-deus` não aciona por ser coberto demais por nível. A demonstração da cascata e do modo degradado é atribuída ao critério 3, onde ocorre de fato.)*
3. Filme obscuro (a escolher): modo degradado severo — piso de 3 por bucket respeitado, bucket sem análise renderiza aviso (contagem + `reviews_url`) e não inventa temas; a cascata de relaxamento por nível (`filtro_aplicado` assumindo 50/0) é exercitada aqui.
4. **Nenhum texto truncado chega ao LLM:** teste com filme contendo reviews longas colapsadas; verificar que todas as reviews enviadas ao LLM têm texto completo ou foram descartadas com registro.
5. Segunda execução de qualquer filme: **zero requisições de rede** (100% cache).
6. Orçamento de requisições por filme novo — **reescrito na v1.9.1**: teto absoluto de **paginação** = **48** (3 buckets × 16 páginas de orçamento — era 40 = 10 níveis × 4 na v1.9.0, computado por nível; a v1.9.1 muda a unidade de contagem para bucket, não o gasto real, que segue medido, não projetado), + 1 histograma + truncadas completadas + busca de slug. **Valor típico MEDIDO sob a v1.9.0 (2026-08-07, 3 filmes): 58-65, média 61** — 32-33 de paginação, 24-33 de completamento, 1 de histograma; abaixo dos 83 (`cure`) e 68 (`cidade-de-deus`) da v1.8.2, apesar de ~50% mais material bruto coletado. **Valor MEDIDO sob a v1.9.1, recoleta INCREMENTAL sobre o bruto da v1.9.0 (2026-08-07, 3 filmes): 17-26, média 21** — não comparável 1:1 com os 61 da v1.9.0 (que foi coleta do zero); é o custo real de alargar uma coleta já existente para o orçamento maior, o caso de uso que a incrementalidade do bruto (§3[B']) foi desenhada para servir. Tabela completa e o achado residual (`cidade-de-deus`/`medianas` fechou 37/40, não 40/40) em §3[B], "Resultado MEDIDO da recoleta v1.9.1". **Valor ESPERADO sob a v1.9.2** (parada determinística — orçamento sempre gasto, salvo esgotamento real): ~32→48 páginas/filme, ~61→~85 requisições numa coleta DO ZERO — custo aceito explicitamente em troca de determinismo (§3[B]). **Valor MEDIDO (2026-08-07, recoleta incremental sobre o bruto da v1.9.1, 3 filmes): 13-15, média 14,3** — não comparável ao valor esperado de coleta do zero, mesmo motivo das sessões anteriores (a maior parte do material já estava cacheada; o custo novo concentrou-se nas posições profundas, nunca visitadas antes). **Resultado central: os 3 filmes fecharam 40/40/40 nos 9 buckets — o déficit residual da v1.9.1 (`cidade-de-deus`/`medianas`, 37/40) fechou.** Tabela completa em §3[B], "Resultado MEDIDO da recoleta v1.9.2". **Valor MEDIDO sob a v1.9.3 (coleta DO ZERO, 3 filmes, harness de lote, 2026-08-07): 67-73 requisições, média 70,0** (`parasite-2019`=67, `eighth-grade`=70, `everything-everywhere-all-at-once`=73) — a primeira medição do zero desde a v1.9.0, com o coletor da v1.9.2 (parada determinística + posicionamento estratificado). **Correção de registro (achado da diagnose pós-Entrega 2, ver §3[H] "Diagnose do déficit de buckets"): os 9 buckets fecham `estado_piso=completa` (n≥15 em todos), mas só 5 dos 9 atingem a COTA cheia de 40** — `parasite-2019` fechou 28/40/32 (negativas/medianas/positivas), `eighth-grade` 38/39/40, `everything-everywhere-all-at-once` 40/40/40; NÃO é "40/40/40 nos 9 buckets" como uma versão anterior deste parágrafo afirmou incorretamente, contradizendo a própria tabela do relatório da Entrega 2. Diagnose completa (motivo de parada, páginas orçadas vs. gastas, descarte discriminado, teste da hipótese de spoiler) em §3[H]: os 4 déficits são 100% ESCASSEZ (filtro `min_chars=150` descartando reviews curtas — 63-87% do bruto de cada nível deficitário — sobre um bruto onde TODAS as páginas orçadas retornaram conteúdo, zero sondagem caindo em página vazia); nenhum é DESPERDÍCIO. Tempo de parede: 499,5s para os 3 (média 166,5s/filme, ~2,8 min/filme, `DELAY_SECONDS=2.0`). Disco do bruto persistido: 240-264 KB/filme, média 248 KB/filme. **Extrapolação para 30 filmes: ~2100 requisições, ~83 min (~1,4 h), ~7,3 MB. Para 50 filmes: ~3500 requisições, ~139 min (~2,3 h), ~12,1 MB** — ambos bem abaixo do teto de ~4h que dispararia parada e pedido de decisão ao usuário (§3[H]). **Achado lateral não previsto:** recoletando os MESMOS 3 filmes do zero ~2h depois com os MESMOS parâmetros, `n` final por bucket variou (`parasite-2019`/positivas: 36→32; `eighth-grade`/negativas: 37→38, medianas: 37→39) — o site é um alvo VIVO sob `by/added`; buckets que fecham exatamente na cota mascaram essa variância, buckets abaixo dela a revelam. Registrado como achado, não corrigido (fora de escopo desta sessão).

---

