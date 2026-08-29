"""
test_url_resolver.py – Pruebas unitarias para url_resolver.py.

Ejecutar:
    python -m unittest -v test_url_resolver
"""

import unittest
from io import StringIO
from unittest.mock import patch
from url_resolver import resolve_url, URLResolver, URLResolverError


class TestURLResolver(unittest.TestCase):
    """Pruebas de la función resolve_url y la clase URLResolver."""

    BASE_URL = "https://example.com/cursos/index.html"

    # ── 1. Ruta relativa simple ───────────────────────────────────
    def test_relative_path_simple(self):
        res = resolve_url(self.BASE_URL, "styles/main.css")
        self.assertEqual(res, "https://example.com/cursos/styles/main.css")

    # ── 2. Ruta relativa con directorio ───────────────────────────
    def test_relative_path_directory(self):
        res = resolve_url(self.BASE_URL, "js/app.js")
        self.assertEqual(res, "https://example.com/cursos/js/app.js")

    # ── 3. Navegación a directorio padre (..) ─────────────────────
    def test_parent_directory_navigation(self):
        res = resolve_url(self.BASE_URL, "../assets/site.css")
        self.assertEqual(res, "https://example.com/assets/site.css")

    # ── 4. Ruta relativa a la raíz (/) ────────────────────────────
    def test_root_relative_path(self):
        res = resolve_url(self.BASE_URL, "/static/app.js")
        self.assertEqual(res, "https://example.com/static/app.js")

    # ── 5. URL protocol-relative (//) ─────────────────────────────
    def test_protocol_relative_url(self):
        res = resolve_url(self.BASE_URL, "//cdn.example.org/app.js")
        self.assertEqual(res, "https://cdn.example.org/app.js")

    # ── 6. URL absoluta previa se conserva ────────────────────────
    def test_absolute_url_preserved(self):
        res = resolve_url(self.BASE_URL, "https://cdn.example.org/main.css")
        self.assertEqual(res, "https://cdn.example.org/main.css")

    # ── 7. Query string conservado y fragmento eliminado ──────────
    def test_query_kept_fragment_removed(self):
        res = resolve_url(self.BASE_URL, "app.js?v=2#config")
        self.assertEqual(res, "https://example.com/cursos/app.js?v=2")

    # ── 8. Formato de salida impreso por consola ──────────────────
    @patch("sys.stdout", new_callable=StringIO)
    def test_console_output_format(self, mock_stdout):
        resolve_url(self.BASE_URL, "styles/main.css")
        output = mock_stdout.getvalue()
        self.assertIn("[URL] styles/main.css -> https://example.com/cursos/styles/main.css", output)

    # ── 9. Rechazo de entradas inválidas ─────────────────────────
    def test_invalid_base_url_raises_error(self):
        with self.assertRaises(URLResolverError):
            resolve_url("invalid-base-url", "styles/main.css")

    def test_empty_relative_url_raises_error(self):
        with self.assertRaises(URLResolverError):
            resolve_url(self.BASE_URL, "")

    def test_crlf_in_relative_url_raises_error(self):
        with self.assertRaises(URLResolverError):
            resolve_url(self.BASE_URL, "styles/main.css\r\nX-Injected: true")

    # ── 10. Método resolve_all de URLResolver ─────────────────────
    def test_resolve_all(self):
        resolver = URLResolver()
        paths = ["styles/main.css", "../assets/site.css", "/static/app.js"]
        resolved = resolver.resolve_all(self.BASE_URL, paths)
        expected = [
            "https://example.com/cursos/styles/main.css",
            "https://example.com/assets/site.css",
            "https://example.com/static/app.js",
        ]
        self.assertEqual(resolved, expected)


if __name__ == "__main__":
    unittest.main()
