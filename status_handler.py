"""
status_handler.py – Parte 8 del navegador: manejador de códigos de estado HTTP.

Clasifica las respuestas HTTP en función de su código de estado (2xx, 3xx, 4xx, 5xx)
y determina la acción a seguir por parte del navegador (use-resource, redirect,
permanent-redirect, error).

Maneja redirecciones verificando la cabecera Location. Si falta Location en una
redirección 3xx, se clasifica como error.
"""

from dataclasses import dataclass
from typing import Optional
from http_response import HTTPResponse


# ── Decisiones de Estado ───────────────────────────────────────────────
@dataclass(frozen=True)
class StatusDecision:
    """Representa la decisión tomada tras evaluar el código de estado HTTP."""
    action: str  # "use-resource", "redirect", "permanent-redirect", "error"
    status_code: int
    reason: str
    location: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Devuelve True si la petición fue exitosa y se debe procesar el recurso."""
        return self.action == "use-resource"

    @property
    def is_redirect(self) -> bool:
        """Devuelve True si se debe seguir una redirección (301, 302, etc.)."""
        return self.action in ("redirect", "permanent-redirect")

    @property
    def is_error(self) -> bool:
        """Devuelve True si ocurrió un error de cliente (4xx) o de servidor (5xx)."""
        return self.action == "error"


# ── Función Principal de Evaluación ─────────────────────────────────
def handle_http_status(response: HTTPResponse) -> StatusDecision:
    """
    Evalúa *response* y devuelve un ``StatusDecision``.

    Muestra por consola los mensajes informativos exigidos por las especificaciones.
    """
    code = response.status
    reason = response.reason

    print(f"[HTTP] {code} {reason}".strip())

    # 1. Familia 2xx - Éxito
    if 200 <= code <= 299:
        print("Recurso disponible.")
        return StatusDecision(
            action="use-resource",
            status_code=code,
            reason=reason,
        )

    # 2. Familia 3xx - Redirecciones
    elif 300 <= code <= 399:
        location = response.headers.get("Location") or response.headers.get("location")
        if not location or not location.strip():
            print(f"[HTTP] Redirección {code} sin cabecera Location válida. Se trata como error.")
            return StatusDecision(
                action="error",
                status_code=code,
                reason=reason,
            )

        location = location.strip()
        print(f"[HTTP] Location: {location}")

        if code in (301, 308):
            print("Redireccion permanente.")
            action = "permanent-redirect"
        else:
            print("Redireccion temporal.")
            action = "redirect"

        return StatusDecision(
            action=action,
            status_code=code,
            reason=reason,
            location=location,
        )

    # 3. Familia 4xx - Errores de cliente / Recurso no encontrado
    elif 400 <= code <= 499:
        if code == 404:
            print("No fue posible cargar el recurso.")
        else:
            print(f"Error del cliente ({code} {reason}).")

        return StatusDecision(
            action="error",
            status_code=code,
            reason=reason,
        )

    # 4. Familia 5xx - Errores del servidor
    elif 500 <= code <= 599:
        print("Error del servidor.")
        return StatusDecision(
            action="error",
            status_code=code,
            reason=reason,
        )

    # 5. Códigos no estándar o fuera de rango
    else:
        print(f"Código de estado desconocido: {code}.")
        return StatusDecision(
            action="error",
            status_code=code,
            reason=reason,
        )
