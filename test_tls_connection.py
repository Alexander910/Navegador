"""
test_tls_connection.py – Pruebas unitarias para tls_connection.establish_tls.

Ejecutar:
    python -m unittest -v test_tls_connection
"""

import unittest
from unittest.mock import patch, MagicMock
import ssl
from tls_connection import establish_tls, TLSError


class TestEstablishTLS(unittest.TestCase):
    """Pruebas de la función establish_tls."""

    # ── 1. Host vacío cierra socket y lanza TLSError ──────────────
    def test_empty_host_raises_error(self):
        mock_sock = MagicMock()
        with self.assertRaises(TLSError):
            establish_tls(mock_sock, "")
        mock_sock.close.assert_called_once()

    # ── 2. Host solo espacios cierra socket y lanza TLSError ──────
    def test_whitespace_host_raises_error(self):
        mock_sock = MagicMock()
        with self.assertRaises(TLSError):
            establish_tls(mock_sock, "   ")
        mock_sock.close.assert_called_once()

    # ── 3. Handshake exitoso devuelve SSLSocket ───────────────────
    @patch("tls_connection.ssl.create_default_context")
    def test_successful_handshake(self, mock_ctx_cls):
        mock_ctx = MagicMock()
        mock_ctx_cls.return_value = mock_ctx

        mock_tls_sock = MagicMock(spec=ssl.SSLSocket)
        mock_tls_sock.version.return_value = "TLSv1.3"
        mock_tls_sock.cipher.return_value = (
            "TLS_AES_256_GCM_SHA384", "TLSv1.3", 256
        )
        mock_tls_sock.getpeercert.return_value = {
            "subject": (
                (("commonName", "example.com"),),
            ),
            "issuer": (
                (("organizationName", "DigiCert Inc"),),
                (("commonName", "DigiCert Global G2 TLS RSA SHA256 2020 CA1"),),
            ),
            "notAfter": "Mar 14 23:59:59 2026 GMT",
        }
        mock_ctx.wrap_socket.return_value = mock_tls_sock

        mock_tcp_sock = MagicMock()
        result = establish_tls(mock_tcp_sock, "example.com")

        mock_ctx.wrap_socket.assert_called_once_with(
            mock_tcp_sock,
            server_hostname="example.com",
        )
        self.assertEqual(result, mock_tls_sock)

    # ── 4. Error de certificado cierra socket TCP ─────────────────
    @patch("tls_connection.ssl.create_default_context")
    def test_cert_error_closes_tcp_socket(self, mock_ctx_cls):
        mock_ctx = MagicMock()
        mock_ctx_cls.return_value = mock_ctx
        mock_ctx.wrap_socket.side_effect = ssl.SSLCertVerificationError(
            "certificate verify failed"
        )

        mock_tcp_sock = MagicMock()
        with self.assertRaises(TLSError):
            establish_tls(mock_tcp_sock, "bad-cert.example.com")
        mock_tcp_sock.close.assert_called_once()

    # ── 5. Error SSL genérico cierra socket TCP ───────────────────
    @patch("tls_connection.ssl.create_default_context")
    def test_ssl_error_closes_tcp_socket(self, mock_ctx_cls):
        mock_ctx = MagicMock()
        mock_ctx_cls.return_value = mock_ctx
        mock_ctx.wrap_socket.side_effect = ssl.SSLError("handshake failure")

        mock_tcp_sock = MagicMock()
        with self.assertRaises(TLSError):
            establish_tls(mock_tcp_sock, "example.com")
        mock_tcp_sock.close.assert_called_once()

    # ── 6. Se usa create_default_context (no contexto inseguro) ───
    @patch("tls_connection.ssl.create_default_context")
    def test_uses_default_secure_context(self, mock_ctx_cls):
        mock_ctx = MagicMock()
        mock_ctx_cls.return_value = mock_ctx

        mock_tls_sock = MagicMock(spec=ssl.SSLSocket)
        mock_tls_sock.version.return_value = "TLSv1.3"
        mock_tls_sock.cipher.return_value = ("AES", "TLSv1.3", 256)
        mock_tls_sock.getpeercert.return_value = {
            "subject": ((("commonName", "example.com"),),),
            "issuer": ((("commonName", "CA"),),),
            "notAfter": "Dec 31 23:59:59 2026 GMT",
        }
        mock_ctx.wrap_socket.return_value = mock_tls_sock

        mock_tcp_sock = MagicMock()
        establish_tls(mock_tcp_sock, "example.com")

        # Verifica que se usó create_default_context (seguro)
        mock_ctx_cls.assert_called_once()


if __name__ == "__main__":
    unittest.main()
