"""
http_request.py – Parte 5 del navegador: construcción de peticiones HTTP/1.1.

Construye manualmente solicitudes HTTP GET sin librerías externas.
Asegura el formato estricto RFC 7230 / RFC 9112 con terminadores \\r\\n.
Previene inyecciones CRLF y maneja puertos no predeterminados en la cabecera Host.
"""

from dataclasses import dataclass, field
from typing import Dict

# ── Puertos por defecto para comparación ─────────────────────────────
DEFAULT_PORTS = {"http": 80, "https": 443}


# ── Excepciones ───────────────────────────────────────────────────────
class HTTPRequestError(Exception):
    """Error en la construcción o validación de la petición HTTP."""


class CRLFInjectionError(HTTPRequestError):
    """Se detectó una inyección de caracteres CRLF (\\r o \\n)."""


# ── Clase de Solicitud HTTP ───────────────────────────────────────────
@dataclass
class HTTPRequest:
    """Representa una solicitud HTTP/1.1 construida."""
    method: str
    request_target: str
    host: str
    port: int
    scheme: str
    headers: Dict[str, str] = field(default_factory=dict)

    def to_string(self) -> str:
        """Devuelve la petición en formato texto con terminadores \\r\\n."""
        lines = [f"{self.method} {self.request_target} HTTP/1.1"]
        for key, value in self.headers.items():
            lines.append(f"{key}: {value}")
        return "\r\n".join(lines) + "\r\n\r\n"

    def to_bytes(self) -> bytes:
        """Convierte la petición a bytes codificados en ASCII."""
        return self.to_string().encode("ascii")


# ── Construcción de Peticiones GET ───────────────────────────────────
def build_get_request(
    host: str,
    request_target: str = "/",
    port: int = 80,
    scheme: str = "http",
    user_agent: str = "MiniBrowser-EDU/1.0",
    accept: str = "text/html,*/*",
) -> HTTPRequest:
    """
    Construye una solicitud HTTP GET validada.

    Raises:
        CRLFInjectionError: si *host* o *request_target* contienen \\r o \\n.
        HTTPRequestError: si los datos del puerto, esquema o blanco son inválidos.
    """
    scheme = scheme.lower()
    if scheme not in ("http", "https"):
        raise HTTPRequestError(f"Esquema no admitido: {scheme!r}")

    if not host or not host.strip():
        raise HTTPRequestError("El host no puede estar vacío.")

    host = host.strip()

    if not isinstance(port, int) or not (1 <= port <= 65535):
        raise HTTPRequestError(f"Puerto inválido: {port!r}")

    if not request_target or not request_target.startswith("/"):
        raise HTTPRequestError(
            f"El recurso objetivo (request_target) debe comenzar con '/': {request_target!r}"
        )

    # Protección contra inyección CRLF
    for param_name, param_val in [("host", host), ("request_target", request_target)]:
        if "\r" in param_val or "\n" in param_val:
            raise CRLFInjectionError(
                f"Inyección CRLF detectada en el parámetro {param_name}: {param_val!r}"
            )

    # Formatear Host header: omitir puerto si es el predeterminado del esquema
    default_port = DEFAULT_PORTS.get(scheme)
    if port == default_port:
        host_header_value = host
    else:
        host_header_value = f"{host}:{port}"

    headers = {
        "Host": host_header_value,
        "User-Agent": user_agent,
        "Accept": accept,
        "Connection": close_header() if callable(close_header := lambda: "close") else "close",
    }

    return HTTPRequest(
        method="GET",
        request_target=request_target,
        host=host,
        port=port,
        scheme=scheme,
        headers=headers,
    )


# ── Visualización de la Petición ──────────────────────────────────────
def print_http_request(request: HTTPRequest) -> None:
    """Imprime por consola la petición HTTP formateada."""
    print("========== HTTP REQUEST ==========")
    lines = [f"{request.method} {request.request_target} HTTP/1.1"]
    for key, value in request.headers.items():
        lines.append(f"{key}: {value}")
    print("\n".join(lines))
    print("==================================")
