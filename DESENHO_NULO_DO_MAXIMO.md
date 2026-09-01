# Desenho da simulação — nulo do máximo sobre 30 células

**Registrado ANTES de rodar.** Nenhum resultado nesta página. Os números vivem
em `ESTUDO_MARGEM_20PP.md`. Zero chamada de LLM; `resultado/` só é lido.

---

## Por que este nulo, e não os que já existem

Três medições de nulo/reamostragem já existem no projeto e **nenhuma delas é
esta**:

- **§2.5 da SPEC (nulo de permutação, 2000 rodadas).** Permuta bucket dentro
  de cada filme e conta **quantos PARES (eixo, bucket) do catálogo inteiro**
  cruzam a margem sob o nulo, contra quantos cruzam no observado. É uma taxa
  de ruído **por célula, agregada sobre o catálogo** — não a distribuição do
  máximo por filme, que é a estatística que o estado `contraste` de fato usa.
- **`ESTUDO_CATALOGO_35.md` §8 e `MEDICAO_VERIFICACAO_BINARIA.md` Entrega 2
  (bootstrap).** Reamostram a amostra observada e perguntam "este achado
  sobrevive a outra amostra da MESMA população?". Isso é variância em torno do
  observado, **não** a distribuição sob "não há contraste nenhum".

O que falta, e é o que este desenho produz: **a distribuição do máximo do lift
sobre as 30 células, sob a hipótese nula de que nenhum eixo se associa a
nenhum bucket.** É a estatística que o critério publicado compara com 20pp, e
é a única que responde "20pp é um limiar alto ou baixo?".

---

## 1. População

Para cada um dos **35 filmes** publicados (os 36 arquivos de `resultado/*.json`
menos `como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual`,
que não tem bloco `eixos`):

```
população(filme, bucket) = amostra_do_bruto(slug, coleta=resultado/<slug>.json.coleta)
                           ∩ consenso_verificado.jsonl
```

Isto é **exatamente** o que `eixos.montar_bloco` conta em produção
(`_filtrar_pela_analisada` sobre o consenso verificado), com a cobertura de
100% de §2.8 — a melhor base que o projeto já teve. Não é `consenso.jsonl`
cru, que acumula a seleção antiga e a nova lado a lado, nem o
`consenso_verificado.jsonl` inteiro (5.371 linhas), que tem o mesmo acúmulo.

**Validação obrigatória antes de qualquer resultado do nulo:** esta
reconstrução tem de reproduzir **16 `tematico` / 19 `valorativo`** e os **10
filmes que trocam de estado** listados em `ESTABILIDADE_10_FLIPS.md`. Se não
reproduzir, o desenho está errado e nada mais é reportado.

## 2. A estatística

Idêntica à de produção (`src/espectro24/eixos.py`), sem reimplementação da
regra:

```
freq(eixo, bucket) = |reviews do bucket com o eixo| / |reviews do bucket|
lift(eixo, bucket) = freq(eixo, bucket) − max(freq(eixo, outros dois buckets))
T = max sobre as 30 células (10 eixos × 3 buckets) de lift
contraste = "tematico"  ⟺  T >= margem
```

`livre` **fora** das 30 células (é o que o código faz: `if eixo != LIVRE`).
Aritmética exata em `Fraction`, comparação `>=` — a semântica da v1.9.15. `T`
é a estatística de teste; 20pp é o valor crítico que o produto usa hoje.

## 3. O embaralhamento — o que permuta e o que NÃO permuta

Dentro de **cada filme**, tomo a lista das reviews classificadas (com seus
conjuntos de eixos) e **permuto o rótulo de bucket** entre elas.

**Preservado exatamente (não é reamostrado, não é sorteado):**

- o conjunto de eixos de cada review, intacto e junto — logo toda a
  **dependência entre eixos da mesma review** (`impacto_emocional` e
  `tom_atmosfera` co-ocorrendo, por exemplo) sobrevive à permutação;
- o número de eixos por review, e portanto a distribuição de carga do filme;
- a **frequência global de cada eixo no filme**;
- o **tamanho de cada bucket** (`n` por bucket), inclusive quando os três
  diferem entre si.

**Destruído (é a hipótese nula):** a associação entre o eixo e o grupo. Sob o
nulo, qualquer lift observado vem só de como a permutação caiu.

Este é o mesmo embaralhamento que a SPEC §2.5 já declara ("embaralhando o
rótulo de bucket DENTRO de cada filme — preserva a frequência global de cada
eixo e destrói só a associação com o grupo"); a diferença desta sessão está na
**estatística lida** (o máximo por filme), não no embaralhamento.

**A alternativa que NÃO uso, e por quê.** Embaralhar eixo a eixo de forma
independente (permutar a coluna de cada eixo separadamente) daria um nulo com
eixos independentes entre si — e a co-ocorrência é real e forte no corpus
(3,01 eixos por review). Um nulo assim tem menos variância no máximo do que a
realidade, e **superestimaria** a significância de 20pp. O nulo escolhido é o
conservador dos dois.

## 4. Parâmetros

- **B = 10.000 permutações por filme.** As medições anteriores usaram 2.000;
  aqui a leitura é de **cauda** (percentil de 20pp, e p-valores perto de 0,05),
  onde 2.000 dá resolução de 0,05% e ruído de Monte Carlo visível. 10.000 custa
  segundos e zero LLM.
- **Semente 24**, a mesma dos estudos anteriores, por continuidade.
- p-valor por filme: `p = (1 + |T_perm >= T_obs|) / (B + 1)` (estimador com
  correção de continuidade, que nunca devolve p = 0).

## 5. As quatro leituras (Entrega 2)

1. **Percentil de 20pp no nulo, por filme e agregado.** Qual fração das
   permutações produz `T >= 20pp` — isto é, com que probabilidade um filme
   **sem contraste nenhum** sai publicado como `tematico`. É a taxa de falso
   contraste por filme, por definição.
2. **Em quantos filmes 20pp fica abaixo da mediana do nulo** — o limiar seria
   cruzado por acaso na maioria das permutações.
3. **Taxa de falso contraste do catálogo.** Dos 35, em quantos o `T` observado
   é distinguível do nulo a α = 0,10 / 0,05 / 0,01, e o mesmo com correção de
   comparações múltiplas entre os 35 filmes (Holm–Bonferroni e
   Benjamini–Hochberg — os 35 testes são o segundo nível de multiplicidade,
   acima das 30 células).
4. **Dependência de `n` e da carga de eixos.** (a) Sub-amostro cada bucket para
   n ∈ {10, 20, 30, 40} e refaço o nulo — mede como a distribuição do máximo se
   move com n. n = 50 e 100 **não** são simuláveis por subamostragem (o pool
   rotulado é ~40/bucket); para eles uso a lei analítica ajustada nos pontos
   medidos, declarada como extrapolação, exatamente como
   `MEDICAO_VERIFICACAO_BINARIA.md` §2.2 declarou a dela. (b) Correlaciono a
   mediana do nulo de cada filme com a média de eixos por review do filme e com
   o `n` médio por bucket.

## 6. Entrega 3 — a varredura de limiar

Para cada limiar de **12,5pp a 40pp em passo de 2,5pp** (o passo não é
arbitrário: com n = 40 o quantum do lift é exatamente 2,5pp — um passo menor
produz limiares que não são distinguíveis do vizinho por nenhuma amostra
possível), reporto sobre o mesmo nulo:

- taxa de falso contraste esperada (média sobre os 35 filmes de
  `P(T_nulo >= limiar)`);
- quantos dos 35 filmes ficariam `tematico` no observado.

Curvas por n ∈ {10, 20, 30, 40} medidas; n ∈ {50, 100} por extrapolação
declarada.

## 7. Previsões registradas antes de rodar

Escritas para poderem falhar:

1. A mediana do nulo do máximo ficará **entre 10pp e 20pp** para a maioria dos
   filmes com n≈40. (Razão: 30 células, quantum 2,5pp, e o desvio-padrão do
   lift de uma célula sob o nulo é da ordem de 10pp para uma frequência média
   de ~30%.)
2. **Menos de 10 dos 35** filmes terão `T` observado significativo a α = 0,05
   sem correção nenhuma.
3. O limiar necessário para taxa de falso contraste de 5% em n = 40 ficará
   **acima de 30pp**, e deixaria **menos de 8** dos 35 filmes `tematico`.
4. A mediana do nulo **cresce** quando n cai (é o mecanismo que
   `MEDICAO_VERIFICACAO_BINARIA.md` Entrega 2 observou por outro caminho:
   P(manter contraste) = 0,993 em n=10).

## 8. O que este desenho NÃO responde

- **Se a classificação por eixo está certa.** O nulo permuta rótulos de bucket;
  o conjunto de eixos de cada review é tomado como dado. Erro de classificação
  não aparece aqui (tem medição própria: `ESTABILIDADE_AGREGADA.md`, 26,5% de
  reprodutibilidade individual antes da votação de 3).
- **Se um contraste significativo é INTERESSANTE.** Significância não é
  tamanho de efeito nem relevância editorial.
- **Se o contraste existe na população de quem viu o filme.** A população aqui
  é a amostra de produção, com os filtros de produção (`texto_completo`, sem
  spoiler, ≥150 caracteres). Reviews curtas ficam fora, como sempre.
- **Nada sobre os filmes fora dos 35.**

---

## Nota acrescentada DEPOIS de rodar (não altere o registrado acima)

**O §6 acima está errado num ponto, e a correção está em
`ESTUDO_MARGEM_20PP.md` §3.1.** O passo de 2,5pp foi justificado pelo quantum
do lift em n = 40 — mas a varredura da Entrega 3 percorre **vários** n, e o
quantum é `100/n`: 5pp em n=20, 10pp em n=10. Uma grade fixa de 2,5pp produz
limiares **inatingíveis** em n pequeno, e a tabela de "limiar necessário" saía
com valores que nenhuma amostra pode realizar (32,5pp com n=20 não existe).

A tabela publicada em §3.2 do relatório usa **a grade própria de cada n**. A
tabela de §2.5 do relatório manteve a grade de 2,5pp e traz a ressalva ao lado,
porque ali ela é lida como curva e as repetições são informativas.

**As previsões de §7 não foram tocadas.** A previsão 3 falhou e está reportada
como falha em `ESTUDO_MARGEM_20PP.md` §2.7.

**Segundo desvio do registrado, e ele foi para melhor — declarado aqui porque
é desvio.** O §5, item 4a acima diz que n = 50 e 100 seriam obtidos por "lei
analítica ajustada nos pontos medidos". Não foi o que rodou. **Sob o nulo, o
rótulo de bucket não carrega informação**, então sortear 3n reviews do pool do
filme e fatiá-las em três buckets de tamanho n é um procedimento único que vale
para todo n: é a permutação exata quando 3n = N, subamostragem quando 3n < N, e
reamostragem com reposição quando 3n > N. Isso dá n = 50 e 100 por simulação em
vez de por ajuste, com a **mesma** premissa de extrapolação que a lei teria
(distribuição empírica congelada, só a variância amostral se move) e sem a
premissa extra de que a forma da lei está certa.

**Não é uma licença para ler n = 50 e 100 como medição de dado novo.** A
ressalva de `MEDICAO_VERIFICACAO_BINARIA.md` §2.2 continua valendo palavra por
palavra: eles dizem quanto a variância amostral encolheria, não se a frequência
observada se moveria. O ajuste 1/√n foi rodado assim mesmo, como conferência —
ele bate com o simulado dentro de 2,8pp (`ESTUDO_MARGEM_20PP.md` §2.5).
