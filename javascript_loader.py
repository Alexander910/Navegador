"""
javascript_loader.py – Carga de scripts JavaScript (Local y Red).

Soporta la lectura de scripts JavaScript locales (desde el sistema de archivos)
así como la descarga remota a través de la red (NetworkLoader).

Mantiene total compatibilidad con el JavaScriptLoader local original.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from content_type import route_content_type
from network_loader import NetworkLoader, NetworkLoaderError
from url_resolver import resolve_url, URLResolverError


# ── Fuente JavaScript ─────────────────────────────────────────────────
@dataclass(frozen=True)
class JavaScriptSource:
    """Contenido y origen de un script JavaScript."""
    filename: str
    source: str


# ── Excepción ─────────────────────────────────────────────────────────
class JavaScriptLoadError(OSError):
    """Error al cargar un script JavaScript (local o remoto)."""


# ── Cargador JavaScript ───────────────────────────────────────────────
class JavaScriptLoader:
    """Cargador dual de JavaScript (Disco local y Red HTTP/HTTPS)."""

    def __init__(
        self,
        document_path: Optional[str] = None,
        resources_path: Optional[str] = None,
        document_url: Optional[str] = None,
        network_loader: Optional[NetworkLoader] = None,
    ) -> None:
        self.document_path = Path(document_path).resolve() if document_path else None
        self.resources_path = Path(resources_path).resolve() if resources_path else None
        self.document_url = document_url
        self.network_loader = network_loader or NetworkLoader()

    def load(self, filename: str) -> JavaScriptSource:
        """
        Carga un script JavaScript dada su ruta local o URL remota.
        """
        if not filename or not isinstance(filename, str):
            raise JavaScriptLoadError("El nombre de archivo o script no puede estar vacío.")

        # 1. Determinar si es una carga por red
        if filename.startswith("http://") or filename.startswith("https://"):
            return self._load_from_network(filename)

        if self.document_url:
            try:
                target_url = resolve_url(self.document_url, filename)
            except URLResolverError as err:
                raise JavaScriptLoadError(
                    f"No se pudo resolver la URL relativa de script {filename!r}: {err}"
                ) from err
            return self._load_from_network(target_url)

        # 2. Carga desde archivo local
        return self._load_from_local(filename)

    def load_all(self, filenames: List[str]) -> List[JavaScriptSource]:
        """
        Carga todos los scripts indicados conservando estrictamente el orden.
        """
        return [self.load(fn) for fn in filenames]

    def _load_from_network(self, url: str) -> JavaScriptSource:
        """Descarga un script JavaScript desde la red."""
        try:
            fetched = self.network_loader.fetch(url)
        except NetworkLoaderError as err:
            raise JavaScriptLoadError(f"Error de red al cargar el script '{url}': {err}") from err

        response = fetched.response
        if not (200 <= response.status <= 299):
            raise JavaScriptLoadError(
                f"Fallo al descargar el script '{url}': respuesta HTTP {response.status} {response.reason}"
            )

        content_decision = route_content_type(response)
        if content_decision.destination != "quickjs":
            raise JavaScriptLoadError(
                f"Content-Type no permitido para JavaScript en '{url}': '{content_decision.media_type}'"
            )

        encoding = content_decision.charset or "utf-8"
        try:
            source = response.body.decode(encoding)
        except (LookupError, UnicodeDecodeError) as err:
            raise JavaScriptLoadError(
                f"No se pudo decodificar el script JavaScript '{url}' con charset '{encoding}': {err}"
            ) from err

        print(f"[JavaScript] Script descargado: {url}")
        return JavaScriptSource(filename=url, source=source)

    def _load_from_local(self, filename: str) -> JavaScriptSource:
        """Lee un script JavaScript desde el disco local."""
        path = self._resolve_local_path(filename)
        try:
            source = path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise JavaScriptLoadError(f"No se encontro el script JavaScript '{filename}' ({path})") from error
        except OSError as error:
            raise JavaScriptLoadError(
                f"No se pudo leer el script JavaScript '{filename}' ({path}): {error}"
            ) from error

        return JavaScriptSource(filename=str(filename), source=source)

    def _resolve_local_path(self, filename: str) -> Path:
        candidate = Path(filename)
        if candidate.is_absolute():
            return candidate
        if self.document_path:
            return self.document_path.parent / candidate
        if self.resources_path:
            return self.resources_path / candidate
        return candidate
