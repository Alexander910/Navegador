"""Carga de JavaScript externo relativa al documento HTML."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JavaScriptSource:
    filename: str
    source: str


class JavaScriptLoadError(OSError):
    pass


class JavaScriptLoader:
    def __init__(self, document_path=None):
        self.document_path = Path(document_path).resolve() if document_path else None

    def load(self, filename):
        path = self._resolve(filename)
        try:
            return JavaScriptSource(str(filename), path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise JavaScriptLoadError(f"No se encontro el script JavaScript '{filename}' ({path})") from error
        except OSError as error:
            raise JavaScriptLoadError(
                f"No se pudo leer el script JavaScript '{filename}' ({path}): {error}") from error

    def load_all(self, filenames):
        return [self.load(filename) for filename in filenames]

    def _resolve(self, filename):
        candidate = Path(filename)
        if candidate.is_absolute() or self.document_path is None:
            return candidate
        return self.document_path.parent / candidate
