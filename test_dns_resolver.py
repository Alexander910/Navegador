"""
test_dns_resolver.py – Pruebas unitarias para dns_resolver.resolve_host.

Ejecutar:
    python -m unittest -v test_dns_resolver
"""

import unittest
from unittest.mock import patch
from dns_resolver import resolve_host, DNSResolutionError, _is_ip_address


class TestIsIPAddress(unittest.TestCase):
    """Pruebas de la función auxiliar _is_ip_address."""

    def test_ipv4_valid(self):
        self.assertTrue(_is_ip_address("192.168.1.1"))

    def test_ipv4_loopback(self):
        self.assertTrue(_is_ip_address("127.0.0.1"))

    def test_hostname_not_ip(self):
        self.assertFalse(_is_ip_address("example.com"))

    def test_empty_string_not_ip(self):
        self.assertFalse(_is_ip_address(""))


class TestResolveHost(unittest.TestCase):
    """Pruebas de la función resolve_host."""

    # ── 1. Host conocido se resuelve a una IP válida ──────────────
    @patch("dns_resolver.socket.gethostbyname", return_value="93.184.216.34")
    def test_resolve_known_host(self, mock_dns):
        ip = resolve_host("example.com")
        self.assertEqual(ip, "93.184.216.34")
        mock_dns.assert_called_once_with("example.com")

    # ── 2. Si ya es una IPv4, se devuelve sin consulta DNS ────────
    def test_ip_passthrough_ipv4(self):
        ip = resolve_host("93.184.216.34")
        self.assertEqual(ip, "93.184.216.34")

    # ── 3. Localhost se resuelve correctamente ────────────────────
    @patch("dns_resolver.socket.gethostbyname", return_value="127.0.0.1")
    def test_resolve_localhost(self, mock_dns):
        ip = resolve_host("localhost")
        self.assertEqual(ip, "127.0.0.1")

    # ── 4. Host inexistente lanza DNSResolutionError ──────────────
    def test_invalid_host_raises_error(self):
        with self.assertRaises(DNSResolutionError):
            resolve_host("este-dominio-no-existe-xyz123.invalid")

    # ── 5. El resultado es siempre una cadena ─────────────────────
    @patch("dns_resolver.socket.gethostbyname", return_value="140.82.121.4")
    def test_result_is_string(self, mock_dns):
        ip = resolve_host("github.com")
        self.assertIsInstance(ip, str)


if __name__ == "__main__":
    unittest.main()
