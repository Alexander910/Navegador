from javascript_engine import JavaScriptEngine
from lector_html import LectorHTML
from lexer_html import LexerHTML
from script_loader import ScriptLoader
from tokenizador_html import TokenizadorHTML
from tree_builder import TreeBuilder
from renderer import Renderer
from browser import Browser
import renderer as renderer_module
from dom import Element


# Los módulos externos declaran ``_init_`` en vez de ``__init__`` y Renderer
# no expone Element. Se completan aquí para no modificar esos archivos.
Browser.__init__ = Browser._init_
Renderer.__init__ = Renderer._init_
renderer_module.Element = Element



# Fases 1 a 4: cargar HTML, tokenizarlo, analizarlo y construir el único DOM.
lector = LectorHTML("resources/index.html")
contenido = lector.leer()

tokenizador = TokenizadorHTML(contenido)
tokens = tokenizador.tokenizar()

lexer = LexerHTML(tokens)
lexer_tokens = lexer.analizar()

builder = TreeBuilder(lexer_tokens)
dom = builder.construir()


print("========== DOM ANTES DE EJECUTAR JAVASCRIPT ==========")
print()
builder.imprimir(dom)


# Script Discovery: detecta referencias externas sin leer todavía su contenido.
scripts_encontrados = []
for token in lexer_tokens:
    if token["type"] != "OPEN_TAG" or token["tag"] != "script":
        continue

    src = token["attributes"].get("src")
    if src:
        scripts_encontrados.append(src)


# Script Loader: abre las fuentes JavaScript descubiertas.
script_loader = ScriptLoader("resources")
javascript_sources = []
for script in scripts_encontrados:
    javascript_source = script_loader.cargar(script)
    if javascript_source is not None:
        javascript_sources.append(javascript_source)


# QuickJS recibe el bridge al DOM Python, no una copia del árbol.
motor_js = JavaScriptEngine(dom)

print("\n========== CONSOLA JAVASCRIPT ==========")
print()
for javascript_source in javascript_sources:
    motor_js.ejecutar(javascript_source.source)


print("\n========== DOM DESPUES DE EJECUTAR JAVASCRIPT ==========")
print()
builder.imprimir(dom)

browser = Browser()
browser.display(dom)
