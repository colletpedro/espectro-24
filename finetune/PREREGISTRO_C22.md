# PRÉ-REGISTRO — avaliação de produção do treinado no C22

Data: 2026-11-05. Commitado ANTES de gerar. Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**.
Base: decisões do dono (Opção A do `RESULTADO_FASE4.md`). O veredito da Fase 4
(NÃO PUBLICÁVEL: C1 e C3) fica como está.

## Registros da Fase 4
- **C6 da Fase 4:** o dono confirmou que quis dizer que os DOIS lados eram publicáveis; o
  registro "ambos" 5/5 está correto.
- **Teste de 30 filmes consumido.** As saídas da Fase 4 (treinado, publicado, base) são dados de
  DESENVOLVIMENTO da guarda de quantidade. Legítimo: a avaliação nova é em filmes nunca vistos.

## Modelo e geração
- `espectro-qwen3-8b-treinado`, GGUF `e488697e7215f12c35c7fdfe9206a5af4438bfe47512a91a8698ad98cdcd6eac`.
- Mesma amostragem (DESVIO_P01: temperature 0,7, top_p 0,8, top_k 20, min_p 0, repeat_penalty 1,0,
  seed 20261019), mesmo prompt (`build_system_prompt`/`build_user_message`), mesma retentativa de
  produção (`synthesize_bucket`; DESVIO_P04), **mais a guarda de quantidade** (`guarda_quantidade.py`,
  sha256 abaixo, lista congelada `a7fcd5a5…`), aplicada em `_construir_temas`.
- Entradas congeladas em `finetune/c22/entrada/` (o Windows não lê bruto nem consenso).

## Filmes
35 filmes, 105 buckets (`finetune/c22/escopo.json`): C22 (55) classificados e não publicados, menos:
- **15 sem classificação** no consenso verificado (ainda não classificados): a-quiet-place-2018,
  batman-begins, bullet-train, fantastic-mr-fox, guardians-of-the-galaxy,
  harry-potter-and-the-philosophers-stone, how-to-make-millions-before-grandma-dies,
  it-was-just-an-accident, scream, the-dark-knight-rises, the-drama, the-empire-strikes-back,
  the-whale-2022, train-dreams, where-is-the-friends-house;
- **5 com pendência de corpus (guarda C14.8):** a amostra analisada tem review nunca classificada:
  logan-2017, mid90s, school-of-rock, superbad, there-will-be-blood.
- Pendência de identidade: nenhuma achada no que o bruto guarda; a conferência contra o TMDB roda na
  publicação e não foi feita (limite). Buckets abaixo de 40 (how-to-train-your-dragon, project-x-2012,
  spider-man-into-the-spider-verse) ficam, descritos.
- O conjunto é este, mesmo que mais filmes sejam classificados depois.

## Critérios (absolutos, ancorados no publicado da Fase 2)
IC95 por bootstrap por filme, 10.000 reamostras, **semente 20261108**, percentil 2,5/97,5, razão das somas.
- **C1:** bullets sem apoio (juiz v2.2 `44606cf1…`, parada no 2º sim): estimativa ≤ 5,6% E limite
  superior < 7,6% (publicado 3,6% + 2,0 / + 4,0).
- **C2:** apoio ≥ 2: limite inferior > 77,8% (publicado 85,6% − δ₂ 7,8).
- **C3:** M1 depois da guarda (lista congelada, sobre o texto publicado): estimativa ≤ 10% E limite
  superior < 15%.
- **C4:** ≥ 97% dos buckets válidos (fora os fora-por-memória) com JSON e validadores de
  `validar_publicado` passando, com a retentativa de produção (105 → ≥ 102).
- **C6:** leitura cega do dono em 5 filmes sorteados (**semente 20261109**, entre os de 3 buckets com
  síntese), só os bullets, pergunta "publicável? S/N"; passa com ≥ 4 de 5.
- **C5 sai.** Motivo registrado: especificidade medida em 30% na Fase 4 (acima do piso de 10%), e
  velocidade (palavra do dono; leitura a confirmar).
- Pré-condição: fluência da guarda ≥ 27/30 (`GUARDA_QUANTIDADE.md`); o `gerar` recusa sem ela.

## Decisão
Se TODOS (C1–C4, C6) passarem, as sínteses geradas nesta rodada são a saída de produção, sem nova
geração. Se algum falhar: resultado negativo, sem publicar.

## Cegueira do dono
Até o C6, nada de C1–C4/M1/taxa do juiz na tela (`finetune/c22/cego/*.log`); não abrir
`finetune/c22/sintese_treinado/`, `juiz/`, `cego/`, `c6_*`.

<!-- preregistro_c22 {"escopo_sha256": "23cc978c5e9e0b350750ef5e2dea7d1f770f216c2218d53fc9694bb756161872", "plano_sha256": "1701d08519845bab892c3348373857d77e7aa00751569d315b631a5cea36c111", "guarda_sha256": "61da0b7d059c7c129532b55bf3d61ab516f991eae1eba2b6af1b80af2c671794"} -->
