"""Punto de entrada del MiniBrowser EDU."""

from pathlib import Path

from browser import Browser
from lector_html import LectorHTML
from lexer_html import LexerHTML
from tokenizador_html import TokenizadorHTML
from tree_builder import TreeBuilder


PROJECT_ROOT = Path(__file__).resolve().parent
RESOURCES = PROJECT_ROOT / "resources"


def load_document(html_path=RESOURCES / "index.html"):
    contenido = LectorHTML(html_path).leer()
    tokens = TokenizadorHTML(contenido).tokenizar()
    return TreeBuilder(LexerHTML(tokens).analizar()).construir()


def main():
    html_path = RESOURCES / "index.html"
    document = load_document(html_path)
    browser = Browser()
    browser.display(document, html_path)


if __name__ == "__main__":
    main()
