"""Contrato auditável entre a obra do Letterboxd e a ficha do TMDB.

O identificador declarado pela página do Letterboxd é a fonte primária.  A
única exceção corrente é explícita e versionada abaixo: o próprio Letterboxd
associa ``obsession-2026`` a um curta, embora a página/reviews estejam sendo
usadas para o longa de Curry Barker.
"""
from __future__ import annotations

from copy import deepcopy


VERSAO_CONTRATO_IDENTIDADE = 1


# Exceções são dados de produto, não fallbacks heurísticos.  Cada entrada
# conserva tanto a associação observada quanto a decisão que a substitui.
OVERRIDES_TMDB_POR_SLUG = {
    "obsession-2026": {
        "tmdb_id": 1339713,
        "tmdb_id_letterboxd_observado": 1615708,
        "motivo": (
            "A obra pretendida pelo catálogo é o longa de Curry Barker; "
            "a página do Letterboxd aponta para um curta homônimo e contém "
            "reviews confundidas com o longa."
        ),
        "decidido_em": "2026-09-08",
        "decidido_por": "dono_do_projeto",
    },
}


def override_tmdb_para(slug: str) -> dict | None:
    """Cópia da associação manual auditável de ``slug``, se existir."""
    item = OVERRIDES_TMDB_POR_SLUG.get(slug)
    return deepcopy(item) if item else None


def tmdb_id_escolhido(identidade: dict) -> tuple[int | None, str, dict | None]:
    """Resolve o ID efetivo sem esconder uma exceção em heurística."""
    slug = identidade.get("slug") or ""
    manual = override_tmdb_para(slug)
    observado = identidade.get("tmdb_id_letterboxd")
    if manual:
        if observado == manual["tmdb_id"]:
            # O Letterboxd foi corrigido; a exceção deixou de ser necessária.
            return observado, "letterboxd", None
        if observado != manual["tmdb_id_letterboxd_observado"]:
            # O mundo mudou para um terceiro estado. Não aplicar uma decisão
            # antiga a uma associação que o dono nunca avaliou.
            return None, "override_manual_desatualizado", manual
        return manual["tmdb_id"], "override_manual", manual
    return observado, "letterboxd", None
