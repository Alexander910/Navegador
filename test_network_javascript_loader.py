"""
test_network_javascript_loader.py – Pruebas unitarias para javascript_loader.py.

Ejecutar:
    python -m unittest -v test_network_javascript_loader
"""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from http_response import HTTPResponse, CaseInsensitiveDict
from network_loader import FetchedResource
from javascript_loader import JavaScriptLoader, JavaScriptSource, JavaScriptLoadError


class TestJavaScriptLoader(unittest.TestCase):
    """Pruebas del cargador JavaScriptLoader en modo local y red."""

    # ── 1. Modo Local (Compatibilidad) ───────────────────────────
    def test_local_js_load(self):
        loader = JavaScriptLoader(document_path="resources/index.html")
        with patch.object(Path, "read_text", return_value="console.log('Local');"):
            js_source = loader.load("app.js")
            self.assertIsInstance(js_source, JavaScriptSource)
            self.assertEqual(js_source.source, "console.log('Local');")

    # ── 2. Modo Red (con document_url) ───────────────────────────
    def test_network_js_load(self):
        mock_net_loader = MagicMock()
        resp = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "application/javascript"}), b"alert('OK');"
        )
        mock_net_loader.fetch.return_value = FetchedResource(
            url="https://example.com/cursos/js/app.js", response=resp
        )

        loader = JavaScriptLoader(
            document_url="https://example.com/cursos/index.html",
            network_loader=mock_net_loader,
        )

        sources = loader.load_all(["js/app.js"])
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].filename, "https://example.com/cursos/js/app.js")
        self.assertEqual(sources[0].source, "alert('OK');")

    # ── 3. Preservación del Orden en load_all ─────────────────────
    def test_order_preservation(self):
        mock_net_loader = MagicMock()

        def mock_fetch(url):
            return FetchedResource(
                url=url,
                response=HTTPResponse(
                    "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "text/javascript"}), f"// {url}".encode()
                ),
            )

        mock_net_loader.fetch.side_effect = mock_fetch

        loader = JavaScriptLoader(
            document_url="https://example.com/index.html",
            network_loader=mock_net_loader,
        )

        sources = loader.load_all(["first.js", "second.js"])
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0].filename, "https://example.com/first.js")
        self.assertEqual(sources[1].filename, "https://example.com/second.js")

    # ── 4. MIME Types Permitidos ─────────────────────────────────
    def test_allowed_mime_types(self):
        allowed_mimes = [
            "application/javascript",
            "application/x-javascript",
            "text/javascript",
            "application/ecmascript",
            "text/ecmascript",
        ]

        for mime in allowed_mimes:
            mock_net_loader = MagicMock()
            resp = HTTPResponse("HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": mime}), b"let x=1;")
            mock_net_loader.fetch.return_value = FetchedResource(
                url="https://example.com/script.js", response=resp
            )

            loader = JavaScriptLoader(
                document_url="https://example.com/index.html",
                network_loader=mock_net_loader,
            )

            src = loader.load("script.js")
            self.assertEqual(src.source, "let x=1;")

    # ── 5. Rechazo de Content-Type Inválido (e.g. text/html) ─────
    def test_rejected_mime_type_raises_error(self):
        mock_net_loader = MagicMock()
        resp = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "text/html"}), b"<html>404 Not JS</html>"
        )
        mock_net_loader.fetch.return_value = FetchedResource(
            url="https://example.com/fake.js", response=resp
        )

        loader = JavaScriptLoader(
            document_url="https://example.com/index.html",
            network_loader=mock_net_loader,
        )

        with self.assertRaises(JavaScriptLoadError):
            loader.load("fake.js")


if __name__ == "__main__":
    unittest.main()
