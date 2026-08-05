# Diagnóstico — disparos de `conteudo_adicionado` na regeneração v1.8.1

**Data:** 2026-08-04. **Sessão OFFLINE — zero chamadas de LLM.** Não é bump
de versão (a Tarefa 1 abaixo é telemetria nova, sem mudança de
comportamento).

**Pergunta em aberto:** a checagem `conteudo_adicionado` disparou 6 vezes em
3 filmes na regeneração da v1.8.1 (o `cure` foi descartado após 3
reprovações seguidas por esse motivo), contra 1 vez na validação anterior
(`VALIDACAO_EDITOR_V18.md`, mesmos limiares). Isso é (a) a checagem apertada
demais reprovando edição legítima, ou (b) o modelo realmente inventando com
frequência alta? **Este relatório não responde isso** — ver "Limitação
central" abaixo.

---

## Limitação central (Tarefa 2) — a comparação pedida NÃO é possível com os dados existentes

Antes desta sessão, `editar_narrativa` persistia `frases_sem_origem` e
`similaridade_minima_por_frase` como **um único estado**, sobrescrito a cada
tentativa — ou seja, o JSON salvo só guarda os dados da **última tentativa
avaliada** (aceita ou não), nunca das anteriores. Isso tem uma consequência
direta e importante:

**Nos 7 disparos de `conteudo_adicionado` registrados nos dois conjuntos de
dados (1 na validação + 6 na regeneração), NENHUM tem sua tentativa que
efetivamente disparou a checagem visível nos dados persistidos** — em todo
caso onde `conteudo_adicionado` apareceu em `motivos_por_tentativa`, a
tentativa seguinte (aceita, ou reprovada por outro motivo) já tinha
sobrescrito `frases_sem_origem`/`similaridade_minima_por_frase` antes do
JSON ser salvo. A tabela abaixo mostra isso explicitamente: em nenhuma linha
o "motivo da última tentativa avaliada" é `conteudo_adicionado`, mesmo em
filmes onde esse motivo aparece em `motivos_por_tentativa`.

**Conclusão desta tarefa: não dá para saber, com os dados que já existem em
disco, o que especificamente disparou qualquer uma das 7 reprovações por
`conteudo_adicionado`.** A Tarefa 1 (implementada nesta sessão,
`tentativas_detalhe`) fecha esse buraco daqui para frente — mas só numa
**próxima regeneração** (nova chamada de LLM), não retroativamente sobre o
que já está em `resultado/*.json` ou `resultado/validacao_editor_v18/*.json`.

---

## O que os dados existentes permitem ver (proxy indireto, não a causa)

Por filme, a sequência de motivos (`motivos_por_tentativa`) mostra QUANTAS
vezes e em que ordem cada checagem reprovou, mesmo sem o texto/frases de
cada tentativa individual. E os campos `frases_sem_origem`/`similaridade`
finais — embora não sejam da tentativa que disparou `conteudo_adicionado`
— são, ainda assim, telemetria real da ÚLTIMA tentativa daquele filme, útil
como ponto de referência (não como explicação).

| Fonte | Filme | n_tentativas | Sequência de motivos | Motivo da ÚLTIMA tentativa avaliada | `frases_sem_origem` da última tentativa | similaridade final |
|---|---|---|---|---|---|---|
| VALIDACAO_EDITOR_V18 | cure | 2 | `["conjunto de números do texto foi alterado"]` | (aceita, 2ª) | 2 frases | 0,747 |
| VALIDACAO_EDITOR_V18 | cidade-de-deus | 2 | `["conteudo_adicionado"]` | (aceita, 2ª) | 3 frases | 0,963 |
| VALIDACAO_EDITOR_V18 | the-invite-2026 | 1 | `[]` | (aceita, 1ª) | 1 frase | 0,875 |
| produção v1.8.1 | cure | 4 | `["conteudo_adicionado", "conteudo_adicionado", "conteudo_adicionado", "regressão de honestidade: perspectiva_nao_marcada"]` | `perspectiva_nao_marcada` (4ª, DESCARTADA) | 3 frases | 0,960 |
| produção v1.8.1 | cidade-de-deus | 2 | `["conteudo_adicionado"]` | (aceita, 2ª) | 1 frase | 0,618 |
| produção v1.8.1 | the-invite-2026 | 4 | `["conteudo_adicionado", "regressão de honestidade: perspectiva_nao_marcada", "conteudo_adicionado"]` | (aceita, 4ª) | 3 frases | 0,661 |

**Total de disparos de `conteudo_adicionado` nos dois conjuntos:** 1 (validação) + 6 (produção: 3 no `cure`, 1 no `cidade-de-deus`, 2 no `the-invite-2026`) = **7**. **Nenhum desses 7 tem o texto ou as frases da tentativa correspondente recuperável** — só a contagem e a posição na sequência (`motivos_por_tentativa`).

### O único sinal indireto disponível

Nos 3 filmes da regeneração de produção, a similaridade final ficou entre
0,618 e 0,960 — abaixo da faixa 0,747-0,963 observada na validação anterior,
mas os dois conjuntos se sobrepõem (0,618-0,963 vs 0,747-0,963), então não
dá para dizer, só com isso, que a regeneração produziu edições mais
agressivas em geral. E mesmo essa comparação é sobre a tentativa ACEITA (ou
a última descartada), não sobre as tentativas que falharam por
`conteudo_adicionado` — o dado que importaria para responder a pergunta
central não está disponível.

**Não há inferência adicional a fazer aqui.** Qualquer conclusão sobre "a
checagem está apertada" ou "o modelo inventa muito" exigiria os textos das
tentativas reprovadas, que não existem nos dados de nenhuma das duas
rodadas.

---

## Tarefa 1 — o que passa a ser visível numa PRÓXIMA regeneração

Implementado nesta sessão (offline, sem chamada de LLM): `editar_narrativa`
agora popula `edicao_flags.tentativas_detalhe`, uma lista com **um registro
por tentativa** (aceita ou reprovada, na ordem em que ocorreram):

```json
"tentativas_detalhe": [
  {
    "tentativa": 1,
    "motivo": "conteudo_adicionado",
    "similaridade": 0.42,
    "frases_sem_origem": [
      {"frase": "O saldo geral, no entanto, é positivo.", "similaridade": 0.31},
      {"frase": "...", "similaridade": 0.28}
    ],
    "texto": "<texto COMPLETO devolvido pelo editor nesta tentativa>"
  },
  {
    "tentativa": 2,
    "motivo": "",
    "similaridade": 0.71,
    "frases_sem_origem": [],
    "texto": "<texto final aceito>"
  }
]
```

Isso é telemetria pura — **nenhum comportamento do editor mudou** (mesmos
limiares, mesma política de retentativa/descarte). O que muda é que, na
PRÓXIMA vez que o pipeline rodar (regeneração ou validação), toda tentativa
reprovada por `conteudo_adicionado` (ou qualquer outro motivo) terá seu
texto completo e as frases exatas que a reprovaram persistidos no JSON —
o que faltou nesta análise.

**Testes (mock, zero rede) cobrindo o campo novo**, em `tests/test_editor.py`:
reprovação seguida de aceite registra os dois estados na ordem certa;
`frases_sem_origem` de cada tentativa carrega a MESMA similaridade máxima
usada pela checagem (não um valor recalculado à parte); descarte total
(todas as `1 + EDITOR_MAX_TENTATIVAS` tentativas esgotadas) registra todas,
sem nenhuma "sumir". Suíte: **389 passed** (386 + 3 novos).

---

## Próximo passo (fora do escopo desta sessão, offline)

Para responder a pergunta original ("apertado demais" vs "modelo inventa
muito"), a próxima regeneração — de qualquer um dos 3 filmes, com
`--reuse-synthesis` — já vai produzir `tentativas_detalhe` completo. Com
isso, dá para ler o texto de cada tentativa reprovada e decidir, por
leitura humana, se as frases marcadas eram mesmo inventadas ou só
paráfrases agressivas mal pontuadas pelo limiar atual.
