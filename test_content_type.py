"""
test_content_type.py – Pruebas unitarias para content_type.py.

Ejecutar:
    python -m unittest -v test_content_type
"""

import unittest
from io import StringIO
from unittest.mock import patch
from http_response import HTTPResponse, CaseInsensitiveDict
from content_type import route_content_type, ContentTypeDecision


class TestContentTypeRouter(unittest.TestCase):
    """Pruebas del enrutador por Content-Type."""

    # ── 1. HTML con charset ───────────────────────────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_html_with_charset(self, mock_stdout):
        headers = CaseInsensitiveDict({"Content-Type": "text/html; charset=UTF-8"})
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, b"")
        decision = route_content_type(resp)

        self.assertEqual(decision.media_type, "text/html")
        self.assertEqual(decision.charset, "utf-8")
        self.assertEqual(decision.destination, "html-parser")
        self.assertTrue(decision.is_supported)

        output = mock_stdout.getvalue()
        self.assertIn("[Content-Type] text/html -> html-parser", output)

    # ── 2. XHTML ──────────────────────────────────────────────────
    def test_xhtml_destination(self):
        headers = CaseInsensitiveDict({"Content-Type": "application/xhtml+xml"})
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, b"")
        decision = route_content_type(resp)

        self.assertEqual(decision.media_type, "application/xhtml+xml")
        self.assertEqual(decision.destination, "html-parser")

    # ── 3. CSS con charset ISO-8859-1 ────────────────────────────
    def test_css_destination(self):
        headers = CaseInsensitiveDict({"content-type": "text/css; charset=ISO-8859-1"})
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, b"")
        decision = route_content_type(resp)

        self.assertEqual(decision.media_type, "text/css")
        self.assertEqual(decision.charset, "iso-8859-1")
        self.assertEqual(decision.destination, "css-parser")

    # ── 4. Variantes de JavaScript -> QuickJS ─────────────────────
    def test_javascript_destinations(self):
        js_types = [
            "application/javascript",
            "text/javascript",
            "application/ecmascript",
            "text/ecmascript",
        ]
        for mime in js_types:
            headers = CaseInsensitiveDict({"Content-Type": mime})
            resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, b"")
            decision = route_content_type(resp)
            self.assertEqual(decision.destination, "quickjs", f"Falló para MIME: {mime}")

    # ── 5. Tipo no soportado ──────────────────────────────────────
    def test_unsupported_media_type(self):
        headers = CaseInsensitiveDict({"Content-Type": "image/png"})
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, b"")
        decision = route_content_type(resp)

        self.assertEqual(decision.media_type, "image/png")
        self.assertEqual(decision.destination, "unsupported")
        self.assertFalse(decision.is_supported)

    # ── 6. Cabecera ausente o vacía ───────────────────────────────
    def test_missing_content_type_header(self):
        resp = HTTPResponse("HTTP/1.1", 200, "OK", CaseInsensitiveDict(), b"")
        decision = route_content_type(resp)

        self.assertEqual(decision.media_type, "")
        self.assertIsNone(decision.charset)
        self.assertEqual(decision.destination, "unsupported")
        self.assertFalse(decision.is_supported)

    # ── 7. Charset con comillas ───────────────────────────────────
    def test_quoted_charset(self):
        headers = CaseInsensitiveDict({"Content-Type": 'text/html; charset="UTF-8"'})
        resp = HTTPResponse("HTTP/1.1", 200, "OK", headers, b"")
        decision = route_content_type(resp)

        self.assertEqual(decision.charset, "utf-8")


if __name__ == "__main__":
    unittest.main()
