# Validação das checagens novas do editor [E2] — v1.8.0, Tarefa 5

**Data:** 2026-08-04. **Objetivo:** validar, em condição real (`--provider
deepseek --com-editor`), as duas checagens novas da Tarefa 3 (conteúdo
adicionado + ordem dos movimentos) que motivaram desligar o editor por
padrão (`EDITOR_ATIVO=False`, ver `config.py`).

**Saídas:** `resultado/validacao_editor_v18/{cure,cidade-de-deus,the-invite-2026}.json`
— diretório isolado; `resultado/*.json` de produção **não foram tocados**
(hashes MD5 conferidos antes/depois, inalterados).

**Orçamento:** até 16 chamadas DeepSeek. Gastas: **8** — cure (1 narrador + 2
editor), cidade-de-deus (1 narrador + 2 editor), the-invite-2026 (1 narrador +
1 editor). Nenhum filme falhou.

**Nenhum veredito de qualidade literária** — textos e números lado a lado.

---

## Resposta direta à pergunta do orçamento: o parágrafo inventado reaparece?

**Não, não reapareceu nesta rodada** do `the-invite-2026` — o narrador e o
editor geraram uma narrativa NOVA e diferente da vista na validação anterior
(VALIDACAO_DEEPSEEK.md), sem o parágrafo de opinião inventado nem a
reordenação do movimento 1. Isso é esperado: o defeito é uma questão de
VARIÂNCIA do modelo entre chamadas (o mesmo texto bruto pode gerar edições
diferentes em execuções diferentes), não um bug determinístico que se repete
sempre.

**Mas a checagem funciona — com duas evidências independentes:**
1. **Reprodução determinística (Tarefa 4, `tests/test_editor.py`):**
   alimentando `editar_narrativa` repetidamente com o texto LITERAL do
   defeito real (o parágrafo inventado + a reordenação, copiados do
   relatório anterior), a checagem nova detecta, retenta com o reforço
   específico, e — como o texto injetado no teste nunca muda — esgota as
   tentativas e DESCARTA, publicando a bruta. Testes automatizados, sempre
   verdes, cobrindo exatamente este defeito.
2. **Disparo real em produção nesta própria validação:** `cidade-de-deus`
   teve sua 1ª tentativa de edição REPROVADA pela checagem nova
   (`motivos_por_tentativa: ["conteudo_adicionado"]`) — não é o mesmo
   defeito do `the-invite-2026`, mas confirma que a checagem dispara sobre
   dados reais, não só sobre o texto sintético do teste. A 2ª tentativa
   corrigiu sozinha e foi aceita (similaridade 0,963, abaixo do limiar de
   edição nula).

---

## Tabela de decisão

| Filme | Similaridade final | `frases_sem_origem` (final) | Conteúdo adicionado? | Ordem alterada? | `n_tentativas` | Aceito/Descartado |
|---|---|---|---|---|---|---|
| **cure** | 0,747 | 2 frases (abaixo do limiar de 4) | Não (passou) | Não | 2 (1ª falhou por número alterado, não por conteúdo) | ✅ Aceito |
| **cidade-de-deus** | 0,963 | 3 frases (abaixo do limiar de 4) na tentativa aceita | **Sim, na 1ª tentativa** (retentada e corrigida) | Não | 2 (1ª falhou com `motivo="conteudo_adicionado"`) | ✅ Aceito |
| **the-invite-2026** | 0,875 | 1 frase (abaixo do limiar de 4) | Não | Não | 1 (aceito de primeira) | ✅ Aceito |

Nenhum dos 3 filmes foi descartado nesta rodada — mas `cidade-de-deus`
mostra a checagem REPROVANDO uma tentativa real antes de aceitar a segunda,
o que não acontecia antes da Tarefa 3 (motivos disponíveis até a v1.7.4 eram
só protegido/número/honestidade/formato/edição-nula — nenhum deles teria
pego o que a 1ª tentativa do `cidade-de-deus` fez).

---

## `cure`

- **Bruta → editada:** o editor quebrou 2 frases longas em pares mais curtos
  (ritmo) e ajustou conectivos ("Só que", "porque" no lugar de "deixando").
  Nenhum conteúdo novo, nenhuma reordenação.
- **Bruta:**
  > Em A Cura (1997), de Kiyoshi Kurosawa, um detetive investiga uma série de assassinatos marcados por um x nos corpos, levando a interrogatórios intermináveis que só avançam quando um rapaz de trejeitos estranhos é preso. Um thriller de crime e mistério que mergulha em um terror psicológico atmosférico. O filme é marcado por um ritmo lento e deliberado, que constrói uma atmosfera de desconforto, envolto em ambiguidade e com uma forte sensação de apreensão sustentada até o fim. A grande maioria das notas (~79%) é positiva, e essas reviews celebram a atmosfera perturbadora e hipnótica, o pacing lento e a exploração de temas psicológicos e existenciais. Para a grande maioria das notas (~79%), a ausência de respostas é um ponto forte, deixando o espectador em reflexão. Uma minoria das notas (~17%) fica no meio: para eles, o ritmo lento gera confusão narrativa, o final é insatisfatório ou ambíguo, e embora reconheçam ideias intrigantes e a atmosfera eficaz, sentem que a execução falha e que uma revisitação é necessária para a compreensão plena. Já entre as notas, uma fração mínima (~3%) representa quem não gostou: para esse grupo, o filme é lento e tedioso, carece de tensão e mistério, e o enredo é repetitivo e fraco, com personagens planos e um final insatisfatório.
- **Editada:**
  > Em A Cura (1997), de Kiyoshi Kurosawa, um detetive investiga uma série de assassinatos marcados por um x nos corpos. Só que os interrogatórios são intermináveis e só avançam quando um rapaz de trejeitos estranhos é preso. Thriller de crime e mistério, o filme mergulha em um terror psicológico atmosférico. O ritmo é lento e deliberado, e essa escolha constrói uma atmosfera de desconforto, envolta em ambiguidade, com uma forte sensação de apreensão sustentada até o fim.
  >
  > a grande maioria das notas (~79%) é positiva, e essas reviews celebram a atmosfera perturbadora e hipnótica, o pacing lento e a exploração de temas psicológicos e existenciais. Para esse mesmo grupo (~79%), a ausência de respostas é um ponto forte, porque deixa o espectador em reflexão.
  >
  > Uma minoria das notas (~17%) fica no meio: para eles, o ritmo lento gera confusão narrativa, o final é insatisfatório ou ambíguo, e embora reconheçam ideias intrigantes e a atmosfera eficaz, sentem que a execução falha. Para esse grupo, uma revisitação é necessária para a compreensão plena.
  >
  > Já entre as notas, uma fração mínima (~3%) representa quem não gostou. Para esse grupo, o filme é lento e tedioso, carece de tensão e mistério, e o enredo é repetitivo e fraco, com personagens planos e um final insatisfatório.
- **`frases_sem_origem` (tentativa aceita):** `["Só que os interrogatórios são intermináveis e só avançam quando um rapaz de trejeitos estranhos é preso.", "Para esse grupo, uma revisitação é necessária para a compreensão plena."]` — ambas são o MESMO conteúdo do bruto, só quebrado em frase separada (similaridade 0,39 e 0,32 contra a frase-fonte inteira — baixa por causa do comprimento diferente, não por invenção). 2 frases < `EDITOR_MIN_FRASES_SEM_ORIGEM` (4): não reprova.
- **`motivos_por_tentativa`:** `["conjunto de números do texto foi alterado"]` na 1ª tentativa (não relacionado às checagens novas); 2ª tentativa aceita.
- **Tempo total (CLI, narrador+editor):** 21,7s.

---

## `cidade-de-deus`

- **Bruta → editada:** o editor quebrou o parágrafo positivo (91%) em
  sentenças menores. A 1ª tentativa foi REPROVADA pela checagem de conteúdo
  adicionado — não temos o texto exato dela (só a tentativa aceita é
  persistida), mas o motivo confirma que o modelo produziu algo abaixo do
  limiar antes de se corrigir sozinho na 2ª chamada.
- **Bruta:**
  > Cidade de Deus, dirigido por Fernando Meirelles, é um drama policial de 2002 que acompanha Buscapé, um jovem que cresce na Cidade de Deus e vê na fotografia uma saída da violência. A experiência de assistir ao filme é marcada por um ritmo acelerado e uma montagem frenética, além de uma violência que é ao mesmo tempo brutal e estilizada, apresentada de forma crua e impactante. A grande maioria das notas (~91%) celebra a obra como um marco do cinema, destacando a edição dinâmica que confere energia contagiante e a narrativa envolvente, que costura múltiplas histórias sem perder coesão, além de ressaltar o realismo da violência, que choca pela seriedade do tema. Para esse vasto grupo, a brutalidade é apresentada de forma realista, sem glamour, e as atuações são marcantes, transmitindo autenticidade. Uma pequena minoria das notas (~8%) reconhece a qualidade técnica e o retrato realista da violência, mas, para esse grupo, falta uma conexão emocional mais profunda, e o ritmo inconstante pode tornar certas partes monótonas. Finalmente, uma fração mínima das notas (~1%) critica o filme por estetizar a violência e a miséria, transformando-as em espetáculo, e por apresentar uma representação estereotipada da favela, com violência excessiva e personagens pouco desenvolvidos, o que, para eles, compromete a autenticidade da obra.
- **Editada (2ª tentativa, aceita):**
  > Cidade de Deus, dirigido por Fernando Meirelles, é um drama policial de 2002 que acompanha Buscapé, um jovem que cresce na Cidade de Deus e vê na fotografia uma saída da violência. A experiência de assistir ao filme é marcada por um ritmo acelerado e uma montagem frenética, além de uma violência que é ao mesmo tempo brutal e estilizada, apresentada de forma crua e impactante.
  >
  > A grande maioria das notas (~91%) celebra a obra como um marco do cinema. O elogio se concentra na edição dinâmica, que confere energia contagiante, e na narrativa envolvente, que costura múltiplas histórias sem perder coesão. Também ressaltam o realismo da violência, que choca pela seriedade do tema. Para esse vasto grupo, a brutalidade é apresentada de forma realista, sem glamour, e as atuações são marcantes, transmitindo autenticidade.
  >
  > Uma pequena minoria das notas (~8%) reconhece a qualidade técnica e o retrato realista da violência, mas, para esse grupo, falta uma conexão emocional mais profunda. O ritmo inconstante pode tornar certas partes monótonas. Já uma fração mínima das notas (~1%) critica o filme por estetizar a violência e a miséria, transformando-as em espetáculo, e por apresentar uma representação estereotipada da favela, com violência excessiva e personagens pouco desenvolvidos, o que, para eles, compromete a autenticidade da obra.
- **`frases_sem_origem` (tentativa aceita, telemetria PERSISTIDA mesmo aceita):** 3 frases —
  `"A grande maioria das notas (~91%) celebra a obra como um marco do cinema."` (0,40),
  `"Também ressaltam o realismo da violência, que choca pela seriedade do tema."` (0,35),
  `"O ritmo inconstante pode tornar certas partes monótonas."` (0,39) —
  todas são o MESMO conteúdo do bruto quebrado em frases menores (mesmo
  padrão do `cure`); 3 < 4 não reprova esta tentativa.
- **`motivos_por_tentativa`:** `["conteudo_adicionado"]` — a 1ª tentativa
  REALMENTE disparou a checagem nova (a única ocorrência real, não sintética,
  desta validação).
- **Tempo total:** 21,4s.

---

## `the-invite-2026`

- **Bruta → editada:** reescrita leve, uma frase quebrada em duas, sem
  reordenação e sem parágrafo novo. **O defeito da validação anterior não se
  repetiu nesta chamada** (ver seção acima).
- **Bruta:**
  > Em O Convite, de Olivia Wilde (2026), um drama com comédia, o casamento de Joe e Angela está em crise, e a noite em que convidam seus enigmáticos vizinhos para um jantar toma rumos inesperados. O filme tem ritmo que desacelera conforme avança, com uma atmosfera íntima que transita entre tons cômicos e dramáticos, abordando com franqueza temas de sexualidade e relacionamentos, ainda que a previsibilidade e a repetição marquem parte da experiência. A grande maioria das notas (~79%) celebra justamente esse equilíbrio: quase todos destacam a direção e o roteiro, cerca de metade valoriza o humor que convive com o drama, e a maioria elogia as atuações e a química do elenco, vendo originalidade no tratamento das crises conjugais. Uma minoria das notas (~18%) reconhece a competência técnica, mas, para esse grupo, o filme se torna repetitivo e a mudança de tom final soa abrupta. Já uma fração mínima das notas (~3%) é mais dura: para quem está nessa faixa, cerca de metade vê humor e roteiro fracos ou entediantes, muitos consideram personagens e diálogos superficiais, e a abordagem da sexualidade é percebida como forçada — uma experiência decepcionante para essa parcela.
- **Editada:**
  > Em O Convite, de Olivia Wilde (2026), um drama com comédia, o casamento de Joe e Angela está em crise, e a noite em que convidam seus enigmáticos vizinhos para um jantar toma rumos inesperados. Conforme avança, o ritmo desacelera. A atmosfera íntima transita entre tons cômicos e dramáticos, e o filme aborda com franqueza temas de sexualidade e relacionamentos, mas a previsibilidade e a repetição marcam parte da experiência. A grande maioria das notas (~79%) celebra justamente esse equilíbrio: quase todos destacam a direção e o roteiro, cerca de metade valoriza o humor que convive com o drama, e a maioria elogia as atuações e a química do elenco, vendo originalidade no tratamento das crises conjugais. Já uma minoria das notas (~18%) reconhece a competência técnica, mas, para esse grupo, o filme se torna repetitivo e a mudança de tom final soa abrupta. E há ainda uma fração mínima das notas (~3%) que é mais dura: para quem está nessa faixa, cerca de metade vê humor e roteiro fracos ou entediantes, muitos consideram personagens e diálogos superficiais, e a abordagem da sexualidade é percebida como forçada — uma experiência decepcionante para essa parcela.
- **`frases_sem_origem`:** `["Conforme avança, o ritmo desacelera."]` — 1
  frase, fragmento de uma frase mais longa do bruto ("O filme tem ritmo que
  desacelera conforme avança..."), similaridade 0,22 contra a frase inteira
  (baixa por comprimento, mesmo padrão dos outros dois filmes). 1 < 4: não
  reprova.
- **`motivos_por_tentativa`:** `[]` — aceito de primeira.
- **Tempo total:** 9,4s (mais rápido — narrador e editor convergiram sem
  retentativa).

---

## Achado sobre a calibração dos limiares

Nos 3 filmes reais desta validação, TODA frase marcada como "sem origem"
tinha similaridade entre 0,22 e 0,40 contra a frase INTEIRA do bruto da qual
derivava — sempre por um motivo estrutural (o editor quebrou uma frase longa
do bruto em duas menores, e cada metade, sozinha, tem baixa similaridade
`SequenceMatcher.ratio` contra a frase original inteira, só por causa da
diferença de comprimento — não porque o conteúdo é novo). Isso confirma, com
dados reais adicionais aos 3 filmes de VALIDACAO_DEEPSEEK.md, que o padrão
"1-3 frases, similaridade 0,2-0,6" é o ruído NORMAL de uma boa edição de
ritmo, e `EDITOR_MIN_FRASES_SEM_ORIGEM=4` mantém distância segura dele. O
caso real do `the-invite-2026` (defeito original) tinha 15 frases flagradas
— quase 4x o limiar — nenhum dos 3 filmes desta rodada chegou perto.

## Conclusão factual

- Nenhum filme foi descartado; todos publicaram uma edição com ganho de
  ritmo sobre a bruta, preservando conteúdo.
- A checagem de conteúdo adicionado disparou UMA VEZ de verdade
  (`cidade-de-deus`, 1ª tentativa) e se autocorrigiu na retentativa —
  exatamente o comportamento pretendido (reforço específico, nova chance,
  fail-safe de descarte só se persistir).
- O defeito original do `the-invite-2026` não reapareceu nesta rodada
  (variância do modelo), mas está coberto por teste de regressão
  determinístico (`tests/test_editor.py`) que injeta o texto literal do
  defeito e confirma DESCARTE.
- `EDITOR_ATIVO` permanece `False` por padrão — esta validação é evidência
  a favor de reativar, mas a decisão de mudar esse default fica para leitura
  humana deste relatório, não foi aplicada aqui.
