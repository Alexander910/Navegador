from lector_html import LectorHTML
from lexer_html import LexerHTML
from tokenizador_html import TokenizadorHTML
from tree_builder import TreeBuilder
from browser import Browser
import renderer as renderer_module
from renderer import Renderer
from dom import Element, TextNode


# Los archivos Browser, Renderer y DOM usan _init_ en lugar de __init__.
# Como no se modifican, se registra aquí el constructor que Python debe usar.
Browser.__init__ = Browser._init_
Renderer.__init__ = Renderer._init_
# En renderer.py la importación de Element quedó comentada; se proporciona
# desde aquí para no alterar ese archivo.
renderer_module.Element = Element


def adaptar_para_renderer(nodo):
    """Convierte el árbol de TreeBuilder al formato que Renderer necesita."""
    if nodo.nombre == "#text":
        texto = TextNode.__new__(TextNode)
        texto.text = nodo.texto
        texto.children = []
        return texto

    elemento = Element.__new__(Element)
    elemento.tag = nodo.nombre
    elemento.children = [adaptar_para_renderer(hijo) for hijo in nodo.hijos]
    return elemento

# Fase 1: Leer el archivo HTML
lector = LectorHTML("resources/index.html")
contenido = lector.leer()
# Al activarlo se imprieme el contenido del archivo HTML
# print(contenido)

# Fase 2: Tokenizar el contenido
tokenizador = TokenizadorHTML(contenido)
tokens = tokenizador.tokenizar()

# Fase 3
lexer = LexerHTML(tokens)
lexer_tokens = lexer.analizar()

# Fase 4
builder = TreeBuilder(lexer_tokens)
dom = builder.construir()

builder.imprimir(dom)

browser = Browser()
browser.display(adaptar_para_renderer(dom))
