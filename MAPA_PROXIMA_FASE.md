# Mapa da próxima fase — o que falta para publicar (Entrega 5, v1.9.11)

Levantamento, **sem implementação**. Substitui a versão da v1.9.10, cujo
item nº 1 ("ligar o narrador novo ao pipeline") foi ENTREGUE nesta sessão e
saiu da lista.

## O que mudou desde o mapa anterior

**Resolvido:** o pipeline de produção usa o narrador novo (briefing
determinístico + best-of-3 + verificações da v1.9.9/v1.9.10 + modelo
fixado). O narrador antigo está arquivado. `scripts/best_of_3.py` virou
invólucro sobre o mesmo código — não há mais duas implementações.

**Encontrado ao integrar, e corrigido junto** (nenhum dos dois estava na
lista porque ninguém sabia que existiam):
- `PROVIDER_POR_ESTAGIO`/`MODELO_POR_ESTAGIO` (v1.9.8) eram configuração
  **inerte**: o default do argparse para `--provider` nunca era `None`, e
  forçava todos os estágios. A narrativa rodava em DeepSeek com
  `gemini-3.7-flash` "fixado";
- `SPEC_VERSION` estava parada em `"1.9.0"`, então todo `resultado/*.json`
  de v1.9.1 a v1.9.10 carimbou a versão errada.

**Encontrado ao integrar, NÃO corrigido** (entra na lista abaixo como item
novo): `--offline` não é reproduzível para filme coletado sob outra
estratégia de posicionamento (item 6).

## Os itens, e o que cada um exige

### 1. Republicar `resultado/*.json` com o pipeline novo

**Pronto para acontecer** — é a primeira vez que isto é verdade. Os 3 filmes
já foram gerados de ponta a ponta em `resultado/v1911-integracao/`, com 0
flags mecânicas nos três. O que falta é a DECISÃO de sobrescrever, mais a
leitura humana dos textos.

**Consequência VISÍVEL ao usuário, medida** (por isso não é mecânico):
os shares mudam sob as fronteiras C, e o rótulo de peso muda com eles.

| filme | shares publicados | shares novos |
|---|---|---|
| `cure` | 3 / 17 / 79 | **2 / 8 / 90** |
| `cidade-de-deus` | 1 / 8 / 91 | **1 / 3 / 96** |
| `the-invite-2026` | 3 / 18 / 79 | **2 / 7 / 91** |

E a cota de análise vai de 50/20/30 para 40/40/40 por bucket — o grupo
mediano passa a ser lido com a mesma profundidade dos outros dois.

**Efeito colateral do share novo, digno de leitura antes de publicar:** com
`negativas` e `medianas` ambos abaixo de 15%, os DOIS recebem o mesmo rótulo
("uma fração mínima das notas"), diferindo só pelo percentual entre
parênteses. Acontece nos 3 filmes. Não é defeito de código — é o que o
histograma diz —, mas é uma frase que o leitor vê duas vezes.

**Depende de:** nada técnico. Só da decisão.

### 2. Schema de eixos, lift e estado `contraste`

Mudança na camada de CLASSIFICAÇÃO (§D), que fica em DeepSeek e está
calibrada/auditada. Se o formato de `temas` mudar, `briefing.montar_briefing`
muda junto — é ele que consome a saída da classificação.

**Depende de:** nada. **Bloqueia:** o item 3 (a spec já registra, desde a
v1.9.5, que a aplicação de S2 fica "para a sessão do schema") e,
idealmente, o item 1 — publicar duas vezes seguidas (uma com o schema
atual, outra com o novo) é trabalho duplicado.

### 3. Seleção temporal S2 (70/30 recente/antigo)

Medida e recomendada na v1.9.5, não aplicada. A decisão de QUAL variante já
foi tomada; falta aplicar. **Depende de:** item 2, por decisão registrada.

### 4. Janela temporal declarada na interface

`janela_temporal` e `distribuicao_pagina_origem` são gravados em
`meta.json` desde a v1.9.1/v1.9.2 e agora aparecem também no bloco `coleta`
do JSON de resultado — mas **não são expostos ao usuário**. Se S2 (item 3)
entrar, a janela deixa de ser detalhe de coleta e passa a descrever o
material que o narrador leu.

**Depende de:** item 3 para virar necessidade; do item 5 para ter onde
aparecer.

### 5. Frontend não conhece nenhum campo novo

Campos que o frontend hoje ignora: `estado_piso` (4 estados, v1.9.0),
`verificacao_narrativa` e `narrativa_selecao` (v1.9.11), `coleta`
(`janela_temporal`, `distribuicao_pagina_origem`), e o que os itens 2 e 4
acrescentarem. Verificado nesta sessão: o frontend lê **apenas** o campo
`narrativa` da etapa [D2] — a telemetria toda passa ao largo.

**Depende de:** 1, 2 e 4 estarem decididos, para não mexer duas vezes.

### 6. `--offline` não é reproduzível após mudança de posicionamento (NOVO)

Achado ao rodar a Entrega 2: `the-invite-2026` **falhou** em `--offline`
pedindo `rated_2_5_page_5.html`, que nunca foi cacheada. O cache tem as
páginas 1,2,3,4,6,8 daquele nível — o conjunto que a estratégia de
posicionamento da época escolheu. O bruto é persistido (v1.9.0), mas a
ESCOLHA de páginas é recomputada a cada execução, e ela mudou (v1.9.2
geométrica → v1.9.5 frações da profundidade real).

Consequência: reprocessar um filme antigo offline pode exigir rede, e
**quanto mais antiga a coleta, mais provável a divergência**. Os 3 filmes do
catálogo: 2 rodaram offline, 1 não.

Não corrigido — é camada de coleta, fora do escopo desta sessão. Duas
direções possíveis, nenhuma avaliada: (a) o pipeline consumir o bruto
persistido diretamente, sem recomputar posição (o bruto já tem
`pagina_origem` por review); (b) `meta.json` gravar as posições REALMENTE
buscadas e o modo offline honrá-las.

**Depende de:** nada. **Bloqueia:** nada hoje — mas é o que decide se o
catálogo de 35 filmes é reprocessável sem rede quando o narrador mudar de
novo.

## Ordem recomendada (não vinculante)

```
2 (schema de eixos/lift/contraste)
   │
   └──▶ 3 (aplicar S2)
             │
             └──▶ 1 (republicar — UMA vez, com tudo decidido)
                        │
                        ├──▶ 4 (janela temporal na interface)
                        │         │
                        └─────────┴──▶ 5 (frontend)

6 (--offline reproduzível) — independente, sem bloquear ninguém
```

Se a prioridade for **ver o produto no ar antes**, o item 1 pode ir sozinho
e primeiro: os 3 JSONs já existem e passam limpos. O custo de publicar antes
do item 2 é republicar de novo depois.

## Fora do escopo desta lista

Custo e prazo — o mapa é só dependência estrutural. Também não inclui
parâmetros já fechados (fronteiras, cota, piso escalonado, calibração da
classificação, modelo de narrativa).
