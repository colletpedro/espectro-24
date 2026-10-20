# Sensibilidade da validação — juiz v2.2 (congelado)

> **ISTO NÃO MUDA O VEREDITO.** O veredito é o da validação com o critério pré-registrado (`validacao_v2.2.md`): **PASSOU**. Esta análise foi pedida depois, para ler a robustez do número; nenhum resultado dela troca o veredito.

## (a) Sem os pares cuja review apareceu na calibração

Excluídos (3): P18, P26, P30.

| recorte | n | VP | FP | FN | VN | precisão [IC95] | recall [IC95] |
|---|---|---|---|---|---|---|---|
| completa · todos | 40 | 23 | 4 | 2 | 11 | 0.852 [0.675, 0.941] | 0.92 [0.75, 0.978] |
| completa · publicado | 20 | 12 | 2 | 1 | 5 | 0.857 [0.601, 0.96] | 0.923 [0.667, 0.986] |
| completa · local | 20 | 11 | 2 | 1 | 6 | 0.846 [0.578, 0.957] | 0.917 [0.646, 0.985] |
| sem calibração · todos | 37 | 20 | 4 | 2 | 11 | 0.833 [0.641, 0.933] | 0.909 [0.722, 0.975] |
| sem calibração · publicado | 20 | 12 | 2 | 1 | 5 | 0.857 [0.601, 0.96] | 0.923 [0.667, 0.986] |
| sem calibração · local | 17 | 8 | 2 | 1 | 6 | 0.8 [0.49, 0.943] | 0.889 [0.565, 0.98] |

Sem esses pares, a diferença de precisão entre os lados é 0.057, e o critério seria atendido — informativo.

## (b) IC95 por bootstrap de reviews

10000 reamostras de REVIEWS com reposição (pares da mesma review entram e saem juntos); percentis 2,5 e 97,5. Ao lado, o Wilson por par, da validação.

| recorte | reviews | pares | precisão: bootstrap · Wilson | recall: bootstrap · Wilson |
|---|---|---|---|---|
| todos | 34 | 40 | [0.677, 1.0] · [0.675, 0.941] | [0.792, 1.0] · [0.75, 0.978] |
| publicado | 19 | 20 | [0.636, 1.0] · [0.601, 0.96] | [0.75, 1.0] · [0.667, 0.986] |
| local | 19 | 20 | [0.625, 1.0] · [0.578, 0.957] | [0.727, 1.0] · [0.646, 0.985] |

## (c) Pares que compartilham a review

### Dentro da amostra de validação

**Review 1** — the-substance/negativas

| amostra | par | lado | tema | dono | juiz |
|---|---|---|---|---|---|
| validação | P02 | publicado | Duração excessiva e ritmo lento | sim | sim |
| validação | P36 | publicado | Roteiro sem desenvolvimento | sim | sim |

**Review 2** — incendies/positivas

| amostra | par | lado | tema | dono | juiz |
|---|---|---|---|---|---|
| validação | P03 | publicado | Direção de Denis Villeneuve | sim | sim |
| validação | P37 | local | impacto emocional intenso | sim | sim |

**Review 3** — mother-2017/negativas

| amostra | par | lado | tema | dono | juiz |
|---|---|---|---|---|---|
| validação | P05 | local | excesso de metáforas e simbolismo | não | sim |
| validação | P20 | publicado | Alta carga alegórica e excesso de simbolismo | não | sim |

**Review 4** — anatomy-of-a-fall/medianas

| amostra | par | lado | tema | dono | juiz |
|---|---|---|---|---|---|
| validação | P12 | local | ritmo lento e alongado | não | não |
| validação | P27 | local | críticas ao sistema judicial francês | não | não |

**Review 5** — napoleon-2023/negativas

| amostra | par | lado | tema | dono | juiz |
|---|---|---|---|---|---|
| validação | P13 | local | Inaccuracy histórica | sim | sim |
| validação | P39 | publicado | Retrato de Napoleão | sim | sim |

**Review 6** — the-substance/positivas

| amostra | par | lado | tema | dono | juiz |
|---|---|---|---|---|---|
| validação | P19 | local | uso de metáforas e simbolismo | sim | sim |
| validação | P21 | publicado | Metáfora da autodestruição e padrões de beleza | sim | sim |

### Entre a validação e a calibração (juiz = a mesma versão congelada, na calibração)

**Review 1** — the-substance/positivas

| amostra | par | lado | tema | dono | juiz |
|---|---|---|---|---|---|
| validação | P18 | local | horror corporal e efeitos visuais extremos | sim | sim |
| calibração | P11 | publicado | Body horror extremo e efeitos práticos | sim | sim |

**Review 2** — anatomy-of-a-fall/positivas

| amostra | par | lado | tema | dono | juiz |
|---|---|---|---|---|---|
| validação | P26 | local | desempenho atorial | sim | sim |
| calibração | P37 | publicado | Direção e atmosfera realista | sim | sim |

**Review 3** — anatomy-of-a-fall/negativas

| amostra | par | lado | tema | dono | juiz |
|---|---|---|---|---|---|
| validação | P30 | local | ritmo lento e monótono | sim | sim |
| calibração | P08 | local | final aberto e frustrante | sim | sim |
