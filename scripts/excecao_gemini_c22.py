"""A lista e a marca da exceção C22 vivem em `espectro24.excecao_c22` (o CLI
de publicação, dentro do pacote, também as usa). Este módulo só as reexporta
para os scripts."""
from espectro24.excecao_c22 import (  # noqa: F401
    CAMADA,
    EXCECAO,
    MODELO,
    SLUGS,
    ForaDaExcecao,
    exigir_no_escopo,
)
