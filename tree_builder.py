"""Construye el DOM definitivo a partir de HTMLToken."""

from dom import Document, Element, TextNode
from lexer_html import HTMLToken


VOID_ELEMENTS = {"br", "img", "input", "meta", "link", "hr"}


class TreeBuilder:
    def __init__(self, lexer_tokens):
        self.lexer_tokens = lexer_tokens

    def construir(self):
        documento = Document()
        pila = [documento]

        for token in self.lexer_tokens:
            if not isinstance(token, HTMLToken):
                token = self._token_legacy(token)
            if token is None:
                continue

            if token.kind == "open":
                nodo = Element(token.name, token.attributes)
                pila[-1].append_child(nodo)
                if not token.self_closing and token.name not in VOID_ELEMENTS:
                    pila.append(nodo)
            elif token.kind == "text":
                if token.text:
                    pila[-1].append_child(TextNode(token.text))
            elif token.kind == "close":
                self._cerrar_etiqueta(pila, token.name)

        return documento

    @staticmethod
    def _cerrar_etiqueta(pila, nombre):
        """Cierra solo una etiqueta que realmente siga abierta."""
        for indice in range(len(pila) - 1, 0, -1):
            nodo = pila[indice]
            if isinstance(nodo, Element) and nodo.tag == nombre:
                del pila[indice:]
                return

    @staticmethod
    def _token_legacy(token):
        if token.startswith("CLOSE_TAG("):
            return HTMLToken("close", token[len("CLOSE_TAG("):-1].strip().lower())
        if token.startswith("TEXT("):
            return HTMLToken("text", text=token[len("TEXT("):-1].strip('"'))
        if token.startswith("OPEN_TAG("):
            contenido = token[len("OPEN_TAG("):-1]
            return HTMLToken("open", contenido.split(",", 1)[0].strip().lower())
        return None

    def imprimir(self, nodo, nivel=0):
        if isinstance(nodo, TextNode):
            print("    " * nivel + nodo.text)
            return
        nombre = "Document" if isinstance(nodo, Document) else nodo.tag
        print("    " * nivel + nombre)
        for hijo in nodo.children:
            self.imprimir(hijo, nivel + 1)
