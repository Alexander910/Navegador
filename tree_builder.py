import re

class NodoDOM:
    def __init__(self, nombre, texto=None):
        self.nombre = nombre
        self.texto = texto
        self.hijos = []

    def agregar_hijo(self, hijo):
        self.hijos.append(hijo)


class TreeBuilder:
    def __init__(self, lexer_tokens):
        self.lexer_tokens = lexer_tokens

    def construir(self):

        documento = NodoDOM("Document")
        pila = [documento]

        for token in self.lexer_tokens:

            # OPEN_TAG(nombre, atributos)
            if token.startswith("OPEN_TAG("):

                contenido = token[len("OPEN_TAG("):-1]

                nombre = contenido.split(",", 1)[0].strip()

                nodo = NodoDOM(nombre)

                pila[-1].agregar_hijo(nodo)

                pila.append(nodo)

            # TEXT(...)
            elif token.startswith("TEXT("):

                texto = token[len("TEXT("):-1].strip('"')

                nodo_texto = NodoDOM("#text", texto)

                pila[-1].agregar_hijo(nodo_texto)

            # CLOSE_TAG(...)
            elif token.startswith("CLOSE_TAG("):

                pila.pop()

        return documento

    def imprimir(self, nodo, nivel=0):

        print("    " * nivel + nodo.nombre)

        for hijo in nodo.hijos:

            if hijo.nombre == "#text":
                print("    " * (nivel + 1) + hijo.texto)
            else:
                self.imprimir(hijo, nivel + 1)