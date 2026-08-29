"""
url_parser.py – Parte 1 del navegador: análisis de URL.

Extrae scheme, host, port, path y query de una URL HTTP/HTTPS.
Asigna puertos por defecto (80 para HTTP, 443 para HTTPS).
Construye el request_target que se envía al servidor.
Descarta fragmentos (#...) porque no se transmiten al servidor.
Rechaza esquemas no admitidos, hosts ausentes y puertos inválidos.
No realiza DNS ni abre conexiones.
"""

from dataclasses import dataclass
from typing import Optional


# ── Esquemas admitidos y puertos por defecto ──────────────────────────
SUPPORTED_SCHEMES = {"http", "https"}
DEFAULT_PORTS = {"http": 80, "https": 443}


# ── Resultado del análisis ────────────────────────────────────────────
@dataclass(frozen=True)
class ParsedURL:
    """Resultado inmutable del análisis de una URL."""
    scheme: str
    host: str
    port: int
    path: str
    query: Optional[str]

    @property
    def request_target(self) -> str:
        """Devuelve path?query o solo path si no hay query."""
        if self.query:
            return f"{self.path}?{self.query}"
        return self.path


# ── Excepciones ───────────────────────────────────────────────────────
class URLError(Exception):
    """Error genérico de análisis de URL."""


class UnsupportedSchemeError(URLError):
    """El esquema no es HTTP ni HTTPS."""


class MissingHostError(URLError):
    """Falta el host en la URL."""


class InvalidPortError(URLError):
    """El puerto no es un entero válido en el rango 1-65535."""


# ── Función principal ─────────────────────────────────────────────────
def parse_url(raw_url: str) -> ParsedURL:
    """
    Analiza *raw_url* y devuelve un objeto ``ParsedURL``.

    Ejemplo::

        >>> url = parse_url("https://example.com:443/cursos/index.html?grupo=A")
        >>> url.scheme
        'https'
        >>> url.host
        'example.com'
        >>> url.port
        443
        >>> url.request_target
        '/cursos/index.html?grupo=A'

    Raises:
        UnsupportedSchemeError: si el esquema no es http o https.
        MissingHostError: si falta el host.
        InvalidPortError: si el puerto no es válido.
    """
    # 1. Extraer scheme
    if "://" not in raw_url:
        raise UnsupportedSchemeError(
            f"URL sin esquema válido: {raw_url!r}"
        )

    scheme, rest = raw_url.split("://", 1)
    scheme = scheme.lower()

    if scheme not in SUPPORTED_SCHEMES:
        raise UnsupportedSchemeError(
            f"Esquema no admitido: {scheme!r}. "
            f"Soportados: {', '.join(sorted(SUPPORTED_SCHEMES))}"
        )

    # 2. Descartar fragmento (#...)
    if "#" in rest:
        rest, _ = rest.split("#", 1)

    # 3. Separar query (?...)
    query: Optional[str] = None
    if "?" in rest:
        rest, query = rest.split("?", 1)
        if not query:          # "??" o "?" al final → sin query real
            query = None

    # 4. Separar authority de path
    if "/" in rest:
        authority, path = rest.split("/", 1)
        path = "/" + path
    else:
        authority = rest
        path = "/"

    # 5. Extraer host y port del authority
    if ":" in authority:
        host, port_str = authority.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            raise InvalidPortError(
                f"Puerto no numérico: {port_str!r}"
            )
        if not (1 <= port <= 65535):
            raise InvalidPortError(
                f"Puerto fuera de rango (1-65535): {port}"
            )
    else:
        host = authority
        port = DEFAULT_PORTS[scheme]

    # 6. Validar host
    host = host.strip()
    if not host:
        raise MissingHostError("El host está vacío.")

    return ParsedURL(
        scheme=scheme,
        host=host,
        port=port,
        path=path,
        query=query,
    )
