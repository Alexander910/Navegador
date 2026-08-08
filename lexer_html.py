import re


class LexerHTML:
    """Convierte tokens crudos en tokens con etiqueta y atributos."""

    ATTRIBUTE_PATTERN = re.compile(
        r'''([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?'''
    )

    def __init__(self, tokens):
        self.tokens = tokens

    def analizar(self):
        lexer_tokens = []

        for token in self.tokens:
            if token.startswith("OPEN_TAG("):
                contenido = token[len("OPEN_TAG("):-1].strip()
                partes = contenido.split(maxsplit=1)
                tag = partes[0].rstrip("/").lower()
                texto_atributos = partes[1] if len(partes) > 1 else ""
                lexer_tokens.append(
                    {
                        "type": "OPEN_TAG",
                        "tag": tag,
                        "attributes": self._extraer_atributos(texto_atributos),
                    }
                )

            elif token.startswith("CLOSE_TAG("):
                tag = token[len("CLOSE_TAG("):-1].strip().lower()
                lexer_tokens.append({"type": "CLOSE_TAG", "tag": tag})

            elif token.startswith("TEXT("):
                texto = token[len("TEXT("):-1]
                lexer_tokens.append({"type": "TEXT", "text": texto})

        return lexer_tokens

    def _extraer_atributos(self, texto):
        atributos = {}
        for coincidencia in self.ATTRIBUTE_PATTERN.finditer(texto.rstrip("/ ")):
            nombre, doble, simple, sin_comillas = coincidencia.groups()
            valor = next(
                (valor for valor in (doble, simple, sin_comillas) if valor is not None),
                "",
            )
            atributos[nombre.lower()] = valor
        return atributos
