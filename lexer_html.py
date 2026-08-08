import re

class LexerHTML:
    def __init__(self, tokens):
        self.tokens = tokens

    def analizar(self):
        lexer_tokens = []

        for token in self.tokens:

            # Etiqueta de apertura
            if token.startswith("OPEN_TAG("):
                contenido = token[len("OPEN_TAG("):-1]

                partes = contenido.split(maxsplit=1)
                nombre = partes[0]

                atributos = {}

                if len(partes) > 1:
                    atributos_texto = partes[1]

                    # Extrae atributos tipo atributo="valor"
                    pares = re.findall(r'(\w+)="([^"]*)"', atributos_texto)

                    for clave, valor in pares:
                        atributos[clave] = valor

                lexer_tokens.append(f"OPEN_TAG({nombre}, {atributos})")

            # Etiqueta de cierre
            elif token.startswith("CLOSE_TAG("):
                nombre = token[len("CLOSE_TAG("):-1]
                lexer_tokens.append(f"CLOSE_TAG({nombre})")

            # Texto
            elif token.startswith("TEXT("):
                texto = token[len("TEXT("):-1]
                lexer_tokens.append(f'TEXT("{texto}")')

        return lexer_tokens