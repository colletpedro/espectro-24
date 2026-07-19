"""CLI (SPEC §E / B1): nome do filme ou --slug."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .config import COTA_POR_NIVEL, PROVIDER_ENV_KEYS, SPEC_VERSION, TETO_PAGINAS
from .fetcher import AntiBotError, Fetcher
from .ficha import buscar_ficha, titulo_ano_de_slug
from .pipeline import resolve_slug, run_pipeline, total_observado
from .render import build_output, render_terminal, write_json
from .synthesize import ProviderError, narrate_output


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
                   help="provider do LLM (gemini|anthropic); sem a flag, "
                       "auto-detecta pela chave presente no ambiente "
                       "(GEMINI_API_KEY / ANTHROPIC_API_KEY); erro se "
                       "ambas ou nenhuma estiverem presentes")
    p.add_argument("--model", default=None,
                   help="modelo do LLM; default depende do provider "
                       "resolvido (ver PROVIDER_DEFAULT_MODELS)")
    p.add_argument("--cota", type=int, default=COTA_POR_NIVEL)
    p.add_argument("--max-pages", type=int, default=TETO_PAGINAS)
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
    else:
        fetcher = Fetcher(cache_dir=args.cache_dir, offline=args.offline)
        try:
            slug = args.slug or _pick_slug(fetcher, args.filme)

            def _on_level(lvl):
                print(f"  [{lvl.nivel}★] {lvl.n_validas} válidas / "
                      f"{lvl.n_brutas} brutas / {lvl.paginas_buscadas}p "
                      f"(filtro {lvl.filtro_aplicado}c, "
                      f"trunc-desc {lvl.n_descartadas_truncamento})", file=sys.stderr)

            print(f"Coletando {slug}...", file=sys.stderr)
            buckets, niveis = run_pipeline(
                fetcher, slug,
                data_coleta=datetime.now(timezone.utc).isoformat(),
                model=args.model, provider=args.provider, synth=not args.no_synth,
                cota=args.cota, max_pages=args.max_pages, on_level=_on_level,
            )
        except AntiBotError as e:
            print(f"\n⛔ ANTI-BOT: {e}", file=sys.stderr)
            print("Parando conforme restrição. Não escalando para evasão.",
                  file=sys.stderr)
            sys.exit(4)
        output = build_output(
            slug=slug, buckets=buckets,
            data_coleta=datetime.now(timezone.utc).isoformat(),
            origens=fetcher.origins, total_observado=total_observado(niveis),
        )
        fetcher_net = fetcher.n_network

    # --- [1.1-1.4] ficha técnica via TMDB (aditiva, nunca bloqueia) ---
    if args.no_ficha:
        output["ficha"] = None
    else:
        titulo = args.titulo
        ano = args.ano
        if titulo is None:
            titulo_derivado, ano_derivado = titulo_ano_de_slug(slug)
            titulo = titulo_derivado
            if ano is None:
                ano = ano_derivado
        ficha, aviso_ficha = buscar_ficha(
            titulo, ano, cache_dir=Path(args.cache_dir) / "_tmdb")
        output["ficha"] = ficha
        if aviso_ficha:
            print(f"⚠️  Ficha TMDB: {aviso_ficha}", file=sys.stderr)

    # --- [D2] narração (etapa pós-síntese) ---
    if vai_narrar:
        print("Gerando narrativa (1 chamada LLM)...", file=sys.stderr)
        res = narrate_output(output, model=args.model, provider=args.provider)
        output["narrativa"] = res.texto
        output["narrativa_flags"] = {
            "idioma_invalido": res.idioma_invalido,
            "escopo_suspeito": res.escopo_suspeito,
            "prevalencia_suspeita": res.prevalencia_suspeita,
            "quantificador_suspeito": res.quantificador_suspeito,
            "aspas_removidas": res.aspas_removidas,
            "falhou": res.falhou,
        }

    path = write_json(output, args.out_dir)
    print(render_terminal(output, tom=args.tom))
    print(f"\nJSON salvo em {path}", file=sys.stderr)
    print(f"Requisições de rede nesta execução: {fetcher_net}", file=sys.stderr)


if __name__ == "__main__":
    main()
