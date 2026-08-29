"""
html_document_loader.py – Parte 10 del navegador: integración con el HTML Parser.

Conecta la respuesta HTTP descargada de la red con el pipeline parser HTML existente
(TokenizadorHTML -> LexerHTML -> TreeBuilder).

Valida Content-Type, decodifica el cuerpo según el charset y construye la estructura DOM (Document).
"""

from typing import Any
from http_response import HTTPResponse
from content_type import route_content_type


# ── Excepción ─────────────────────────────────────────────────────────
class HTMLDocumentLoaderError(Exception):
    """Error al cargar o decodificar el documento HTML."""


# ── Función del Pipeline Parser HTML ─────────────────────────────────
def parse_html_source(source: str) -> Any:
    """
    Parsea una cadena HTML utilizando el lexer, tokenizador y tree builder existentes.
    """
    from lexer_html import LexerHTML
    from tokenizador_html import TokenizadorHTML
    from tree_builder import TreeBuilder

    tokens = TokenizadorHTML(source).tokenizar()
    lexer_tokens = LexerHTML(tokens).analizar()
    return TreeBuilder(lexer_tokens).construir()


# ── Carga Completa del Documento HTML ─────────────────────────────────
def load_html_document(response: HTTPResponse) -> Any:
    """
    Valida la respuesta HTTP, enruta el Content-Type, decodifica los bytes
    y construye el árbol DOM del documento HTML.

    Raises:
        HTMLDocumentLoaderError: si la respuesta no es HTTPResponse, no es 2xx,
                                 el Content-Type no es HTML o hay error de charset.
    """
    if not isinstance(response, HTTPResponse):
        raise HTMLDocumentLoaderError(
            f"Se esperaba una instancia de HTTPResponse, se recibió: {type(response).__name__}"
        )

    if not (200 <= response.status <= 299):
        raise HTMLDocumentLoaderError(
            f"No se puede construir HTML a partir de una respuesta no exitosa ({response.status} {response.reason})."
        )

    content_decision = route_content_type(response)

    if content_decision.destination != "html-parser":
        raise HTMLDocumentLoaderError(
            f"Content-Type {content_decision.media_type!r} no es soportado por el HTML parser."
        )

    encoding = content_decision.charset or "utf-8"

    try:
        source = response.body.decode(encoding)
    except LookupError as err:
        raise HTMLDocumentLoaderError(
            f"Charset desconocido: {encoding!r}"
        ) from err
    except UnicodeDecodeError as err:
        raise HTMLDocumentLoaderError(
            f"Bytes incompatibles con el charset {encoding!r}: {err}"
        ) from err

    print(f"[HTML] Fuente decodificada: {len(source)} caracteres ({encoding})")

    document = parse_html_source(source)

    print("[HTML] DOM construido.")

    return document
