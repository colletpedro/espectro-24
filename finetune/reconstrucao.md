# Reconstrução do par da síntese

## 1. Fonte primária (prompt enviado / resposta crua gravados?)

Varridos 1960 arquivos de texto em ['/Users/pedrocollet/Downloads/espectro-24', '/Users/pedrocollet/Downloads/espectro-24-finetune'] (fora código, documentação e cache HTML). Achados com o prompt ou o cabeçalho da mensagem: **0**. Nenhum caminho do código grava o prompt nem a resposta crua da síntese: `synthesize_bucket` guarda só os temas já pós-processados (MEDIDO por leitura do código).

## 2. Remontagem byte a byte

- Código atual × código da época: **294/294** buckets com `system` e `user` idênticos (sha256), remontados com o `src/` de cada commit de síntese.
| commit | filmes | buckets | byte a byte | bruto igual ao de HEAD |
|---|---|---|---|---|
| `1253eb73d` | 19 | 57 | 57 | 19/19 |
| `31c463528` | 31 | 93 | 93 | 31/31 |
| `594786f55` | 1 | 3 | 3 | 1/1 |
| `7d2fa09eb` | 44 | 132 | 132 | 44/44 |
| `d0dee5159` | 3 | 9 | 9 | 3/3 |

- Seleção (n e composição iguais ao publicado): 294/294 buckets.
- Bloco `eixos` reconciliado célula a célula contra o consenso verificado, sobre a amostra remontada: 97/98 filmes (2910 células).
  - spider-man-across-the-spider-verse: ValueError: spider-man-across-the-spider-verse/positivas/impacto_emocional: contei 16/40, o bloco eixos diz 17/40

## 3. O publicado é a saída crua? Não.

Contagens nos 293 buckets utilizáveis (1757 temas): aspas removidas em 3 temas; menções corrigidas (clamp) em 0; buckets com `idioma_invalido` 0, `escopo_suspeito` 0.

Lado a lado (o que o dado guarda da resposta crua):

- **aspas** `eighth-grade/negativas` — Diálogos artificiais e repetitivos: cru = o mesmo texto COM aspas de citação (posições não gravadas) → publicado = As falas da personagem são marcadas por gaguejos e muletas linguísticas como tipo e gucci, o que soa forçado e cansativo.
- **aspas** `eighth-grade/negativas` — Comparações desfavoráveis com outros filmes: cru = o mesmo texto COM aspas de citação (posições não gravadas) → publicado = O longa é comparado negativamente a outras obras do gênero, como Lady Bird e The Edge of Seventeen, que são consideradas superiores.

## 4. Validadores mecânicos atuais sobre o publicado

- Passam todos (publicado): **293/293**
- Passariam todos se o alvo fosse a resposta crua (estimado pelas flags de correção): **291/293**

  - `aspas_bruto` falha em 2: eighth-grade/negativas, wicked-2024/positivas

## 5. Par de leitura: finetune/par_exemplo/whiplash-2014__negativas.json, finetune/par_exemplo/whiplash-2014__negativas.md
