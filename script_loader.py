class JavaScriptSource:
    def __init__(self, filename, source):
        self.filename = filename
        self.source = source

    def __str__(self):
        return (
            "JavaScriptSource\n"
            f'  filename = "{self.filename}"\n'
            f"  source = {repr(self.source)}"
        )


class ScriptLoader:
    def __init__(self, ruta_base="resources"):
        self.ruta_base = ruta_base

    def cargar(self, filename):
        ruta = f"{self.ruta_base}/{filename}"

        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                contenido_js = archivo.read()

            return JavaScriptSource(
                filename=filename,
                source=contenido_js,
            )

        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {ruta}")
            return None

        except Exception as e:
            print(f"Error al cargar JavaScript: {e}")
            return None
