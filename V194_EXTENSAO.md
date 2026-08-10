# v1.9.4 — Extensão de orçamento por déficit

**Data:** 2026-08-08 · **Spec:** [SPEC.md](SPEC.md) v1.9.4 (delta escrito ANTES da implementação)

Fora de escopo e não tocados: `MIN_CHARS`, cascata, fronteiras, cota, alocação
proporcional, `ORCAMENTO_PAGINAS_POR_BUCKET` (a base continua **16**),
ordenação, reserva de profundidade, schema de eixos, lift, narrador, editor,
estratificação por `pagina_origem`. Nenhum `resultado/*.json` republicado.

---

## Entrega 1 — Extensão por déficit

`src/espectro24/extensao.py`, ligado ao pipeline por um gancho que
`coletar_superset` chama **entre o orçamento base e a persistência**. O
coletor continua sem saber o que é um bucket: quem passa o gancho é o
`pipeline`, a única camada que já sabia.

**A regra, como implementada:**

1. gasta o orçamento base (16 páginas/bucket) exatamente como antes;
2. se o bucket fecha a base com menos válidas que a meta com folga
   (`40 × 1,25 = 50`), concede extras **uma a uma** até
   `TETO_EXTENSAO_PAGINAS = 24`, aos níveis em déficit;
3. para na meta, no teto, ou quando todo nível do bucket devolve página vazia.

**Zero estimativa.** Os dois números que a regra consulta são medidos: quantas
válidas o bucket tem agora — contadas pelo **mesmo `_cascade_pool` que a
seleção usa**, não por uma contagem própria — e quais níveis estão abaixo do
próprio alvo. O desenho preditivo está rejeitado com racional na spec: as
páginas são log-espaçadas desde a v1.9.2 e o rendimento do bloco raso não
descreve o do profundo; e a parada por ALVO, removida na v1.9.2, já era uma
heurística otimista decidindo orçamento — reintroduzi-la sob outro nome, dois
releases depois, repetiria o erro.

**Quarto uso de `redistribuir_deficit`, não um mecanismo novo.** A cada
página, o plano das extras restantes é montado por `alocar_bucket` sobre os
níveis em déficit e passado por `redistribuir_deficit` com a *liveness* do
nível como disponibilidade — é essa segunda chamada que move a cota de um
nível esgotado para um que ainda rende. Um teste espiona as duas funções e
falha se alguém escrever um segundo caminho de código.

**Peso por DÉFICIT, não por histograma.** Todos os outros usos de
`alocar_bucket` pesam pelo histograma. Aqui isso daria todas as extras ao
mesmo nível populoso de baixo rendimento que a diagnose apontou como
*amplificador* do problema — repetiria a concentração em vez de corrigi-la.

**Onde as extras caem.** Anexadas, nunca recalculando a divisão raso/profundo
(se recalculasse, as posições geométricas mudariam e a base deixaria de ser
prefixo exato da coleta estendida — há teste para isso): primeiro os buracos
dentro do intervalo já confirmado, que por monotonicidade **têm conteúdo
garantido**; depois consecutivas além do mais profundo já buscado, onde uma
página pode vir vazia e, vindo, mata o nível.

Uma decisão de implementação que o briefing não fixava: **a página extra
completa as truncadas que ela mesma traz.** Review sem texto completo é
descartada pela seleção (§3[C2]) — sem isso a extensão gastaria página sem
render válida nenhuma.

### Telemetria (`meta.json → extensao_por_bucket`)

Por bucket: `paginas_base`, `paginas_extensao`, `extras_por_nivel`,
`motivo_parada` (`meta_atingida` | `teto_extensao` | `material_esgotado`),
`n_validas_pos_base`, `n_validas_pos_extensao`, `meta`. Mais
`paginas_base_por_nivel` e `paginas_extensao_por_nivel` no topo — a soma das
duas é `paginas_gastas_por_nivel`, sempre (há teste).

### Testes

**764 passando** (eram 706): 26 da regra com dublês, 8 do posicionamento das
extras, 8 da fiação ponta a ponta, 22 do guard-rail.

Os obrigatórios do briefing, um a um:

| exigência | teste |
|---|---|
| não dispara quando a base fecha a meta | `test_nao_dispara_quando_a_base_ja_atinge_a_meta`, `test_material_farto_nao_dispara_extensao_e_nao_gasta_pagina_extra` |
| os que já fechavam gastam exatamente 16 | `test_base_continua_gastando_o_orcamento_de_sempre` |
| respeita o teto de 24, nunca excede | `test_extensao_respeita_o_teto_e_nunca_o_excede`, `test_material_pobre_dispara_a_extensao_ate_o_teto` |
| só a níveis em déficit | `test_extra_nunca_vai_a_nivel_que_ja_fechou_o_proprio_alvo` |
| nunca a nível esgotado | `test_extra_nunca_vai_a_nivel_esgotado`, `test_redistribuir_deficit_move_a_extra_de_nivel_morto_para_vivo` |
| reuso de `redistribuir_deficit` | `test_a_escolha_da_extra_passa_por_redistribuir_deficit` (monkeypatch espião) |
| os três motivos de parada | `test_motivo_meta_atingida_no_meio_da_extensao`, `test_motivo_teto_extensao`, `test_motivo_material_esgotado_quando_todo_nivel_morre` |
| degenerado: todos os níveis esgotados | `test_bucket_com_todos_os_niveis_ja_esgotados_na_base`, `test_bucket_vazio_nao_quebra` |
| degenerado: meta exatamente na última extra | `test_meta_atingida_exatamente_na_ultima_extra_permitida` + o espelho (49 de 50 → `teto_extensao`) |
| guard-rail detecta violação injetada | `test_a_varredura_detecta_violacao_injetada` (9 formas de violação) |

Um achado durante a escrita dos testes, que mudou a fixture: um filme cujas
reviews sejam **todas** curtas não produz déficit nenhum — a cascata (§3[C])
desce o degrau e passa a contá-las como válidas. O déficit só existe quando há
material longo o bastante para o degrau de 150 vigorar, mas pouco dele. A
fixture que reproduz a diagnose é 1 review longa + 11 curtas por página.

### Uma regressão que a extensão introduziu, encontrada e corrigida

`--offline` (reexecução 100% cache, garantia anterior a esta versão) passou a
**quebrar** em todo filme coletado antes da v1.9.4: a extensão pedia uma
página que nunca esteve no cache e o `FetchError` subia pelo pipeline inteiro.
Reproduzido contra dado real — `longlegs`, página 9 do nível 2,0★.

A guarda devolve o `extensao_por_bucket` já gravado em disco, sem buscar nada.
Não devolver nada apagaria o registro (`persistir` **sobrescreve** o meta) e
devolver zeros inventaria uma extensão que não aconteceu. Verificado contra
dado real depois do fix: 0 requisições de rede, 71 de cache.

### Uma limitação declarada, não corrigida

**O teto de 24 é por EXECUÇÃO, não pela vida do bruto.** A contabilidade
posicional não é persistida, então reexecutar um filme de propósito volta a
ter 8 extras disponíveis e gasta parte delas em posições já buscadas —
cacheadas, sem custo de rede, mas sem material novo. Corrigir exigiria um
registro posicional persistente; o checkpoint do lote (§3[H]) já evita a
reexecução acidental. Registrado na spec.

---

## Entrega 3 — Recoleta seletiva

9 filmes (`obsession-2026` fora, como pedido: o déficit dele é escassez
genuína — 214 notas no total —, mecanismo diferente, a extensão não teria o
que buscar). Incremental sobre o bruto existente: as páginas da base já
estavam no cache do lote da v1.9.3, então o custo de rede medido é o das
páginas de **extensão** e do completamento das truncadas que elas trazem.

| filme | dom. | antes (n/m/p) | depois | extras (n/m/p) | motivo (n/m/p) | rede |
|---|---|---|---|---|---|---|
| `wicked-2024` | pos | 30/32/**20** | 36/40/**24** | 8/8/8 | teto/teto/teto | 26 |
| `avengers-endgame` | pos | 40/40/**34** | **40/40/40** | 3/3/8 | meta/meta/teto | 20 |
| `talk-to-me-2022` | pos | 28/24/**23** | 40/31/**34** | 8/8/8 | teto/teto/teto | 30 |
| `aftersun` | pos | 40/40/**38** | **40/40/40** | 0/0/8 | meta/meta/teto | 9 |
| `pearl-2022` | pos | 15/24/**30** | 26/33/**35** | 8/8/8 | teto/teto/teto | 27 |
| `parasite-2019` | pos | 28/40/**32** | **40/40/40** | 8/7/8 | teto/meta/teto | 32 |
| `wonka` | pos | 18/23/**32** | 32/25/**38** | 8/8/8 | teto/teto/teto | 25 |
| `hereditary` | pos | 28/31/**34** | 36/40/**39** | 8/8/8 | teto/teto/teto | 24 |
| `shutter-island` | pos | 30/36/**36** | **40/40/40** | 8/7/8 | teto/meta/teto | 29 |

**Agregado**

| | antes | depois |
|---|---|---|
| bucket dominante fechando 40 | 0 de 9 | **4 de 9** |
| buckets abaixo de 40 | 22 de 27 | **12 de 27** |
| dominante MENOR que outro bucket do mesmo filme | 5 | **3** |
| `estado_piso = completa` | 27 de 27 | 27 de 27 |

**Custo:** 222 requisições nos 9 filmes (**24,7/filme**, contra as ~78/filme
de uma coleta do zero), 603 servidas de cache, 551 s de parede (~9 min).
Menor: `aftersun`, 9 requisições — dois dos três buckets fecharam a meta na
base e não estenderam. Maior: `parasite-2019`, 32.

**Rendimento das páginas extras: 188 concedidas → 225 válidas ganhas**, ou
~10% do material bruto (a ~12 reviews/página). Exatamente a faixa de 10-20%
que a diagnose mediu para esta classe de filme — a extensão não descobriu
material melhor, ela comprou mais material do mesmo.

**Motivos de parada:** 21 `teto_extensao`, 6 `meta_atingida`, **zero
`material_esgotado`**. Coerente: são os filmes mais populares do catálogo, e
nenhum deles chega perto de esgotar o Letterboxd. O caminho de
`material_esgotado` continua exercitado só em teste — é o mesmo estado que
`obsession-2026` produziria, e ele ficou de fora por decisão.

### Seletividade — a evidência de que a extensão não é um aumento de orçamento disfarçado

`aftersun` é o caso limpo: `negativas` e `medianas` atingiram a meta dentro
da base e receberam **zero** extras; só `positivas` estendeu. `avengers-endgame`
gastou 3 extras em dois buckets e 8 no terceiro. A extensão dispara por
bucket, medindo o déficit de cada um.

### O que a recoleta NÃO resolveu, e por quê

- **`wicked-2024`/positivas: 20 → 24, ainda o menor dos três.** 8 páginas
  extras renderam +4 válidas (~4%), pior que os 6,9% que a diagnose mediu.
  É o pior rendimento dos 35 filmes; fechar 40 exigiria da ordem de 40-50
  páginas no bucket, não 24.
- **`hereditary` passou a ter o dominante menor que outro bucket** — 39
  contra 40 em `medianas`, diferença de 1 review. É efeito colateral honesto
  da extensão ter ajudado mais `medianas` que `positivas`, e a diferença é
  irrelevante para precisão (±7,9pp contra ±8,0pp a 1 EP).
- **`talk-to-me-2022`/medianas: 24 → 31.** O bucket morno tem 2 níveis sob a
  opção C, então 8 extras se espalham por menos níveis e batem antes no
  material de baixo rendimento.

**A tensão original — dominante medido com menos precisão que o minoritário —
caiu de 5 filmes para 3, não a zero.** Os dois que sobraram do conjunto
original (`wicked-2024`, `talk-to-me-2022`) são os dois piores rendimentos da
classe.

---

## Entrega 2 — Correção e declaração são CAMADAS

Registrado na spec (§3[B], "Correção e declaração são CAMADAS, não
alternativas") e confirmado pela recoleta.

**12 dos 27 buckets seguem abaixo de 40.** O motivo, medido, é o mesmo em
todos os 12: **`teto_extensao`** — nenhum esgotou material. Não é falta de
reviews no Letterboxd; é o teto de custo funcionando como projetado. Sem
teto, esses 12 buckets continuariam paginando enquanto o rendimento de ~10%
fosse pagando, e o custo de um lote deixaria de ser previsível.

O enquadramento que fica registrado:

- a **extensão** encolhe a CLASSE de buckets sub-40 — atacou os casos em que
  o material existia e o orçamento é que acabava cedo (22 → 12 buckets, 0 → 4
  dominantes fechando a cota);
- o **piso escalonado** (§3[C3]) e o **denominador visível** absorvem o
  RESÍDUO. Os 27 buckets estão em `estado_piso = completa` (n ≥ 15), antes e
  depois: mesmo os que ficaram em 24 ou 25 entregam tema, frequência e
  quantificador, com o `n` real à vista.

**A declaração honesta continua sendo o mecanismo final, não a alternativa
rejeitada.** Nenhuma quantidade de orçamento a torna dispensável: sempre
existirá `obsession-2026` (214 notas no total) para o qual nenhum orçamento
acha material que não existe. A extensão muda **quantos** buckets caem no
resíduo, nunca **se** o resíduo precisa ser declarado.

Uma consequência de custo que o briefing não fixava e que a implementação
tornou concreta: a regra é **por bucket**, então um filme deficitário estende
os três buckets — até 24 páginas extras por filme, não 8. Nos 9 filmes isso
deu 188 extras, média de 20,9 por filme.

---

## Entrega 4 — Guard-rail do adaptador

`tests/test_guardrail_adaptador.py` varre `src/` **e `scripts/`** procurando
import/instanciação de SDK de LLM e chamadas diretas de geração fora de
`src/espectro24/synthesize.py`. Falha com arquivo e linha.

**A causa de o bug ter reaparecido não era descuido — era uma lacuna do
adaptador.** `_deepseek_call` devolvia só o texto, e todo script de medição
precisa de `usage` para reportar custo real. Era essa falta que empurrava cada
script novo a reimplementar o transporte e, no caminho, esquecer
`thinking: disabled`. Um guard-rail que só proibisse o desvio, sem fechar a
lacuna, seria uma regra que os scripts continuariam tendo motivo para violar.

Adicionados ao adaptador (aditivos, nenhum caminho de produção alterado):
`deepseek_client()` (fábrica reutilizável, para chamadas concorrentes),
`deepseek_resposta()` (resposta inteira, com `usage`) e `deepseek_uso()`.
`scripts/gate_taxonomia.py` foi reparado para usar os três — verificado por
chamada real.

**Allowlist literal, de 3 arquivos, cada um com o motivo escrito ao lado:**
`diagnostico_fluencia.py`, `diagnostico_fluencia_v2.py`, `compare_models.py`.
Eles chamam o SDK direto de propósito — o `thinking_budget` e a escolha de
modelo **são o objeto de estudo** deles, e passar pelo adaptador (que fixa
exatamente esses parâmetros) tornaria o experimento impossível. Um teste
compara a allowlist contra o conjunto literal, então acrescentar um arquivo é
uma mudança deliberada e revisável.

`tests/` fica fora da varredura (importa o SDK para dublês, nunca chama de
verdade). A exceção é a fixture do próprio guard-rail, que injeta 9 violações
sintéticas num diretório temporário e confirma a detecção — sem ela, um
guard-rail quebrado passaria igual a um que não tem nada a detectar.

**O que ele não garante:** checa o CAMINHO, não os parâmetros. Quem replicar
o transporte com outro nome de variável pode escapar da varredura textual. É
uma rede de classe de regressão, no mesmo estatuto das checagens do §E2 —
cobre o modo de falha observado, não todo modo concebível.

---

## Entrega 5 — Frequência do estado "sem contraste temático"

MEDIÇÃO apenas. Sobre as classificações que o gate já deixou em disco (8
eixos, 859 reviews, 14 filmes com pelo menos 15 reviews por bucket). Nada foi
reclassificado. `scripts/contraste_v194.py`.

| margem | filmes com ZERO eixos acima da margem | esperado sob o nulo |
|---|---|---|
| **15 pp** | **1 de 14** — `barbie` | 2,2 filmes (p5=0, p95=4) |
| 20 pp | 3 de 14 — `barbie`, `napoleon-2023`, `perfect-days-2023` | 6,8 (p5=4, p95=10) |

**Resposta direta: é caso de borda, não estado comum — 1 em 14.**

**Mas o "1 em 14" é um PISO, não uma estimativa, e a diferença importa para o
desenho.** A coluna do nulo é o que dá a leitura: embaralhando o rótulo de
bucket dentro de cada filme (zero associação real, por construção), 2,2 filmes
ficariam sem contraste — *mais* que o 1 observado. Ou seja, com 20 reviews por
bucket o ruído **manufatura separadores**, e "tem pelo menos um eixo acima de
15 pp" é um sinal fraco de contraste real. O número honesto de filmes
`contraste: valorativo` é ≥ 1, provavelmente maior, e só uma medição a n=40
por bucket o fixa.

Os dois filmes que caem já a 20 pp — `napoleon-2023` e `perfect-days-2023`,
ambos com melhor lift de exatamente 15,0 pp — são os candidatos seguintes: um
filme cujo melhor separador é 15,0 pp está dentro do ruído a n=20.

Detalhe por filme em `resultado/v194-recoleta/contraste.json`.

---
