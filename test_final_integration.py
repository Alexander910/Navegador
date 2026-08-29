"""
test_final_integration.py – Pruebas unitarias de integración final (Parte 14).

Ejecutar:
    python -m unittest -v test_final_integration
"""

import unittest
from unittest.mock import MagicMock, patch
from io import StringIO
from http_response import HTTPResponse, CaseInsensitiveDict
from network_loader import FetchedResource
from main import load_remote_document
from pipeline import RenderPipeline


class TestFinalIntegration(unittest.TestCase):
    """Pruebas del flujo completo de integración remota (Parte 14)."""

    @patch("network_loader.NetworkLoader")
    def test_load_remote_document(self, mock_loader_cls):
        mock_loader = MagicMock()
        mock_loader_cls.return_value = mock_loader

        html_body = (
            b"<!doctype html>"
            b"<html>"
            b"<head>"
            b'<link rel="stylesheet" href="styles.css">'
            b"<title>Test Page</title>"
            b"</head>"
            b"<body>"
            b'<h1 id="title">Hello World</h1>'
            b'<script src="script.js"></script>'
            b"</body>"
            b"</html>"
        )
        resp = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "text/html; charset=utf-8"}), html_body
        )
        mock_loader.fetch.return_value = FetchedResource(
            url="https://example.com/index.html", response=resp
        )

        doc, final_url = load_remote_document("https://example.com/index.html", loader=mock_loader)

        self.assertEqual(final_url, "https://example.com/index.html")
        self.assertIsNotNone(doc)

    def test_full_pipeline_remote_execution(self):
        mock_loader = MagicMock()

        # 1. Mock de respuestas para HTML, CSS y JS
        html_resp = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "text/html"}),
            b'<html><head><link rel="stylesheet" href="style.css"></head><body><h1 id="main">Title</h1><script src="app.js"></script></body></html>'
        )
        css_resp = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "text/css"}),
            b"h1 { color: red; }"
        )
        js_resp = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "application/javascript"}),
            b"document.getElementById('main').textContent = 'Loaded';"
        )

        def mock_fetch(url):
            if "style.css" in url:
                return FetchedResource(url=url, response=css_resp)
            if "app.js" in url:
                return FetchedResource(url=url, response=js_resp)
            return FetchedResource(url=url, response=html_resp)

        mock_loader.fetch.side_effect = mock_fetch

        # 2. Cargar documento HTML remoto
        doc, document_url = load_remote_document("https://example.com/index.html", loader=mock_loader)

        # 3. Inicializar RenderPipeline con la URL remota y el mock loader
        pipeline = RenderPipeline(
            doc,
            canvas=None,
            document_url=document_url,
            network_loader=mock_loader,
        )

        # 4. Renderizado (HTML → CSS → CSSOM → RenderTree → Layout)
        render_tree = pipeline.render()
        self.assertIsNotNone(render_tree)
        self.assertEqual(len(pipeline.css_sources), 1)
        self.assertEqual(pipeline.css_sources[0].filename, "https://example.com/style.css")

        # 5. Ejecución de scripts
        scripts = pipeline.execute_scripts()
        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0].filename, "https://example.com/app.js")

    @patch("sys.stdout", new_callable=StringIO)
    def test_unsupported_js_api_graceful_handling(self, mock_stdout):
        """Verifica que APIs no soportadas (como localStorage) no detengan el pipeline."""
        mock_loader = MagicMock()

        html_resp = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "text/html"}),
            b'<html><body><script src="bad.js"></script><script src="good.js"></script></body></html>'
        )
        bad_js = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "application/javascript"}),
            b"localStorage.setItem('key', 'val');"
        )
        good_js = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "application/javascript"}),
            b"var a = 1;"
        )

        def mock_fetch(url):
            if "bad.js" in url:
                return FetchedResource(url=url, response=bad_js)
            if "good.js" in url:
                return FetchedResource(url=url, response=good_js)
            return FetchedResource(url=url, response=html_resp)

        mock_loader.fetch.side_effect = mock_fetch

        doc, document_url = load_remote_document("https://example.com/index.html", loader=mock_loader)
        pipeline = RenderPipeline(doc, canvas=None, document_url=document_url, network_loader=mock_loader)
        pipeline.render()

        scripts = pipeline.execute_scripts()
        self.assertEqual(len(scripts), 2)

        output = mock_stdout.getvalue()
        self.assertIn("[JavaScript] No se pudo ejecutar 'https://example.com/bad.js'", output)


if __name__ == "__main__":
    unittest.main()
