"""
test_status_handler.py – Pruebas unitarias para status_handler.py.

Ejecutar:
    python -m unittest -v test_status_handler
"""

import unittest
from io import StringIO
from unittest.mock import patch
from http_response import HTTPResponse, CaseInsensitiveDict
from status_handler import handle_http_status, StatusDecision


class TestStatusHandler(unittest.TestCase):
    """Pruebas del manejador de códigos de estado HTTP."""

    # ── 1. Código 200 OK ──────────────────────────────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_status_200_ok(self, mock_stdout):
        resp = HTTPResponse("HTTP/1.1", 200, "OK", CaseInsensitiveDict(), b"OK")
        decision = handle_http_status(resp)

        self.assertEqual(decision.action, "use-resource")
        self.assertTrue(decision.is_success)
        self.assertFalse(decision.is_redirect)
        self.assertFalse(decision.is_error)
        self.assertIsNone(decision.location)

        output = mock_stdout.getvalue()
        self.assertIn("[HTTP] 200 OK", output)
        self.assertIn("Recurso disponible.", output)

    # ── 2. Redirección 301 Moved Permanently ─────────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_status_301_permanent_redirect(self, mock_stdout):
        headers = CaseInsensitiveDict({"Location": "https://example.com/nueva-ruta"})
        resp = HTTPResponse("HTTP/1.1", 301, "Moved Permanently", headers, b"")
        decision = handle_http_status(resp)

        self.assertEqual(decision.action, "permanent-redirect")
        self.assertTrue(decision.is_redirect)
        self.assertFalse(decision.is_success)
        self.assertEqual(decision.location, "https://example.com/nueva-ruta")

        output = mock_stdout.getvalue()
        self.assertIn("[HTTP] 301 Moved Permanently", output)
        self.assertIn("[HTTP] Location: https://example.com/nueva-ruta", output)
        self.assertIn("Redireccion permanente.", output)

    # ── 3. Redirección 302 Found ──────────────────────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_status_302_temporary_redirect(self, mock_stdout):
        headers = CaseInsensitiveDict({"location": "/temp-page"})
        resp = HTTPResponse("HTTP/1.1", 302, "Found", headers, b"")
        decision = handle_http_status(resp)

        self.assertEqual(decision.action, "redirect")
        self.assertTrue(decision.is_redirect)
        self.assertEqual(decision.location, "/temp-page")

        output = mock_stdout.getvalue()
        self.assertIn("Redireccion temporal.", output)

    # ── 4. Redirección 3xx sin cabecera Location ──────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_status_301_missing_location(self, mock_stdout):
        resp = HTTPResponse("HTTP/1.1", 301, "Moved Permanently", CaseInsensitiveDict(), b"")
        decision = handle_http_status(resp)

        self.assertEqual(decision.action, "error")
        self.assertTrue(decision.is_error)
        self.assertFalse(decision.is_redirect)
        self.assertIsNone(decision.location)

    # ── 5. Error 404 Not Found ───────────────────────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_status_404_not_found(self, mock_stdout):
        resp = HTTPResponse("HTTP/1.1", 404, "Not Found", CaseInsensitiveDict(), b"")
        decision = handle_http_status(resp)

        self.assertEqual(decision.action, "error")
        self.assertTrue(decision.is_error)

        output = mock_stdout.getvalue()
        self.assertIn("[HTTP] 404 Not Found", output)
        self.assertIn("No fue posible cargar el recurso.", output)

    # ── 6. Error 500 Internal Server Error ───────────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_status_500_internal_server_error(self, mock_stdout):
        resp = HTTPResponse("HTTP/1.1", 500, "Internal Server Error", CaseInsensitiveDict(), b"")
        decision = handle_http_status(resp)

        self.assertEqual(decision.action, "error")
        self.assertTrue(decision.is_error)

        output = mock_stdout.getvalue()
        self.assertIn("[HTTP] 500 Internal Server Error", output)
        self.assertIn("Error del servidor.", output)


if __name__ == "__main__":
    unittest.main()
