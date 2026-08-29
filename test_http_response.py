"""
test_http_response.py – Pruebas unitarias para http_response.py.

Ejecutar:
    python -m unittest -v test_http_response
"""

import unittest
from http_response import (
    parse_http_response,
    HTTPResponse,
    HTTPResponseError,
    CaseInsensitiveDict,
)


class TestHTTPResponseParser(unittest.TestCase):
    """Pruebas del parser de respuestas HTTP."""

    # ── 1. Respuesta HTTP/1.1 básica con 200 OK ──────────────────
    def test_basic_parse_200_ok(self):
        raw = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/html\r\n"
            b"Content-Length: 15\r\n"
            b"\r\n"
            b"<html>OK</html>"
        )
        resp = parse_http_response(raw)
        self.assertEqual(resp.version, "HTTP/1.1")
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.reason, "OK")
        self.assertEqual(resp.headers["Content-Type"], "text/html")
        self.assertEqual(resp.body, b"<html>OK</html>")

    # ── 2. Acceso a cabeceras case-insensitive ────────────────────
    def test_case_insensitive_headers(self):
        raw = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/html\r\n"
            b"\r\n"
            b"Test"
        )
        resp = parse_http_response(raw)
        self.assertEqual(resp.headers["content-type"], "text/html")
        self.assertEqual(resp.headers["Content-Type"], "text/html")
        self.assertEqual(resp.headers["CONTENT-TYPE"], "text/html")
        self.assertIn("content-type", resp.headers)
        self.assertIn("Content-Type", resp.headers)

    # ── 3. Razón con múltiples palabras (e.g. 404 Not Found) ─────
    def test_multi_word_reason_phrase(self):
        raw = (
            b"HTTP/1.1 404 Not Found\r\n"
            b"Content-Length: 9\r\n"
            b"\r\n"
            b"Not Found"
        )
        resp = parse_http_response(raw)
        self.assertEqual(resp.status, 404)
        self.assertEqual(resp.reason, "Not Found")

    # ── 4. Soporte para HTTP/1.0 ─────────────────────────────────
    def test_http_1_0_response(self):
        raw = (
            b"HTTP/1.0 200 OK\r\n"
            b"Server: SimpleServer\r\n"
            b"\r\n"
            b"Hello 1.0"
        )
        resp = parse_http_response(raw)
        self.assertEqual(resp.version, "HTTP/1.0")
        self.assertEqual(resp.status, 200)

    # ── 5. Conversión dict(response.headers) ──────────────────────
    def test_dict_conversion(self):
        raw = (
            b"HTTP/1.1 200 OK\r\n"
            b"Server: Test\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"Data"
        )
        resp = parse_http_response(raw)
        headers_dict = dict(resp.headers)
        self.assertIsInstance(headers_dict, dict)
        self.assertEqual(headers_dict["Server"], "Test")
        self.assertEqual(headers_dict["Content-Type"], "text/plain")

    # ── 6. Delimitado por Content-Length ─────────────────────────
    def test_content_length_delimited(self):
        raw = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Length: 5\r\n"
            b"\r\n"
            b"1234567890"  # Exceso ignorado
        )
        resp = parse_http_response(raw)
        self.assertEqual(resp.body, b"12345")

    # ── 7. Transfer-Encoding: chunked ────────────────────────────
    def test_chunked_transfer_encoding(self):
        raw = (
            b"HTTP/1.1 200 OK\r\n"
            b"Transfer-Encoding: chunked\r\n"
            b"\r\n"
            b"7\r\n"
            b"Mozilla\r\n"
            b"a\r\n"
            b" Developer\r\n"
            b"0\r\n"
            b"\r\n"
        )
        resp = parse_http_response(raw)
        self.assertEqual(resp.body, b"Mozilla Developer")

    # ── 8. Cuerpo incompleto lanza HTTPResponseError ──────────────
    def test_incomplete_body_raises_error(self):
        raw = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Length: 50\r\n"
            b"\r\n"
            b"Short"
        )
        with self.assertRaises(HTTPResponseError):
            parse_http_response(raw)

    # ── 9. Status Line o cabeceras malformadas ───────────────────
    def test_empty_raw_bytes_raises_error(self):
        with self.assertRaises(HTTPResponseError):
            parse_http_response(b"")

    def test_no_header_delimiter_raises_error(self):
        with self.assertRaises(HTTPResponseError):
            parse_http_response(b"HTTP/1.1 200 OK")

    def test_invalid_status_code_raises_error(self):
        raw = b"HTTP/1.1 ABC OK\r\n\r\n"
        with self.assertRaises(HTTPResponseError):
            parse_http_response(raw)

    def test_malformed_header_line_raises_error(self):
        raw = b"HTTP/1.1 200 OK\r\nInvalidHeaderNoColon\r\n\r\n"
        with self.assertRaises(HTTPResponseError):
            parse_http_response(raw)

    def test_malformed_chunk_hex_raises_error(self):
        raw = (
            b"HTTP/1.1 200 OK\r\n"
            b"Transfer-Encoding: chunked\r\n"
            b"\r\n"
            b"XYZ\r\n"
            b"Data\r\n"
        )
        with self.assertRaises(HTTPResponseError):
            parse_http_response(raw)


if __name__ == "__main__":
    unittest.main()
