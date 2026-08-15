"""CLI (SPEC §E / B1): nome do filme ou --slug."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .config import (
    BEST_OF_N,
    COTA_POR_BUCKET,
    DADOS_BRUTO_DIR,
    DEFAULT_PROVIDER,
    ORCAMENTO_PAGINAS_POR_BUCKET,
    ORDENACAO_DEFAULT,
    ORDENACOES,
    PROVIDER_ENV_KEYS,
    SPEC_VERSION,
)
from .fetcher import AntiBotError, Fetcher
from .ficha import buscar_ficha, resolver_ano_letterboxd, titulo_ano_de_slug
from .collector import collect_distribuicao
from .pipeline import resolve_slug, run_pipeline, total_observado
from .render import (
    aplicar_distribuicao,
    build_output,
    render_terminal,
    write_json,
)
from .narrador import narrar, telemetria_para_json
from .synthesize import ProviderError


def _parse_args(argv):
    p = argparse.ArgumentParser(
        prog="espectro24",
        description="Agrega reviews do Letterboxd em 3 buckets por nota e "
                    "sintetiza cada um via LLM.",
    )
    p.add_argument("filme", nargs="?", help="nome do filme para buscar o slug")
    p.add_argument("--slug", help="slug direto do Letterboxd (pula a busca)")
    p.add_argument("--cache-dir", default="resultado/cache",
                   help="raiz do cache em disco (default: resultado/cache)")
    p.add_argument("--out-dir", default="resultado")
    p.add_argument("--provider", choices=sorted(PROVIDER_ENV_KEYS),
                   default=DEFAULT_PROVIDER,
                   help="provider do LLM (gemini|anthropic|deepseek); "
                       f"default (v1.8.0): {DEFAULT_PROVIDER!r} — ver "
                       "DEFAULT_PROVIDER em config.py e VALIDACAO_DEEPSEEK.md "
                       "para a decisão. anthropic/gemini seguem selecionáveis "
                       "passando a flag explicitamente (requer "
                       "ANTHROPIC_API_KEY / GEMINI_API_KEY no ambiente)")
    p.add_argument("--model", default=None,
                   help="modelo do LLM; default depende do provider "
                       "resolvido (ver PROVIDER_DEFAULT_MODELS)")
    p.add_argument("--cota", type=int, default=COTA_POR_BUCKET,
                   help="cota de análise POR BUCKET (v1.9.0; era por nível "
                       f"até a v1.8.2). Default: {COTA_POR_BUCKET}")
    p.add_argument("--orcamento-paginas", type=int,
                   default=ORCAMENTO_PAGINAS_POR_BUCKET,
                   help="orçamento de páginas POR BUCKET (v1.9.1, §3[B]); "
                       "substitui o antigo teto por nível — igual para os "
                       "três buckets, não importa quantos níveis cada um "
                       f"tem. Default: {ORCAMENTO_PAGINAS_POR_BUCKET}")
    p.add_argument("--ordenacao", choices=sorted(ORDENACOES),
                   default=ORDENACAO_DEFAULT,
                   help="ordenação da listagem — PARÂMETRO DE AMOSTRAGEM "
                       "(§2.3), gravado no meta.json do bruto e na chave de "
                       f"cache. Default: {ORDENACAO_DEFAULT!r} "
                       f"({ORDENACOES[ORDENACAO_DEFAULT]}, cronológica). "
                       "'atividade' ordena por ENGAJAMENTO e enviesa para "
                       "review longa e promovida")
    p.add_argument("--dados-dir", default=DADOS_BRUTO_DIR,
                   help="raiz do superset bruto persistido (§3[B']); "
                       f"default: {DADOS_BRUTO_DIR}")
    p.add_argument("--no-synth", action="store_true",
                   help="não chamar o LLM (só coleta + metadados)")
    p.add_argument("--offline", action="store_true",
                   help="usar somente cache; erro se faltar página")
    p.add_argument("--tom", choices=["estruturado", "narrativo", "ambos"],
                   default="estruturado",
                   help="tom da saída (MECANISMO DE DESENVOLVIMENTO para A/B, "
                        "SPEC §D2): estruturado (default, comportamento atual), "
                        "narrativo (só a prosa, mas metadados/avisos permanecem), "
                        "ambos (os dois lado a lado). narrativo/ambos gastam +1 "
                        "chamada LLM (o narrador)")
    p.add_argument("--reuse-synthesis", action="store_true",
                   help="reaproveita a síntese de <out-dir>/<slug>.json existente "
                        "(não recoleta nem re-sintetiza); só (re)gera a narrativa "
                        "e renderiza. Requer --slug. Para A/B de tom sem re-gastar "
                        "as chamadas de síntese")
    p.add_argument("--titulo", default=None,
                   help="título para a busca da ficha TMDB (v1.3.0); default: "
                       "derivado do slug (ver ficha.titulo_ano_de_slug)")
    p.add_argument("--ano", type=int, default=None,
                   help="ano para desambiguar a busca da ficha TMDB (v1.3.0); "
                       "default: derivado do slug quando o slug tem sufixo -YYYY")
    p.add_argument("--no-ficha", action="store_true",
                   help="pula a busca da ficha TMDB (v1.3.0)")
    p.add_argument("--no-distribuicao", action="store_true",
                   help="pula a busca do histograma de notas do Letterboxd "
                       "(v1.4.0); sem ele o narrador volta às regras da "
                       "v1.2.1 (proibição de prevalência)")
    return p.parse_args(argv)


def _pick_slug(fetcher, query):
    resultados = resolve_slug(fetcher, query)
    if not resultados:
        print(f"Nenhum filme encontrado para {query!r}.", file=sys.stderr)
        sys.exit(2)
    if len(resultados) == 1:
        return resultados[0].slug
    print(f"Múltiplos filmes para {query!r} — reexecute com --slug <slug>:",
          file=sys.stderr)
    for r in resultados[:10]:
        ano = f" ({r.year})" if r.year else ""
        print(f"  --slug {r.slug:35} {r.name}{ano}", file=sys.stderr)
    sys.exit(3)


def main(argv=None):
    # Carrega .env do diretório atual, se existir (no-op silencioso se não
    # existir). Sem argumentos: NÃO sobrescreve variáveis já exportadas no
    # ambiente (comportamento default do python-dotenv). Precisa vir antes de
    # qualquer leitura de ambiente/detecção de provider abaixo.
    load_dotenv()

    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if not args.slug and not args.filme:
        print("Informe o nome do filme ou --slug.", file=sys.stderr)
        sys.exit(2)
    if args.reuse_synthesis and not args.slug:
        print("--reuse-synthesis requer --slug (para localizar o JSON).",
              file=sys.stderr)
        sys.exit(2)

    quer_narrar = args.tom in ("narrativo", "ambos")
    # Vai chamar o LLM? síntese (fresh, com síntese) e/ou narrador.
    vai_sintetizar = not args.no_synth and not args.reuse_synthesis
    vai_narrar = quer_narrar and (args.reuse_synthesis or not args.no_synth)

    if vai_sintetizar or vai_narrar:
        # Falha rápido (antes de gastar qualquer requisição/coleta) se o
        # provider/chave não puder ser resolvido.
        try:
            from .synthesize import detect_provider
            detect_provider(args.provider)
        except ProviderError as e:
            print(f"Provider LLM: {e}", file=sys.stderr)
            print("(ou rode com --no-synth / --tom estruturado)", file=sys.stderr)
            sys.exit(5)

    # --- Caminho A/B: reaproveita síntese de um JSON existente ---
    if args.reuse_synthesis:
        json_path = Path(args.out_dir) / f"{args.slug}.json"
        if not json_path.exists():
            print(f"--reuse-synthesis: {json_path} não existe (rode a síntese "
                  f"primeiro).", file=sys.stderr)
            sys.exit(2)
        output = json.loads(json_path.read_text(encoding="utf-8"))
        output["spec_version"] = SPEC_VERSION  # re-renderizado sob a versão atual
        slug = args.slug
        print(f"Reaproveitando síntese de {json_path} "
              f"(0 chamadas de síntese).", file=sys.stderr)
        fetcher_net = 0
        # v1.4.0: a distribuição é buscada mesmo reaproveitando a síntese —
        # é 1 requisição cacheada, e sem ela a narrativa regenerada cairia
        # nas regras antigas. Aplicada pelo MESMO helper do caminho fresh.
        if not args.no_distribuicao:
            f_dist = Fetcher(cache_dir=args.cache_dir, offline=args.offline)
            distrib = collect_distribuicao(f_dist, slug)
            aplicar_distribuicao(output, distrib)
            fetcher_net = f_dist.n_network
            if distrib is None:
                print("⚠️  Distribuição de notas indisponível — narrativa segue "
                      "sob as regras da v1.2.1 (sem prevalência).", file=sys.stderr)
    else:
        fetcher = Fetcher(cache_dir=args.cache_dir, offline=args.offline)
        try:
            slug = args.slug or _pick_slug(fetcher, args.filme)

            def _on_level(nb):
                parada = ("teto" if nb.parou_por_teto
                          else "esgotado" if nb.esgotado else "alvo")
                print(f"  [{nb.nivel}★] {nb.n_bruta} brutas / "
                      f"{nb.n_estimada_valida} válidas(heur) / "
                      f"{nb.paginas_gastas}p → parada: {parada}", file=sys.stderr)

            print(f"Coletando superset de {slug} "
                  f"(ordenação {ORDENACOES[args.ordenacao]})...", file=sys.stderr)
            buckets, superset, distrib = run_pipeline(
                fetcher, slug,
                data_coleta=datetime.now(timezone.utc).isoformat(),
                model=args.model, provider=args.provider, synth=not args.no_synth,
                cota_por_bucket=args.cota,
                orcamento_paginas_bucket=args.orcamento_paginas,
                on_level=_on_level, distribuicao=not args.no_distribuicao,
                ordenacao=ORDENACOES[args.ordenacao], dados_dir=args.dados_dir,
            )
        except AntiBotError as e:
            print(f"\n⛔ ANTI-BOT: {e}", file=sys.stderr)
            print("Parando conforme restrição. Não escalando para evasão.",
                  file=sys.stderr)
            sys.exit(4)
        output = build_output(
            slug=slug, buckets=buckets,
            data_coleta=datetime.now(timezone.utc).isoformat(),
            origens=fetcher.origins, total_observado=total_observado(superset),
            distribuicao=distrib,
            # v1.9.0 (§4): o meta.json do bruto espelhado no resultado, mais
            # o total persistido — auditoria sem abrir `dados/`.
            coleta={**superset.meta, "n_reviews_bruto": superset.n_reviews},
        )
        if not args.no_distribuicao and distrib is None:
            print("⚠️  Distribuição de notas indisponível — narrativa segue "
                  "sob as regras da v1.2.1 (sem prevalência).", file=sys.stderr)
        fetcher_net = fetcher.n_network

    # --- [1.1-1.4] ficha técnica via TMDB (aditiva, nunca bloqueia) ---
    if args.no_ficha:
        output["ficha"] = None
    else:
        titulo = args.titulo
        ano = args.ano
        ano_fonte = "argumento" if args.ano is not None else None
        if titulo is None:
            titulo_derivado, ano_derivado = titulo_ano_de_slug(slug)
            titulo = titulo_derivado
            if ano is None:
                ano = ano_derivado
                if ano is not None:
                    ano_fonte = "slug"
        if ano is None:
            # v1.7.0 (Tarefa 1.1b) — sem ano no slug: 1 requisição à página
            # do filme no Letterboxd, cacheada, mesmo fetcher/headers/delay
            # já validados pelo resto do pipeline. Em --reuse-synthesis não
            # existe um `fetcher` da coleta (não recoleta nada) — cria um
            # dedicado, mesmo padrão já usado para a distribuição reaproveitada.
            f_ano = fetcher if not args.reuse_synthesis else Fetcher(
                cache_dir=args.cache_dir, offline=args.offline)
            ano = resolver_ano_letterboxd(f_ano, slug)
            if ano is not None:
                ano_fonte = "letterboxd"
        if ano is None:
            # v1.7.0 (Tarefa 1.1c) — ano segue indisponível: NÃO busca a
            # ficha (a desambiguação por só o título já causou o defeito real
            # do `cure`, resolvido para "The Cure" 2026 em vez de 1997).
            # Melhor nenhuma ficha do que arriscar a do filme errado.
            output["ficha"] = None
            output["ficha_indisponivel"] = "ano_desconhecido"
        else:
            ficha, aviso_ficha, ficha_descartada = buscar_ficha(
                titulo, ano, cache_dir=Path(args.cache_dir) / "_tmdb",
                ano_fonte=ano_fonte)
            output["ficha"] = ficha
            if ficha_descartada:
                output["ficha_descartada"] = ficha_descartada
            if aviso_ficha:
                print(f"⚠️  Ficha TMDB: {aviso_ficha}", file=sys.stderr)

    # --- [D2] narração (etapa pós-síntese) ---
    # v1.9.11: o caminho de produção passa a ser o BRIEFING DETERMINÍSTICO +
    # BEST-OF-3 (`narrador.narrar`). Até a v1.9.10 aqui vivia
    # `narrate_output`, o narrador pré-briefing — e todo o trabalho das três
    # versões anteriores rodava só em `scripts/best_of_3.py`, fora do
    # produto. Custo declarado: `BEST_OF_N` chamadas por filme (4 no pior
    # caso, com o retry direcionado) contra 1 de antes.
    if vai_narrar:
        print(f"Gerando narrativa ({BEST_OF_N} chamadas LLM — best-of-"
              f"{BEST_OF_N})...", file=sys.stderr)
        res = narrar(output, provider=args.provider, model=args.model)
        output["narrativa"] = res.texto
        # As flags MECÂNICAS, computadas sobre o texto (não declaradas pelo
        # LLM, como eram as do narrador antigo — sob briefing ele não
        # declara nada, só escreve prosa).
        output["verificacao_narrativa"] = res.verificacao
        # O registro da escolha do best-of-3 — sem o briefing (função
        # determinística do próprio output) e sem os textos perdedores.
        output["narrativa_selecao"] = telemetria_para_json(res)
        if res.falhou:
            print("⚠️  Narrativa: nenhuma das amostras devolveu texto.",
                  file=sys.stderr)
        else:
            v = res.verificacao
            print(f"  narrativa: candidato #{res.escolha['indice']} "
                  f"({res.escolha['motivo']}/{res.escolha['criterio_decisivo']}) "
                  f"· {v['n_flags']} flags · {v['n_resenha_speak']} clichês",
                  file=sys.stderr)

    # O editor [E2] foi APOSENTADO na v1.9.10 (SPEC.md, "Fechamento do
    # narrador") — código arquivado em `experimentos-editor-e2-arquivado/`.
    # A narrativa publicada é sempre a do narrador diretamente, o mesmo
    # formato de saída que o antigo caminho "editor desligado" já tinha
    # (era o mais testado e o mais conservador dos dois). `edicao_flags`/
    # `narrativa_bruta` não são mais gravados aqui; `resultado/*.json`
    # publicados ANTES desta versão continuam com o campo, e
    # `render_terminal` continua sabendo lê-lo (compatibilidade histórica).

    path = write_json(output, args.out_dir)
    print(render_terminal(output, tom=args.tom))
    print(f"\nJSON salvo em {path}", file=sys.stderr)
    print(f"Requisições de rede nesta execução: {fetcher_net}", file=sys.stderr)


if __name__ == "__main__":
    main()
