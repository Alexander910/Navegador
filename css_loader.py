"""
css_loader.py – Carga de hojas de estilo CSS (Local y Red).

Soporta la lectura de hojas CSS locales (desde sistema de archivos)
así como la descarga remota a través de la red (NetworkLoader).

Mantiene total compatibilidad con el CSSLoader local original.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from content_type import route_content_type
from network_loader import NetworkLoader, NetworkLoaderError
from url_resolver import resolve_url, URLResolverError


# ── Fuente CSS ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CSSSource:
    """Contenido y origen de una hoja de estilo CSS."""
    filename: str
    source: str


# ── Excepción ─────────────────────────────────────────────────────────
class CSSLoadError(OSError):
    """Error al cargar una hoja de estilo CSS (local o remota)."""


# ── Cargador CSS ──────────────────────────────────────────────────────
class CSSLoader:
    """Cargador dual de CSS (Disco local y Red HTTP/HTTPS)."""

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

    def load(self, filename: str) -> CSSSource:
        """
        Carga una hoja de estilo CSS dada su ruta local o URL remota.
        """
        if not filename or not isinstance(filename, str):
            raise CSSLoadError("El nombre de archivo u hoja CSS no puede estar vacío.")

        # 1. Determinar si es una carga por red
        if filename.startswith("http://") or filename.startswith("https://"):
            return self._load_from_network(filename)

        if self.document_url:
            try:
                target_url = resolve_url(self.document_url, filename)
            except URLResolverError as err:
                raise CSSLoadError(
                    f"No se pudo resolver la URL relativa CSS {filename!r}: {err}"
                ) from err
            return self._load_from_network(target_url)

        # 2. Carga desde archivo local
        return self._load_from_local(filename)

    def load_all(self, filenames: List[str]) -> List[CSSSource]:
        """Carga todas las hojas de estilo indicadas en la lista."""
        return [self.load(fn) for fn in filenames]

    def _load_from_network(self, url: str) -> CSSSource:
        """Descarga una hoja de estilo desde la red."""
        try:
            fetched = self.network_loader.fetch(url)
        except NetworkLoaderError as err:
            raise CSSLoadError(f"Error de red al cargar CSS '{url}': {err}") from err

        response = fetched.response
        if not (200 <= response.status <= 299):
            raise CSSLoadError(
                f"Fallo al descargar CSS '{url}': respuesta HTTP {response.status} {response.reason}"
            )

        content_decision = route_content_type(response)
        if content_decision.destination != "css-parser":
            print(f"[CSS] Advertencia: Content-Type '{content_decision.media_type}' inesperado para CSS.")

        encoding = content_decision.charset or "utf-8"
        try:
            source = response.body.decode(encoding)
        except (LookupError, UnicodeDecodeError) as err:
            raise CSSLoadError(
                f"No se pudo decodificar la hoja CSS '{url}' con charset '{encoding}': {err}"
            ) from err

        print(f"[CSS] Hoja descargada: {url}")
        return CSSSource(filename=url, source=source)

    def _load_from_local(self, filename: str) -> CSSSource:
        """Lee una hoja de estilo desde el disco local."""
        path = self._resolve_local_path(filename)
        try:
            source = path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise CSSLoadError(f"No se encontro la hoja CSS '{filename}' ({path})") from error
        except OSError as error:
            raise CSSLoadError(f"No se pudo leer la hoja CSS '{filename}' ({path}): {error}") from error
        return CSSSource(filename=str(filename), source=source)

    def _resolve_local_path(self, filename: str) -> Path:
        candidate = Path(filename)
        if candidate.is_absolute():
            return candidate
        if self.document_path:
            return self.document_path.parent / candidate
        if self.resources_path:
            return self.resources_path / candidate
        return candidate
