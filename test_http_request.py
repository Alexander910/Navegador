"""
test_http_request.py – Pruebas unitarias para http_request.py.

Ejecutar:
    python -m unittest -v test_http_request
"""

import unittest
from io import StringIO
from unittest.mock import patch
from http_request import (
    HTTPRequest,
    build_get_request,
    print_http_request,
    HTTPRequestError,
    CRLFInjectionError,
)


class TestHTTPRequest(unittest.TestCase):
    """Pruebas de la construcción y formato de peticiones HTTP."""

    # ── 1. Petición GET estándar ─────────────────────────────────
    def test_standard_get_request(self):
        req = build_get_request(
            host="example.com",
            request_target="/index.html",
            port=80,
            scheme="http",
        )
        self.assertEqual(req.method, "GET")
        self.assertEqual(req.request_target, "/index.html")
        self.assertEqual(req.headers["Host"], "example.com")
        self.assertEqual(req.headers["User-Agent"], "MiniBrowser-EDU/1.0")
        self.assertEqual(req.headers["Accept"], "text/html,*/*")
        self.assertEqual(req.headers["Connection"], "close")

    # ── 2. Terminadores \r\n y final \r\n\r\n ────────────────────
    def test_crlf_line_endings(self):
        req = build_get_request(
            host="example.com",
            request_target="/index.html",
            port=443,
            scheme="https",
        )
        raw_str = req.to_string()
        self.assertTrue(raw_str.endswith("\r\n\r\n"))
        lines = raw_str.split("\r\n")
        self.assertEqual(lines[0], "GET /index.html HTTP/1.1")
        self.assertIn("Host: example.com", lines)
        self.assertIn("Connection: close", lines)

    # ── 3. Conversión a bytes ASCII ──────────────────────────────
    def test_to_bytes_ascii(self):
        req = build_get_request("example.com", "/index.html")
        raw_bytes = req.to_bytes()
        self.assertIsInstance(raw_bytes, bytes)
        self.assertEqual(raw_bytes, req.to_string().encode("ascii"))
        self.assertTrue(raw_bytes.startswith(b"GET /index.html HTTP/1.1\r\n"))
        self.assertTrue(raw_bytes.endswith(b"\r\n\r\n"))

    # ── 4. Puerto no predeterminado en Host ──────────────────────
    def test_non_default_port_in_host_header(self):
        req = build_get_request(
            host="example.com",
            request_target="/api",
            port=8080,
            scheme="http",
        )
        self.assertEqual(req.headers["Host"], "example.com:8080")

    def test_default_port_omitted_in_host_header(self):
        req_http = build_get_request("example.com", "/", port=80, scheme="http")
        self.assertEqual(req_http.headers["Host"], "example.com")

        req_https = build_get_request("example.com", "/", port=443, scheme="https")
        self.assertEqual(req_https.headers["Host"], "example.com")

    # ── 5. Integración de ruta y query ────────────────────────────
    def test_request_target_with_query(self):
        req = build_get_request(
            host="example.com",
            request_target="/cursos/index.html?grupo=A",
            port=443,
            scheme="https",
        )
        self.assertEqual(req.request_target, "/cursos/index.html?grupo=A")
        self.assertTrue(req.to_string().startswith("GET /cursos/index.html?grupo=A HTTP/1.1\r\n"))

    # ── 6. Rechazo de entradas inválidas ─────────────────────────
    def test_invalid_scheme(self):
        with self.assertRaises(HTTPRequestError):
            build_get_request("example.com", "/", scheme="ftp")

    def test_empty_host(self):
        with self.assertRaises(HTTPRequestError):
            build_get_request("", "/")

    def test_invalid_port(self):
        with self.assertRaises(HTTPRequestError):
            build_get_request("example.com", "/", port=70000)

    def test_request_target_must_start_with_slash(self):
        with self.assertRaises(HTTPRequestError):
            build_get_request("example.com", "index.html")

    # ── 7. Protección contra inyección CRLF ──────────────────────
    def test_crlf_injection_in_host(self):
        with self.assertRaises(CRLFInjectionError):
            build_get_request("example.com\r\nX-Injected: true", "/")

    def test_crlf_injection_in_target(self):
        with self.assertRaises(CRLFInjectionError):
            build_get_request("example.com", "/index.html\nHost: evil.com")

    # ── 8. Función de impresión ──────────────────────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_print_http_request(self, mock_stdout):
        req = build_get_request("example.com", "/index.html")
        print_http_request(req)
        output = mock_stdout.getvalue()
        self.assertIn("========== HTTP REQUEST ==========", output)
        self.assertIn("GET /index.html HTTP/1.1", output)
        self.assertIn("Host: example.com", output)
        self.assertIn("Connection: close", output)
        self.assertIn("==================================", output)


if __name__ == "__main__":
    unittest.main()
