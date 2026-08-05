"""CLI (SPEC §E / B1): nome do filme ou --slug."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .config import (
    COTA_POR_NIVEL,
    DEFAULT_PROVIDER,
    EDITOR_ATIVO,
    PROVIDER_ENV_KEYS,
    SPEC_VERSION,
    TETO_PAGINAS,
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
from .synthesize import (
    ProviderError,
    editar_narrativa,
    montar_protegidos,
    narrate_output,
)


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
    p.add_argument("--no-edicao", action="store_true",
                   help="pula o passe de edição [E2] (v1.6.0) e publica a "
                       "narrativa crua do narrador; economiza 1 chamada LLM "
                       "(o editor vem LIGADO por padrão desde a v1.8.1 — "
                       "EDITOR_ATIVO=True em config.py —, então esta flag é "
                       "o jeito de desligar pontualmente, ex. para debug ou "
                       "economizar a chamada)")
    p.add_argument("--com-editor", action="store_true",
                   help="liga o passe de edição [E2] explicitamente — "
                       "redundante desde a v1.8.1 (EDITOR_ATIVO=True já é "
                       "o default; ver config.py e VALIDACAO_EDITOR_V18.md "
                       "para a validação que motivou a reativação), mantida "
                       "por compatibilidade")
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

            def _on_level(lvl):
                print(f"  [{lvl.nivel}★] {lvl.n_validas} válidas / "
                      f"{lvl.n_brutas} brutas / {lvl.paginas_buscadas}p "
                      f"(filtro {lvl.filtro_aplicado}c, "
                      f"trunc-desc {lvl.n_descartadas_truncamento})", file=sys.stderr)

            print(f"Coletando {slug}...", file=sys.stderr)
            buckets, niveis, distrib = run_pipeline(
                fetcher, slug,
                data_coleta=datetime.now(timezone.utc).isoformat(),
                model=args.model, provider=args.provider, synth=not args.no_synth,
                cota=args.cota, max_pages=args.max_pages, on_level=_on_level,
                distribuicao=not args.no_distribuicao,
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
            distribuicao=distrib,
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
    if vai_narrar:
        print("Gerando narrativa (1 chamada LLM)...", file=sys.stderr)
        res = narrate_output(output, model=args.model, provider=args.provider)
        output["narrativa"] = res.texto
        # v1.3.1: consensos_usados fica junto de narrativa (mesmo bloco
        # lógico) — artefato de revisão humana do MOVIMENTO 2.
        output["consensos_usados"] = res.consensos_usados
        # v1.4.1: quantificadores_usados segue o mesmo padrão — telemetria
        # par a par do MOVIMENTO 3, conferível contra a fração real.
        output["quantificadores_usados"] = res.quantificadores_usados
        # v1.5.0: marcadores_perspectiva e metricas_fluencia seguem o mesmo
        # padrão — telemetria persistida como campo global, ao lado da
        # narrativa que ela descreve.
        output["marcadores_perspectiva"] = res.marcadores_perspectiva
        output["metricas_fluencia"] = res.metricas_fluencia
        output["narrativa_flags"] = {
            "idioma_invalido": res.idioma_invalido,
            "escopo_suspeito": res.escopo_suspeito,
            "prevalencia_suspeita": res.prevalencia_suspeita,
            "quantificador_suspeito": res.quantificador_suspeito,
            "consenso_suspeito": res.consenso_suspeito,
            "peso_nao_ancorado": res.peso_nao_ancorado,
            "vocabulario_peso_suspeito": res.vocabulario_peso_suspeito,
            "perspectiva_nao_marcada": res.perspectiva_nao_marcada,
            "aspas_removidas": res.aspas_removidas,
            "falhou": res.falhou,
        }

        # --- [E2] passe de edição (v1.6.0) ---
        # +1 chamada LLM. O editor recebe SÓ o texto e os trechos protegidos
        # (montados em código a partir do que o narrador declarou) — nunca os
        # buckets, as reviews ou a ficha. Se a edição quebrar qualquer
        # checagem mecânica, ela é DESCARTADA e a narrativa do narrador
        # prevalece: o editor pode não melhorar, mas não pode piorar.
        #
        # `editor_ativo` decide se o editor roda. `EDITOR_ATIVO` (config.py)
        # é o default de produção — LIGADO desde a v1.8.1, ver o comentário
        # lá — e `--no-edicao` sempre vence (desliga mesmo com
        # --com-editor), para continuar existindo como "desligar
        # explicitamente" sem depender do valor do default.
        editor_ativo = (EDITOR_ATIVO or args.com_editor) and not args.no_edicao
        if editor_ativo:
            print("Editando narrativa (1 chamada LLM)...", file=sys.stderr)
            protegidos = montar_protegidos(res, output)
            ed = editar_narrativa(res, protegidos, output=output,
                                  model=args.model, provider=args.provider)
            output["narrativa_bruta"] = ed.texto_bruto   # auditoria
            output["narrativa"] = ed.texto               # texto final
            output["metricas_fluencia"] = ed.metricas_fluencia
            output["edicao_flags"] = {
                "edicao_descartada": ed.edicao_descartada,
                "motivo_descarte": ed.motivo_descarte,
                "protegidos_perdidos": ed.protegidos_perdidos,
                "numeros_alterados": ed.numeros_alterados,
                "houve_retentativa": ed.houve_retentativa,
                "falhou": ed.falhou,
                "n_protegidos": len(protegidos),
                # v1.7.3: telemetria da política de retentativa — quantas
                # chamadas foram feitas e o motivo de falha de cada uma.
                "n_tentativas": ed.n_tentativas,
                "motivos_por_tentativa": ed.motivos_por_tentativa,
                # v1.7.4: similaridade bruta×editada (telemetria de edição
                # nula) e se a capitalização residual foi corrigida.
                "similaridade": ed.similaridade,
                "capitalizacao_ajustada": ed.capitalizacao_ajustada,
                # v1.8.0 (Tarefa 3.1): telemetria da checagem de conteúdo
                # adicionado — persistida SEMPRE, aceita ou não a edição.
                "frases_sem_origem": ed.frases_sem_origem,
                "similaridade_minima_por_frase": ed.similaridade_minima_por_frase,
                # v1.8.1 (Tarefa 1, diagnóstico): registro completo de TODA
                # tentativa (aceita ou reprovada) — motivo, similaridade,
                # frases_sem_origem com similaridade máxima e o texto
                # inteiro produzido em cada uma. Ver EdicaoResult em
                # models.py para o formato exato.
                "tentativas_detalhe": ed.tentativas_detalhe,
            }
            if ed.edicao_descartada:
                print(f"⚠️  Edição descartada ({ed.motivo_descarte}) — "
                      f"mantida a narrativa do narrador.", file=sys.stderr)
        else:
            # editor DESLIGADO (v1.8.1: só via --no-edicao explícito, já que
            # o default agora é LIGADO) — mesmo formato de saída que um
            # descarte (narrativa == narrativa_bruta == texto do narrador),
            # caminho já existente e testado, só que sem gastar a chamada
            # LLM do editor. `editor_desativado` deixa o motivo explícito no
            # JSON em vez de "edicao_flags" simplesmente sumir.
            output["narrativa_bruta"] = res.texto
            output["edicao_flags"] = {"editor_desativado": True}

    path = write_json(output, args.out_dir)
    print(render_terminal(output, tom=args.tom))
    print(f"\nJSON salvo em {path}", file=sys.stderr)
    print(f"Requisições de rede nesta execução: {fetcher_net}", file=sys.stderr)


if __name__ == "__main__":
    main()
