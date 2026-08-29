"""
content_type.py – Parte 9/13 del navegador: enrutador según Content-Type.

Inspecciona la cabecera Content-Type de una respuesta HTTP y determina
el componente receptor adecuado (html-parser, css-parser, quickjs, unsupported).

Extrae el tipo de medio (media_type) y el juego de caracteres (charset).
No decodifica el cuerpo ni ejecuta los componentes receptores.
"""

from dataclasses import dataclass
from typing import Optional, Dict
from http_response import HTTPResponse

# ── Tabla de Enrutamiento MIME ─────────────────────────────────────────
CONTENT_TYPE_ROUTES: Dict[str, str] = {
    "text/html": "html-parser",
    "application/xhtml+xml": "html-parser",
    "text/css": "css-parser",
    "application/javascript": "quickjs",
    "application/x-javascript": "quickjs",
    "text/javascript": "quickjs",
    "application/ecmascript": "quickjs",
    "text/ecmascript": "quickjs",
}


# ── Decisión de Content-Type ───────────────────────────────────────────
@dataclass(frozen=True)
class ContentTypeDecision:
    """Resultado del análisis y enrutamiento del Content-Type."""
    raw_header: str
    media_type: str
    charset: Optional[str]
    destination: str

    @property
    def is_supported(self) -> bool:
        """Devuelve True si el destino no es 'unsupported'."""
        return self.destination != "unsupported"


# ── Función Principal de Enrutamiento ─────────────────────────────────
def route_content_type(response: HTTPResponse) -> ContentTypeDecision:
    """
    Parsea la cabecera Content-Type de *response* y devuelve un ``ContentTypeDecision``.
    """
    raw_header = response.headers.get("Content-Type") or response.headers.get("content-type") or ""
    raw_header_clean = raw_header.strip()

    if not raw_header_clean:
        print("[Content-Type] Ausente -> unsupported")
        return ContentTypeDecision(
            raw_header="",
            media_type="",
            charset=None,
            destination="unsupported",
        )

    # Separar media_type de los parámetros (ej. text/html; charset=utf-8)
    parts = raw_header_clean.split(";")
    media_type = parts[0].strip().lower()

    charset: Optional[str] = None
    for param in parts[1:]:
        param = param.strip()
        if "=" in param:
            k, v = param.split("=", 1)
            if k.strip().lower() == "charset":
                charset = v.strip().strip("\"'").lower()

    destination = CONTENT_TYPE_ROUTES.get(media_type, "unsupported")

    print(f"[Content-Type] {media_type} -> {destination}")

    return ContentTypeDecision(
        raw_header=raw_header_clean,
        media_type=media_type,
        charset=charset,
        destination=destination,
    )
