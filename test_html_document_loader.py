"""
test_html_document_loader.py – Pruebas unitarias para html_document_loader.py.

Ejecutar:
    python -m unittest -v test_html_document_loader
"""

import unittest
from io import StringIO
from unittest.mock import patch
from http_response import HTTPResponse, CaseInsensitiveDict
from html_document_loader import (
    load_html_document,
    parse_html_source,
    HTMLDocumentLoaderError,
)


class TestHTMLDocumentLoader(unittest.TestCase):
    """Pruebas del cargador de documentos HTML."""

    # ── 1. Carga exitosa de HTML en UTF-8 ─────────────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_load_html_utf8_success(self, mock_stdout):
        headers = CaseInsensitiveDict({"Content-Type": "text/html; charset=utf-8"})
        html_str = "<html><body><h1>Hola Mundo</h1></body></html>"
        raw_body = html_str.encode("utf-8")
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, raw_body)

        doc = load_html_document(resp)
        self.assertIsNotNone(doc)

        output = mock_stdout.getvalue()
        self.assertIn("[Content-Type] text/html -> html-parser", output)
        self.assertIn("[HTML] Fuente decodificada: 45 caracteres (utf-8)", output)
        self.assertIn("[HTML] DOM construido.", output)

    # ── 2. Carga exitosa en ISO-8859-1 ────────────────────────────
    def test_load_html_iso_8859_1_success(self):
        headers = CaseInsensitiveDict({"Content-Type": "text/html; charset=ISO-8859-1"})
        html_str = "<html><body><p>Café y Canción</p></body></html>"
        raw_body = html_str.encode("iso-8859-1")
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, raw_body)

        doc = load_html_document(resp)
        self.assertIsNotNone(doc)

    # ── 3. Equivalencia Disco vs Red ──────────────────────────────
    def test_disk_vs_network_equivalence(self):
        def dom_equal(node1, node2):
            if type(node1) != type(node2):
                return False
            if hasattr(node1, "tag") and node1.tag != node2.tag:
                return False
            if hasattr(node1, "attributes") and node1.attributes != node2.attributes:
                return False
            if hasattr(node1, "text") and node1.text != node2.text:
                return False
            if len(node1.children) != len(node2.children):
                return False
            return all(dom_equal(c1, c2) for c1, c2 in zip(node1.children, node2.children))

        html_text = "<div><h1>Test</h1><p>Parrafo</p></div>"
        disk_dom = parse_html_source(html_text)

        headers = CaseInsensitiveDict({"Content-Type": "text/html"})
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, html_text.encode("utf-8"))
        network_dom = load_html_document(resp)

        self.assertTrue(dom_equal(disk_dom, network_dom))

    # ── 4. Rechazo de tipo no HTTPResponse ───────────────────────
    def test_invalid_response_type(self):
        with self.assertRaises(HTMLDocumentLoaderError):
            load_html_document("cadena-no-response")

    # ── 5. Rechazo de respuestas con código no exitoso ────────────
    def test_non_2xx_status_raises_error(self):
        headers = CaseInsensitiveDict({"Content-Type": "text/html"})
        resp = HTTPResponse("HTTP/1.1", 404, "Not Found", headers, b"<html>Not Found</html>")
        with self.assertRaises(HTMLDocumentLoaderError):
            load_html_document(resp)

    # ── 6. Rechazo de Content-Type no HTML ───────────────────────
    def test_non_html_content_type_raises_error(self):
        headers = CaseInsensitiveDict({"Content-Type": "text/css"})
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, b"body { color: red; }")
        with self.assertRaises(HTMLDocumentLoaderError):
            load_html_document(resp)

    # ── 7. Charset desconocido ────────────────────────────────────
    def test_unknown_charset_raises_error(self):
        headers = CaseInsensitiveDict({"Content-Type": "text/html; charset=invalid-charset-xyz"})
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, b"<html></html>")
        with self.assertRaises(HTMLDocumentLoaderError):
            load_html_document(resp)

    # ── 8. Bytes incompatibles con el charset ────────────────────
    def test_incompatible_bytes_raises_error(self):
        headers = CaseInsensitiveDict({"Content-Type": "text/html; charset=utf-8"})
        bad_utf8_bytes = b"\x80\x81\x82\xff"
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, bad_utf8_bytes)
        with self.assertRaises(HTMLDocumentLoaderError):
            load_html_document(resp)


if __name__ == "__main__":
    unittest.main()
