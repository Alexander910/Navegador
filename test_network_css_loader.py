"""
test_network_css_loader.py – Pruebas unitarias para network_loader.py y css_loader.py.

Ejecutar:
    python -m unittest -v test_network_css_loader
"""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from http_response import HTTPResponse, CaseInsensitiveDict
from network_loader import NetworkLoader, NetworkLoaderError, FetchedResource
from css_loader import CSSLoader, CSSSource, CSSLoadError


class TestNetworkLoader(unittest.TestCase):
    """Pruebas del cargador de red NetworkLoader."""

    @patch("network_loader.parse_url")
    @patch("network_loader.resolve_host")
    @patch("network_loader.connect_tcp")
    @patch("network_loader.establish_tls")
    @patch("network_loader.build_get_request")
    @patch("network_loader.exchange_bytes")
    @patch("network_loader.parse_http_response")
    def test_fetch_success(
        self,
        mock_parse_resp,
        mock_exchange,
        mock_build_req,
        mock_tls,
        mock_tcp,
        mock_dns,
        mock_parse_url,
    ):
        mock_parsed = MagicMock()
        mock_parsed.scheme = "https"
        mock_parsed.host = "example.com"
        mock_parsed.port = 443
        mock_parsed.request_target = "/style.css"
        mock_parse_url.return_value = mock_parsed

        mock_dns.return_value = "93.184.216.34"
        mock_sock = MagicMock()
        mock_tcp.return_value = mock_sock
        mock_tls.return_value = mock_sock

        resp = HTTPResponse("HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "text/css"}), b"body { margin: 0; }")
        mock_parse_resp.return_value = resp

        loader = NetworkLoader()
        fetched = loader.fetch("https://example.com/style.css")

        self.assertEqual(fetched.url, "https://example.com/style.css")
        self.assertEqual(fetched.response.status, 200)
        self.assertEqual(fetched.response.body, b"body { margin: 0; }")

    @patch("network_loader.parse_url")
    @patch("network_loader.resolve_host")
    @patch("network_loader.connect_tcp")
    @patch("network_loader.build_get_request")
    @patch("network_loader.exchange_bytes")
    @patch("network_loader.parse_http_response")
    def test_fetch_redirect_302(
        self,
        mock_parse_resp,
        mock_exchange,
        mock_build_req,
        mock_tcp,
        mock_dns,
        mock_parse_url,
    ):
        # 1. Petición inicial -> 302 Found
        resp_302 = HTTPResponse(
            "HTTP/1.1", 302, "Found", CaseInsensitiveDict({"Location": "/assets/style.css"}), b""
        )
        # 2. Petición redireccionada -> 200 OK
        resp_200 = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "text/css"}), b"h1 { color: red; }"
        )

        mock_parse_resp.side_effect = [resp_302, resp_200]

        loader = NetworkLoader()
        fetched = loader.fetch("http://example.com/style.css")

        self.assertEqual(fetched.url, "http://example.com/assets/style.css")
        self.assertEqual(fetched.response.body, b"h1 { color: red; }")


class TestCSSLoader(unittest.TestCase):
    """Pruebas del cargador CSSLoader en modo local y red."""

    # ── 1. Modo Local (Compatibilidad) ───────────────────────────
    def test_local_css_load(self):
        loader = CSSLoader(resources_path="resources")
        # Si resources/style.css existe o probamos la lógica de resolución
        with patch.object(Path, "read_text", return_value="body { color: black; }"):
            css_source = loader.load("style.css")
            self.assertIsInstance(css_source, CSSSource)
            self.assertEqual(css_source.source, "body { color: black; }")

    # ── 2. Modo Red (con document_url) ───────────────────────────
    def test_network_css_load(self):
        mock_net_loader = MagicMock()
        resp = HTTPResponse(
            "HTTP/1.1", 200, "OK", CaseInsensitiveDict({"Content-Type": "text/css"}), b"p { color: blue; }"
        )
        mock_net_loader.fetch.return_value = FetchedResource(
            url="https://example.com/cursos/styles/main.css", response=resp
        )

        loader = CSSLoader(
            document_url="https://example.com/cursos/index.html",
            network_loader=mock_net_loader,
        )

        css_sources = loader.load_all(["styles/main.css"])
        self.assertEqual(len(css_sources), 1)
        self.assertEqual(css_sources[0].filename, "https://example.com/cursos/styles/main.css")
        self.assertEqual(css_sources[0].source, "p { color: blue; }")

    # ── 3. Fallo HTTP 404 en red lanza CSSLoadError ──────────────
    def test_network_404_raises_error(self):
        mock_net_loader = MagicMock()
        resp = HTTPResponse(
            "HTTP/1.1", 404, "Not Found", CaseInsensitiveDict({"Content-Type": "text/html"}), b"404"
        )
        mock_net_loader.fetch.return_value = FetchedResource(
            url="https://example.com/missing.css", response=resp
        )

        loader = CSSLoader(
            document_url="https://example.com/index.html",
            network_loader=mock_net_loader,
        )

        with self.assertRaises(CSSLoadError):
            loader.load("missing.css")


if __name__ == "__main__":
    unittest.main()
