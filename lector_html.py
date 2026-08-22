"""Lectura explicita del documento HTML de MiniBrowser EDU."""

from pathlib import Path


class LectorHTML:
    def __init__(self, ruta):
        self.ruta = ruta

    def leer(self):
        try:
            return Path(self.ruta).read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise FileNotFoundError(f"No se encontro el archivo HTML: {self.ruta}") from error
        except OSError as error:
            raise OSError(f"No se pudo leer el archivo HTML '{self.ruta}': {error}") from error
