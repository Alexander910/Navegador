"""
test_url_parser.py – 13 pruebas unitarias para url_parser.parse_url.

Ejecutar:
    python -m unittest -v test_url_parser
"""

import unittest
from url_parser import (
    ParsedURL,
    parse_url,
    UnsupportedSchemeError,
    MissingHostError,
    InvalidPortError,
)


class TestParseURL(unittest.TestCase):
    """Pruebas de la función parse_url."""

    # ── 1. URL completa con todos los componentes ─────────────────
    def test_full_url(self):
        url = parse_url("https://example.com:443/cursos/index.html?grupo=A")
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.host, "example.com")
        self.assertEqual(url.port, 443)
        self.assertEqual(url.path, "/cursos/index.html")
        self.assertEqual(url.query, "grupo=A")
        self.assertEqual(url.request_target, "/cursos/index.html?grupo=A")

    # ── 2. Puerto por defecto HTTP (80) ───────────────────────────
    def test_http_default_port(self):
        url = parse_url("http://example.com/index.html")
        self.assertEqual(url.scheme, "http")
        self.assertEqual(url.port, 80)

    # ── 3. Puerto por defecto HTTPS (443) ─────────────────────────
    def test_https_default_port(self):
        url = parse_url("https://example.com/index.html")
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.port, 443)

    # ── 4. Puerto explícito distinto al predeterminado ────────────
    def test_explicit_port(self):
        url = parse_url("http://localhost:8080/api")
        self.assertEqual(url.host, "localhost")
        self.assertEqual(url.port, 8080)

    # ── 5. Ruta vacía se convierte en "/" ─────────────────────────
    def test_empty_path_becomes_slash(self):
        url = parse_url("http://example.com")
        self.assertEqual(url.path, "/")
        self.assertEqual(url.request_target, "/")

    # ── 6. Query con múltiples parámetros ─────────────────────────
    def test_query_multiple_params(self):
        url = parse_url("http://example.com/buscar?q=python&page=2")
        self.assertEqual(url.query, "q=python&page=2")
        self.assertEqual(url.request_target, "/buscar?q=python&page=2")

    # ── 7. Sin query → request_target es solo la ruta ─────────────
    def test_no_query(self):
        url = parse_url("https://example.com/about")
        self.assertIsNone(url.query)
        self.assertEqual(url.request_target, "/about")

    # ── 8. Fragmento descartado ───────────────────────────────────
    def test_fragment_discarded(self):
        url = parse_url("https://example.com/doc#seccion")
        self.assertEqual(url.path, "/doc")
        self.assertIsNone(url.query)

    # ── 9. Fragmento con query: se conserva query, se descarta fragmento
    def test_query_with_fragment(self):
        url = parse_url("http://example.com/page?id=5#top")
        self.assertEqual(url.query, "id=5")
        self.assertEqual(url.request_target, "/page?id=5")

    # ── 10. Esquema no admitido → UnsupportedSchemeError ──────────
    def test_unsupported_scheme(self):
        with self.assertRaises(UnsupportedSchemeError):
            parse_url("ftp://example.com/file")

    # ── 11. Sin esquema → UnsupportedSchemeError ──────────────────
    def test_missing_scheme(self):
        with self.assertRaises(UnsupportedSchemeError):
            parse_url("example.com/page")

    # ── 12. Host ausente → MissingHostError ───────────────────────
    def test_missing_host(self):
        with self.assertRaises(MissingHostError):
            parse_url("http:///ruta")

    # ── 13. Puerto inválido → InvalidPortError ───────────────────
    def test_invalid_port(self):
        with self.assertRaises(InvalidPortError):
            parse_url("http://example.com:abc/page")


if __name__ == "__main__":
    unittest.main()
