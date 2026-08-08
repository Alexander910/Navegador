import re

class TokenizadorHTML:
    def __init__(self, html):
        self.html = html

    def tokenizar(self):
        tokens = []

        # Divide el HTML en etiquetas y texto
        elementos = re.findall(r'<[^>]+>|[^<]+', self.html)

        for elemento in elementos:
            elemento = elemento.strip()

            if not elemento:
                continue

            # Etiqueta de cierre
            if elemento.startswith("</"):
                nombre = elemento[2:-1].strip()
                tokens.append(f"CLOSE_TAG({nombre})")

            # Etiqueta de apertura
            elif elemento.startswith("<"):
                contenido = elemento[1:-1].strip()
                tokens.append(f"OPEN_TAG({contenido})")

            # Texto
            else:
                tokens.append(f"TEXT({elemento})")

        return tokens