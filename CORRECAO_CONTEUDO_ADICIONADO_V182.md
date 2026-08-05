# v1.8.2 — Correção do falso positivo de `conteudo_adicionado` + regeneração

**Data:** 2026-08-04.

**Diagnóstico** (confirmado pela calibração desta versão): a métrica da
v1.8.0 comparava cada frase do editado contra cada frase do bruto INTEIRA,
usando `difflib.SequenceMatcher.ratio()` (char-level, sensível a ORDEM).
Quando o editor quebrava uma frase longa em duas menores — exatamente o
trabalho de ritmo que ele existe para fazer — cada metade tinha similaridade
baixa contra a frase-fonte inteira só por diferença de COMPRIMENTO, não por
conteúdo novo; e quando reordenava palavras dentro da frase, a mesma métrica
também caía, mesmo com o conteúdo idêntico. Foi isso que descartou o `cure`
na v1.8.1 após 3 reprovações seguidas por `conteudo_adicionado`.

---

## Tarefa 1 — nova métrica

Trocada por **cobertura de palavras** (multiset, insensível a ORDEM):
tokeniza a frase e a frase-de-referência em palavras, ordena os tokens
(remove a informação de posição) e roda
`difflib.SequenceMatcher.get_matching_blocks()` sobre as duas listas
ordenadas — matematicamente equivalente à interseção de multiset, mas ainda
usando `SequenceMatcher` como base. Comparada contra a **melhor frase
INDIVIDUAL do bruto** (não o texto inteiro de uma vez): medido ao vivo que
comparar contra o bruto inteiro infla o placar de frases genuinamente
inventadas, que pegam carona em vocabulário genérico de crítica de cinema
espalhado por frases distantes do bruto.

`EDITOR_LIMIAR_FRASE_SEM_ORIGEM` subiu de 0,45 para **0,6**.
`EDITOR_MIN_FRASES_SEM_ORIGEM` (4) e
`EDITOR_LIMIAR_PALAVRAS_SEM_ORIGEM_FRACAO` (0,35) mantidos como estavam —
a correção é só da métrica por frase, não da política de agregação.

---

## Tarefa 2 — calibração (offline, zero LLM)

Três testes novos em `tests/test_editor.py`, rodando a métrica nova sobre
os casos reais já em disco:

| Caso | Cobertura (nova métrica) |
|---|---|
| v18/cure — "Só que os interrogatórios são intermináveis..." | 0,765 |
| v18/cure — "Para esse grupo, uma revisitação é necessária..." | 0,818 |
| v18/cidade-de-deus — "A grande maioria das notas (~91%) celebra..." | 1,000 |
| v18/cidade-de-deus — "Também ressaltam o realismo da violência..." | 0,833 |
| v18/cidade-de-deus — "O ritmo inconstante pode tornar..." | 1,000 |
| v18/the-invite-2026 — "Conforme avança, o ritmo desacelera." (reordenação) | 1,000 |
| produção v1.8.1/cure — 3 frases que descartaram o filme | 1,000 / 1,000 / 1,000 |
| produção v1.8.1/cidade-de-deus — "O filme é intenso e frenético." | 1,000 |
| produção v1.8.1/the-invite-2026 — 2 de 3 frases | 1,000 / 0,889 |
| **parágrafo REALMENTE inventado** (`the-invite-2026`, texto literal) — 6 frases | **0,222 a 0,500** |

**Resultado da calibração: todas as 11 frases legítimas testadas ficaram
ACIMA do limiar (0,6); todas as 6 frases do parágrafo realmente inventado
ficaram ABAIXO.** Folga de 0,265 entre o pior caso legítimo (0,765) e o pior
caso inventado (0,500).

**Uma ressalva documentada, não bloqueante:** a 3ª frase de
produção-v1.8.1/the-invite-2026, *"O resultado é uma recepção polarizada."*,
não é uma quebra de frase — é um REENQUADRAMENTO com vocabulário diferente
do bruto ("recepção polarizada" no lugar de "o filme parece dividir
opiniões"). Ela mede exatamente 0,500, empatada até a 3ª casa decimal com a
frase mais próxima do limiar entre as REALMENTE inventadas. Nenhum limiar
escalar separa as duas — isso é esperado (reenquadramento com sinônimos e
conteúdo inventado são mais parecidos entre si do que uma quebra de frase é
de qualquer um dos dois). Não é uma regressão: essa frase, sozinha, não
reprova nenhuma edição (`EDITOR_MIN_FRASES_SEM_ORIGEM=4`). Documentada em
teste próprio (`test_calibracao_reenquadramento_documenta_o_empate_sem_falhar`),
não escondida.

**A calibração passou** (com a ressalva acima, fora do escopo estrito da
Tarefa 2 — que pedia especificamente as quebras de frase). Suíte: **392
passed** (389 + 3 testes de calibração novos).

---

## Tarefa 3 — regeneração de produção

13 chamadas DeepSeek no total (orçamento de 16): `cure` (1 narrador + 4
editor), `cidade-de-deus` (1 narrador + 1 editor), `the-invite-2026` (2
narrador + 2 editor). Zero chamadas Letterboxd/TMDB (`--offline`, cache
intocado). `frontend/build_data.py` rodado.

---

## Tarefa 4 — verificação

### Resultado central: **zero disparos de `conteudo_adicionado` nesta regeneração** (contra 6 na v1.8.1)

| Filme | Resultado | n_tentativas | motivos_por_tentativa | similaridade |
|---|---|---|---|---|
| `cure` | **Descartada** (mesmo assim) — bruta publicada | 4 | `ordem_alterada`, `perspectiva_nao_marcada`, `perspectiva_nao_marcada`, `edicao_nula` | 0,972 |
| `cidade-de-deus` | Aceita **de primeira** | 1 | (nenhum) | 0,931 |
| `the-invite-2026` | Aceita (2ª tentativa) | 2 | `ordem_alterada` | 0,926 |

**Comparação direta com a v1.8.1** (mesmo diagnóstico, motivos diferentes):

| | v1.8.1 (métrica antiga) | v1.8.2 (métrica nova) |
|---|---|---|
| Disparos de `conteudo_adicionado` | 6 (3 no `cure`, 1 no `cidade-de-deus`, 2 no `the-invite-2026`) | **0** |
| `cure` | Descartada (3× `conteudo_adicionado` + 1× `perspectiva_nao_marcada`) | Descartada (`ordem_alterada`, 2×`perspectiva_nao_marcada`, `edicao_nula`) |
| `cidade-de-deus` | Aceita na 2ª tentativa | **Aceita de primeira** |
| `the-invite-2026` | Aceita na 4ª tentativa | Aceita na 2ª tentativa |

**A correção funcionou exatamente como diagnosticado: nenhuma tentativa foi
reprovada por `conteudo_adicionado` desta vez.** As tentativas caíram em
`cidade-de-deus` (2→1) e `the-invite-2026` (4→2). O `cure` continua sendo
descartado — mas agora por motivos genuinamente diferentes (`ordem_alterada`
e `perspectiva_nao_marcada`, checagens que esta sessão NÃO alterou), o que é
esperado: o descarte é fail-safe por natureza, e a variância do modelo entre
chamadas pode acionar qualquer checagem, não só a que foi corrigida.

**Achado à parte, fora do escopo desta correção:** a tentativa 1 do `cure`
foi reprovada por `ordem_alterada` com um texto que, por leitura humana
(ver `tentativas_detalhe` abaixo), parece preservar a ordem dos movimentos
normalmente — candidato a um falso positivo semelhante na checagem de ORDEM
(que usa a métrica antiga, sensível a ordem, não tocada nesta sessão).
Registrado como observação, não investigado nem corrigido aqui.

```
--- tentativa 1 | motivo: ordem_alterada | similaridade: 0.769 ---
A Cura (1997), do diretor Kiyoshi Kurosawa, acompanha um detetive que
investiga mortes marcadas por um x estranho. O caso o leva até um suspeito
tímido e enigmático, num thriller de crime e mistério que mergulha no
horror psicológico. [...]
```

### Flags de honestidade (narrador) — nos 3 filmes

Todas `false`, exceto: `cure` e `cidade-de-deus` com `aspas_removidas=true`
(mecânico); `the-invite-2026` com `perspectiva_nao_marcada=true` (mesmo após
retentativa do narrador — variância do modelo, checagem não relacionada a
esta correção).

### Defeitos conhecidos — checados explicitamente nos 3 textos publicados

- **Parágrafo de opinião inventado:** ausente nos 3.
- **Movimento 1 fora de ordem:** ausente nos 3 — todos abrem com a
  apresentação do filme.
- **Contrabarra residual:** ausente nos 3.
- **Rótulo de peso com maiúscula no meio de frase:** ausente nos 3 (a única
  ocorrência de "A grande maioria" fora do início do texto, em
  `the-invite-2026`, está no início de um PARÁGRAFO NOVO — capitalização
  correta, não um defeito).

---

## Narrativas finais (bruta e editada) dos 3 filmes

### `cure` — DESCARTADA (bruta = publicada, igual às duas)

> Em A Cura (1997), do diretor Kiyoshi Kurosawa, um detetive investiga mortes marcadas por um x estranho, levando-o a um suspeito tímido e enigmático — um thriller de crime e mistério que mergulha no horror psicológico. A experiência é marcada por um ritmo lento que domina a narrativa, com uma atmosfera sombria e perturbadora, mas que se desdobra de forma ambígua e sem respostas definitivas. A grande maioria das notas (~79%) é positiva, e essas reviews celebram o trabalho como hipnótico e perturbador: para esse grupo, o ritmo lento e deliberado intensifica o suspense, e a ausência de respostas é vista como um trunfo, forçando a reflexão sobre temas psicológicos profundos. Uma minoria das notas (~17%) fica no meio-termo — nessa leitura, o mesmo ritmo lento gera confusão narrativa, e o final ambíguo deixa pontas soltas, embora reconheçam ideias intrigantes e uma atmosfera eficaz. Para a fração mínima das notas (~3%), que não gostou, o filme é tedioso e arrastado, sem tensão, com personagens planos e um enredo repetitivo — uma experiência que, para eles, não cumpre o potencial da premissa.

### `cidade-de-deus`

**Bruta:**
> Em Cidade de Deus (2002), o diretor Fernando Meirelles conduz um drama criminal que acompanha Buscapé, um jovem da Cidade de Deus que, temendo tornar-se um bandido, vê na fotografia uma chance de vida digna. O filme, com 130 minutos de duração, apresenta uma narrativa fragmentada que alterna linhas do tempo e múltiplos personagens, ambientada em uma favela carioca marcada pela violência e pela pobreza. A edição é ágil e a câmera, dinâmica, criando um ritmo acelerado e uma atmosfera intensa, enquanto a violência é retratada de forma crua e realista, sem suavização. As notas são dominadas pela aprovação: a grande maioria das notas (~91%) é positiva. Quem gostou celebra o estilo visual e a edição dinâmicos, apontados pela maioria das reviews positivas como fonte de energia e imersão, além da narrativa envolvente e da brutalidade realista da violência, que muitos destacam como impactante e não glamourizada. Uma pequena minoria das notas (~8%) fica no meio-termo: para esse grupo, o filme é tecnicamente impressionante e retrata a violência e a realidade social de forma realista — cerca de metade das reviews medianas menciona esse retrato —, mas muitos sentem que falta conexão emocional, o que impede uma nota mais alta. Por fim, uma fração mínima das notas (~1%) rejeita o filme: nessa leitura, muitos veem a estetização e a espetacularização da violência e da miséria como um problema ético, muitos apontam representação estereotipada da favela e muitos consideram a violência excessiva e gratuita, o que compromete a experiência.

**Editada (publicada):**
> Em Cidade de Deus (2002), o diretor Fernando Meirelles conduz um drama criminal que acompanha Buscapé, um jovem da Cidade de Deus que, temendo tornar-se um bandido, vê na fotografia uma chance de vida digna. O filme tem 130 minutos de duração e apresenta uma narrativa fragmentada, que alterna linhas do tempo e múltiplos personagens, numa favela carioca marcada pela violência e pela pobreza. A edição é ágil e a câmera é dinâmica, criando um ritmo acelerado e uma atmosfera intensa, enquanto a violência surge crua e realista, sem suavização. As notas são dominadas pela aprovação: a grande maioria das notas (~91%) é positiva. Quem gostou celebra o estilo visual e a edição dinâmicos, que a maioria das reviews positivas aponta como fonte de energia e imersão. Também entram na conta a narrativa envolvente e a brutalidade realista, que muitos destacam como impactante e não glamourizada. Uma pequena minoria das notas (~8%) fica no meio-termo. Para esse grupo, o filme é tecnicamente impressionante e retrata a violência e a realidade social de forma realista — cerca de metade das reviews medianas menciona esse retrato —, mas muitos sentem falta de conexão emocional, o que impede uma nota mais alta. Por fim, uma fração mínima das notas (~1%) rejeita o filme. Nessa leitura, muitos veem a estetização e a espetacularização da violência e da miséria como um problema ético. Muitos também apontam representação estereotipada da favela, e muitos consideram a violência excessiva e gratuita, o que compromete a experiência.

### `the-invite-2026`

**Bruta:**
> O Convite (2026), dirigido por Olivia Wilde, é um drama com toques de comédia que acompanha um casal à beira do divórcio quando um jantar com vizinhos enigmáticos toma rumos inesperados. Ambientado quase inteiramente em um apartamento, o filme sustenta um tom de comédia que transita para o drama, com ritmo que alguns acham arrastado e outros enxuto. A grande maioria das notas (~79%) é positiva, e quem gostou destaca a direção e o roteiro como pontos fortes, quase todos elogiando o equilíbrio entre humor e drama, além da maioria exaltar as atuações e a química do elenco, com cerca de metade apontando a originalidade da narrativa. Para a minoria que ficou no meio (~18%), o filme é bem atuado e dirigido, mas muitos sentem que a repetição e a duração tornam a experiência cansativa, e a mudança de tom no final divide opiniões. Já para a fração mínima das notas (~3%), a experiência é decepcionante: cerca de metade das reviews aponta humor e roteiro fracos, muitos criticam personagens superficiais e atuações questionáveis, e a abordagem da sexualidade é vista como forçada.

**Editada (publicada):**
> O Convite (2026), dirigido por Olivia Wilde, é um drama com toques de comédia que acompanha um casal à beira do divórcio quando um jantar com vizinhos enigmáticos toma rumos inesperados. Ambientado quase inteiramente em um apartamento, o filme sustenta um tom de comédia que transita para o drama, com ritmo que alguns acham arrastado e outros enxuto.
>
> A grande maioria das notas (~79%) é positiva, e quem gostou destaca a direção e o roteiro como pontos fortes. Quase todos elogiam o equilíbrio entre humor e drama, e a maioria também exalta as atuações e a química do elenco. Cerca de metade ainda aponta a originalidade da narrativa.
>
> Para a minoria que ficou no meio (~18%), o filme é bem atuado e dirigido. Só que muitos sentem que a repetição e a duração tornam a experiência cansativa, e a mudança de tom no final divide opiniões.
>
> Já a fração mínima das notas (~3%) acha a experiência decepcionante. Cerca de metade das reviews aponta humor e roteiro fracos, muitos criticam personagens superficiais e atuações questionáveis, e a abordagem da sexualidade é vista como forçada.

---

## Conclusão factual

O buraco relatado — falso positivo de `conteudo_adicionado` reprovando
edição legítima — **foi corrigido**: zero disparos nesta regeneração,
contra 6 na v1.8.1. `cidade-de-deus` passou a ser aceito de primeira
(era 2 tentativas); `the-invite-2026` caiu de 4 para 2 tentativas. O `cure`
continua sendo descartado, mas por motivos não relacionados a esta
correção — um achado à parte (possível falso positivo em `ordem_alterada`)
foi registrado, não investigado. Nenhum defeito conhecido das versões
anteriores reapareceu nos textos publicados.
