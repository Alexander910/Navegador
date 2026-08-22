"""Analizador sencillo de las cadenas que produce TokenizadorHTML."""

from dataclasses import dataclass, field
import re


@dataclass
class HTMLToken:
    kind: str
    name: str = ""
    attributes: dict = field(default_factory=dict)
    text: str = ""
    self_closing: bool = False


class LexerHTML:
    def __init__(self, tokens):
        self.tokens = tokens

    def analizar(self):
        lexer_tokens = []
        for token in self.tokens:
            if token.startswith("OPEN_TAG("):
                contenido = token[len("OPEN_TAG("):-1].strip()
                self_closing = contenido.endswith("/")
                if self_closing:
                    contenido = contenido[:-1].rstrip()
                partes = contenido.split(maxsplit=1)
                if not partes:
                    continue
                nombre = partes[0].lower()
                atributos = self._leer_atributos(partes[1] if len(partes) > 1 else "")
                lexer_tokens.append(HTMLToken(
                    "open", nombre, atributos, self_closing=self_closing
                ))
            elif token.startswith("CLOSE_TAG("):
                nombre = token[len("CLOSE_TAG("):-1].strip().lower()
                lexer_tokens.append(HTMLToken("close", nombre))
            elif token.startswith("TEXT("):
                texto = token[len("TEXT("):-1]
                lexer_tokens.append(HTMLToken("text", text=texto))
        return lexer_tokens

    @staticmethod
    def _leer_atributos(texto):
        """Acepta comillas simples, dobles y atributos booleanos."""
        patron = r"([^\s=/>]+)(?:\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+)))?"
        atributos = {}
        for match in re.finditer(patron, texto):
            nombre, doble, simple, sin_comillas = match.groups()
            atributos[nombre.lower()] = next(
                (valor for valor in (doble, simple, sin_comillas) if valor is not None),
                "",
            )
        return atributos
