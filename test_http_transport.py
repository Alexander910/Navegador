"""
test_http_transport.py – Pruebas unitarias para http_transport.py.

Ejecutar:
    python -m unittest -v test_http_transport
"""

import unittest
import socket
from unittest.mock import MagicMock
from http_request import build_get_request
from http_transport import (
    exchange_bytes,
    HTTPTransportError,
    EmptyResponseError,
    ResponseTooLargeError,
)


class TestHTTPTransport(unittest.TestCase):
    """Pruebas de la función exchange_bytes."""

    # ── 1. Intercambio exitoso con HTTPRequest ────────────────────
    def test_successful_exchange_with_httprequest(self):
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = [
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n",
            b"<html><body>Hello</body></html>",
            b"",
        ]

        req = build_get_request("example.com", "/")
        response = exchange_bytes(mock_sock, req)

        mock_sock.sendall.assert_called_once_with(req.to_bytes())
        self.assertEqual(
            response,
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body>Hello</body></html>",
        )

    # ── 2. Intercambio exitoso con bytes crudos ──────────────────
    def test_successful_exchange_with_bytes(self):
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = [b"HTTP/1.1 200 OK\r\n\r\nOK", b""]

        raw_req = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
        response = exchange_bytes(mock_sock, raw_req)

        mock_sock.sendall.assert_called_once_with(raw_req)
        self.assertEqual(response, b"HTTP/1.1 200 OK\r\n\r\nOK")

    # ── 3. Respuesta vacía lanza EmptyResponseError ──────────────
    def test_empty_response_raises_error(self):
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""

        req = build_get_request("example.com", "/")
        with self.assertRaises(EmptyResponseError):
            exchange_bytes(mock_sock, req)

    # ── 4. Exceder max_response_size lanza ResponseTooLargeError ─
    def test_response_too_large(self):
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = [b"A" * 100, b"B" * 100, b""]

        req = build_get_request("example.com", "/")
        with self.assertRaises(ResponseTooLargeError):
            exchange_bytes(mock_sock, req, max_response_size=150)

    # ── 5. Error en sendall lanza HTTPTransportError ─────────────
    def test_send_error_raises_error(self):
        mock_sock = MagicMock()
        mock_sock.sendall.side_effect = socket.error("Network unreachable")

        req = build_get_request("example.com", "/")
        with self.assertRaises(HTTPTransportError):
            exchange_bytes(mock_sock, req)

    # ── 6. Tipo de petición inválido ─────────────────────────────
    def test_invalid_request_type(self):
        mock_sock = MagicMock()
        with self.assertRaises(HTTPTransportError):
            exchange_bytes(mock_sock, 12345)


if __name__ == "__main__":
    unittest.main()
