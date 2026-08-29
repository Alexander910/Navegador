"""Punto de entrada del MiniBrowser EDU."""

import sys
from pathlib import Path

from browser import Browser
from lector_html import LectorHTML
from lexer_html import LexerHTML
from tokenizador_html import TokenizadorHTML
from tree_builder import TreeBuilder
from network_loader import NetworkLoader
from html_document_loader import load_html_document


PROJECT_ROOT = Path(__file__).resolve().parent
RESOURCES = PROJECT_ROOT / "resources"


def load_document(html_path=RESOURCES / "index.html"):
    contenido = LectorHTML(html_path).leer()
    tokens = TokenizadorHTML(contenido).tokenizar()
    return TreeBuilder(LexerHTML(tokens).analizar()).construir()


def load_remote_document(url: str, loader=None):
    """
    Descarga una página HTML remota a través de la red (NetworkLoader)
    y construye su árbol DOM.
    """
    loader = loader or NetworkLoader()
    fetched = loader.fetch(url)
    document = load_html_document(fetched.response)
    return document, fetched.url


def main():
    browser = Browser()

    if len(sys.argv) > 1:
        target = sys.argv[1].strip()
        if target.startswith("http://") or target.startswith("https://"):
            document, final_url = load_remote_document(target)
            browser.display(document, document_url=final_url)
            return

        html_path = Path(target)
        document = load_document(html_path)
        browser.display(document, document_path=html_path)
        return

    html_path = RESOURCES / "index.html"
    document = load_document(html_path)
    browser.display(document, document_path=html_path)


if __name__ == "__main__":
    main()
