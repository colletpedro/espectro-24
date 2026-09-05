# Fase Histograma — sondagem da distribuição real de notas (v1.4.0, Etapa A)

**Data:** 2026-07-21
**Veredito do GATE: APROVADO.** O histograma é extraível de forma confiável,
com estrutura estável e um caso-limite bem caracterizado. Custo da sondagem:
**2 requisições** ao Letterboxd (teto autorizado: 4).

Este documento registra o que foi validado ao vivo, para que a próxima pessoa
não precise re-sondar nem adivinhar seletor.

---

## 1. Endpoint

```
https://letterboxd.com/csi/film/<slug>/rating-histogram/
```

Fragmento **CSI** (server-rendered, sem JS), retorna HTML parcial. Funcionou
de primeira, com os mesmos headers/delay/encoding já validados na Fase 0
(`config.HEADERS`, `DELAY_SECONDS`) — nenhum header novo foi necessário e não
houve resposta anti-bot.

**Por que não a página principal do filme** (`/film/<slug>/`): o fragmento CSI
é ~5,8 KB contra centenas de KB da página completa, e expõe exatamente o dado
desejado sem depender do layout da página inteira. Menos banda, menos
superfície de quebra.

Cache: `resultado/cache/_histograma/<slug>.html`, no mesmo padrão dos demais
(`urls.histogram_cache_key`). **1 requisição por filme, para sempre.**

---

## 2. Estrutura do fragmento

```html
<div class="rating-histogram">
  <table class="chart">
    <tbody>
      <tr class="column" style="--value: 0.0041...">
        <th class="_sr-only" scope="row">half-★</th>
        <td class="cell">
          <a class="barcolumn tooltip"
             href="/film/cure/ratings/rated/%C2%BD/by/rating/"
             title="456 half-★ ratings (0%)">
            <span class="_sr-only">456 (0%)</span>
            <span class="bar"><span class="fill"></span></span>
          </a>
        </td>
      </tr>
      … (10 linhas no total)
    </tbody>
  </table>
</div>
```

| Item | Valor validado |
|---|---|
| Linhas | **Sempre 10**, uma por nível, em ordem crescente (0.5 → 5) |
| Nível | `th._sr-only`, em glifos: `half-★`, `★`, `★½`, `★★`, … `★★★★★` |
| **Contagem** | **atributo `title` do `.barcolumn`** |
| Fração normalizada | `style="--value: 0.0041…"` na `<tr>` (não usada; o `title` é exato) |

### Seletores adotados (`parser.parse_rating_histogram`)

- Linhas: `table.chart tbody tr`
- Nível: texto do `th` → `half-★` = 0.5 (caso especial); senão
  `count("★") + 0.5 se "½"`
- Contagem: regex `^([\d,]+)` sobre o `title` do `.barcolumn`

---

## 3. Armadilhas encontradas (as três importam)

### 3.1 Nível zerado NÃO tem `<a>`

Num filme com poucas notas, níveis sem nenhuma nota trocam a âncora por um
`<span>`:

```html
<tr class="column" style="--value: 0.0;">
  <th class="_sr-only" scope="row">★½</th>
  <td class="cell">
    <span class="barcolumn tooltip" title="No ★½ ratings">
      <span class="_sr-only">0 (0%)</span> …
    </span>
  </td>
</tr>
```

Um parser que buscasse `a.barcolumn` **perderia silenciosamente os zeros** e
produziria um total inflado — erro que só apareceria em filmes pequenos, isto
é, justamente onde o denominador é frágil. Por isso o seletor é `.barcolumn`
(qualquer tag) e o `title` sem número resolve para `0`.

### 3.2 O `_sr-only` da barra ABREVIA — não usar como fonte

O `<span class="_sr-only">` dentro da barra mostra `23.4K`, `111K`, `87.4K`.
Usá-lo custaria precisão. O atributo `title` traz o número exato com
separador de milhar (`110,990`). **O `title` é a única fonte confiável.**

### 3.3 Singular/plural e "No"

Três formas observadas, todas cobertas pelo regex:

| `title` | Contagem |
|---|---|
| `456 half-★ ratings (0%)` | 456 |
| `1 half-★ rating (4%)` | 1 (singular) |
| `No ★½ ratings` | 0 |

Os percentuais do próprio `title` são **arredondados pelo Letterboxd** e
somam 99–101%; o pipeline os ignora e calcula os shares a partir das
contagens brutas.

---

## 4. Extrações reais (evidência)

### `cure` — 375.278 notas

| Nível | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 3.5 | 4 | 4.5 | 5 |
|---|---|---|---|---|---|---|---|---|---|---|
| Notas | 456 | 1.037 | 989 | 4.251 | 6.214 | 23.371 | 41.371 | 110.990 | 87.357 | 99.242 |

Agregado: **negativas 3% · medianas 17% · positivas 79%**

### `como-fazer-um-curta-metragem-…` (filme minúsculo) — 26 notas

| Nível | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 3.5 | 4 | 4.5 | 5 |
|---|---|---|---|---|---|---|---|---|---|---|
| Notas | 1 | 2 | **0** | 2 | 2 | 8 | 1 | 4 | **0** | 6 |

Agregado: **negativas 27% · medianas 35% · positivas 38%**
(exercita os dois níveis zerados de 3.1)

Ambos os fragmentos foram salvos como fixtures — `fixtures/histograma_cure.html`
e `fixtures/histograma_filme_minusculo.html` — e os testes de
`tests/test_distribuicao.py` rodam **sem rede** sobre eles.

---

## 5. Robustez / degradação

`parse_rating_histogram` só devolve dados se os **10 níveis canônicos**
aparecerem exatamente uma vez; qualquer divergência (layout mudou, fragmento
vazio, endpoint trocado) retorna `None`. `collect_distribuicao` converte
qualquer falha — rede, HTTP, anti-bot, estrutura inesperada — em `None`
também.

Consequência de design (§3b da SPEC): a ausência do dado **não é erro**. O
narrador volta automaticamente às regras da v1.2.1 (proibição de prevalência),
o render volta ao disclaimer antigo e o frontend omite os shares. Nenhuma
exceção escapa para o pipeline — perder a distribuição não justifica abortar
uma coleta que já custou dezenas de requisições.

**Risco conhecido (não mitigado):** se o Letterboxd trocar o texto do `title`
(ex.: localizar para outro idioma, ou mudar `No ★½ ratings`), a contagem daquele
nível vira 0 em silêncio — o formato do `title` é contrato não-documentado de
terceiro. A validação estrutural pega mudança de layout, mas não mudança de
redação. Mesma classe de ressalva já registrada para o detector de spoiler
(SPEC §2.1).
