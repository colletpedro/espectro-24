# Fontes auto-hospedadas

## `inter-latin-var.woff2`

**Inter**, subconjunto **latin**, variável (peso 400–700). 85 KB.

- **Licença:** SIL Open Font License 1.1 — texto completo em `OFL.txt`.
  A OFL permite uso, incorporação e redistribuição, inclusive comercial;
  exige que a licença acompanhe o arquivo (é o que este diretório faz) e
  proíbe vender a fonte isolada.
- **Origem do arquivo:** subconjunto latin servido pelo Google Fonts
  (`fonts.gstatic.com`, Inter v20), baixado uma vez e versionado aqui.
  **Não** é puxado de CDN em runtime — ver o porquê abaixo.

### Por que auto-hospedada, e não `<link>` para o Google Fonts

O cabeçalho de `css/styles.css` registra a decisão de **offline-first**:
o site funciona por `file://`, sem CORS, sem requisição de rede. Um
`@import` ou `<link>` para CDN de terceiro quebraria as três coisas de
uma vez e ainda exporia o IP de quem lê a página a um terceiro. O arquivo
local mantém a promessa; o custo é 85 KB versionados no repositório.

### Por que NÃO existe arquivo da San Francisco aqui

O pedido original era "a fonte que a Apple usa" — a **San Francisco (SF
Pro)**. Ela **não pode** ser embutida: a licença da Apple restringe o uso
a mock-ups de interface para iOS/OS X/tvOS, e não autoriza redistribuição
nem uso como webfont em site próprio. Nenhum arquivo de SF Pro é baixado,
hospedado ou referenciado neste projeto.

A saída legal para ter SF de verdade é a **pilha de fontes de sistema**
(`-apple-system, BlinkMacSystemFont, ...`): o navegador usa a SF já
instalada no aparelho do leitor, sem o site distribuir nada. É a
variante 1 da linha de metadados da ficha (ver `?ficha=sistema`).
