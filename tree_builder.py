from dom import Document, Element, TextNode


class TreeBuilder:
    """Construye un DOM jerárquico a partir de tokens analizados."""

    def __init__(self, lexer_tokens):
        self.lexer_tokens = lexer_tokens

    def construir(self):
        documento = Document()
        pila = [documento]

        for token in self.lexer_tokens:
            if token["type"] == "OPEN_TAG":
                nodo = Element(token["tag"], token["attributes"])
                pila[-1].add_child(nodo)
                pila.append(nodo)

            elif token["type"] == "TEXT":
                pila[-1].add_child(TextNode(token["text"]))

            elif token["type"] == "CLOSE_TAG":
                if len(pila) == 1 or pila[-1].tag != token["tag"]:
                    raise ValueError(f"Etiqueta de cierre inesperada: </{token['tag']}>")
                pila.pop()

        if len(pila) != 1:
            raise ValueError(f"Etiqueta sin cerrar: <{pila[-1].tag}>")

        return documento

    def imprimir(self, nodo, nivel=0):
        sangria = "    " * nivel
        if isinstance(nodo, Document):
            print(f"{sangria}Document")
        elif isinstance(nodo, TextNode):
            print(f'{sangria}TEXT("{nodo.text}")')
        else:
            print(
                f"{sangria}Element tag={nodo.tag} "
                f"attributes={nodo.attributes}"
            )

        for hijo in nodo.children:
            self.imprimir(hijo, nivel + 1)
