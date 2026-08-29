"""
url_resolver.py – Parte 11 del navegador: resolución de URLs relativas.

Resuelve referencias relativas a URLs absolutas a partir de una URL base dada,
utilizando urllib.parse.urljoin.

Garantías y controles:
  - Exige una URL base absoluta válida (verificada con url_parser).
  - Admite rutas relativas (styles/main.css), absolutas (/static/app.js),
    protocol-relative (//cdn.example.org/app.js) o absolutas completas.
  - Elimina fragmentos (#...).
  - Conserva cadenas de consulta (?query=...).
  - Valida el resultado final con url_parser (solo esquemas http y https).
  - Rechaza referencias vacías o con saltos de línea.
"""

from typing import List
from urllib.parse import urljoin
from url_parser import parse_url, URLError


# ── Excepción ─────────────────────────────────────────────────────────
class URLResolverError(Exception):
    """Error al resolver una URL relativa."""


# ── Función Principal de Resolución ──────────────────────────────────
def resolve_url(base_url: str, relative_url: str) -> str:
    """
    Resuelve *relative_url* respecto a *base_url*.

    Raises:
        URLResolverError: si la URL base o la relativa son inválidas o la resultante no es http/https.
    """
    # 1. Validar URL base
    if not base_url or not isinstance(base_url, str):
        raise URLResolverError("La URL base no puede estar vacía.")

    try:
        parse_url(base_url)
    except URLError as err:
        raise URLResolverError(
            f"La URL base dada no es válida: {base_url!r}: {err}"
        ) from err

    # 2. Validar URL relativa
    if not relative_url or not isinstance(relative_url, str):
        raise URLResolverError("La URL relativa no puede estar vacía.")

    rel_clean = relative_url.strip()
    if not rel_clean:
        raise URLResolverError("La URL relativa no puede ser solo espacios en blanco.")

    if "\r" in rel_clean or "\n" in rel_clean:
        raise URLResolverError("Inyección CRLF detectada en la URL relativa.")

    # 3. Resolver la URL usando urljoin
    resolved = urljoin(base_url, rel_clean)

    # 4. Eliminar fragmentos (#...)
    if "#" in resolved:
        resolved, _ = resolved.split("#", 1)

    # 5. Validar la URL resuelta final
    try:
        parse_url(resolved)
    except URLError as err:
        raise URLResolverError(
            f"La URL resuelta {resolved!r} es inválida o no utiliza un esquema soportado: {err}"
        ) from err

    print(f"[URL] {rel_clean} -> {resolved}")

    return resolved


# ── Clase Helper URLResolver ──────────────────────────────────────────
class URLResolver:
    """Helper orientado a objetos para resolver una o múltiples URLs."""

    def resolve(self, base_url: str, relative_url: str) -> str:
        """Resuelve una sola URL relativa."""
        return resolve_url(base_url, relative_url)

    def resolve_all(self, base_url: str, relative_urls: List[str]) -> List[str]:
        """
        Resuelve una lista de URLs relativas respecto a *base_url*.
        """
        resolved_list = []
        for rel in relative_urls:
            try:
                resolved_list.append(resolve_url(base_url, rel))
            except URLResolverError:
                # Omitir o registrar URLs relativas inválidas en listas masivas
                continue
        return resolved_list
