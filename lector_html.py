class LectorHTML:
    def __init__(self, ruta):
        self.ruta = ruta

    def leer(self):
        try:
            with open(self.ruta, "r", encoding="utf-8") as archivo:
                return archivo.read()
        except FileNotFoundError:
            return "Error: El archivo no existe."
        except Exception as e:
            return f"Ocurrió un error: {e}"