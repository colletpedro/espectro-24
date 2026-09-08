"""Contrato auditável entre a obra do Letterboxd e a ficha do TMDB.

O identificador declarado pela página do Letterboxd é a fonte primária.
Exceções, quando existirem, precisam ser decisões editoriais explícitas e
versionadas; não existe nenhuma em vigor.
"""
from __future__ import annotations

from copy import deepcopy


VERSAO_CONTRATO_IDENTIDADE = 1


# Exceções são dados de produto, não fallbacks heurísticos.  Cada entrada
# conserva tanto a associação observada quanto a decisão que a substitui.
OVERRIDES_TMDB_POR_SLUG = {}


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
