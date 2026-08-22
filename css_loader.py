"""Fase 2: lectura de CSS; no interpreta las reglas."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CSSSource:
    filename: str
    source: str


class CSSLoadError(OSError):
    """Error de una hoja declarada por el documento."""


class CSSLoader:
    def __init__(self, document_path=None, resources_path=None):
        self.document_path = Path(document_path).resolve() if document_path else None
        self.resources_path = Path(resources_path).resolve() if resources_path else None

    def load(self, filename):
        path = self._resolve(filename)
        try:
            source = path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise CSSLoadError(f"No se encontro la hoja CSS '{filename}' ({path})") from error
        except OSError as error:
            raise CSSLoadError(f"No se pudo leer la hoja CSS '{filename}' ({path}): {error}") from error
        return CSSSource(filename=str(filename), source=source)

    def load_all(self, filenames):
        return [self.load(filename) for filename in filenames]

    def _resolve(self, filename):
        candidate = Path(filename)
        if candidate.is_absolute():
            return candidate
        if self.document_path:
            return self.document_path.parent / candidate
        if self.resources_path:
            return self.resources_path / candidate
        return candidate
