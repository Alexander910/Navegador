"""
network_loader.py – Parte 12 del navegador: cargador de red.

Descarga recursos remotos a través del pipeline completo de red:
  URL Parser → DNS Resolver → TCP Connection → TLS Connection → HTTP Request → Exchange Bytes → Response Parser → Status Handler.

Soporta redirecciones HTTP (301 y 302) hasta un máximo configurable (5 por defecto).
Devuelve un objeto FetchedResource con la URL final y el HTTPResponse.
"""

from dataclasses import dataclass
from typing import Optional
from url_parser import parse_url, URLError
from dns_resolver import resolve_host, DNSResolutionError
from tcp_connection import connect_tcp, TCPConnectionError
from tls_connection import establish_tls, TLSError
from http_request import build_get_request
from http_transport import exchange_bytes, HTTPTransportError
from http_response import parse_http_response, HTTPResponse, HTTPResponseError
from status_handler import handle_http_status
from url_resolver import resolve_url, URLResolverError


# ── Excepción ─────────────────────────────────────────────────────────
class NetworkLoaderError(Exception):
    """Error general durante la carga de recursos de red."""


# ── Resultado de la Carga de Red ──────────────────────────────────────
@dataclass(frozen=True)
class FetchedResource:
    """Resultado devuelto por NetworkLoader al descargar una URL."""
    url: str
    response: HTTPResponse


# ── Cargador de Red ───────────────────────────────────────────────────
class NetworkLoader:
    """Ejecuta peticiones GET de red y gestiona las redirecciones."""

    def __init__(self, max_redirects: int = 5) -> None:
        self.max_redirects = max_redirects

    def fetch(self, url: str) -> FetchedResource:
        """
        Descarga la URL dada manejando redirecciones automáticas.

        Raises:
            NetworkLoaderError: si falla cualquier capa de red o se supera el límite de redirecciones.
        """
        current_url = url
        redirect_count = 0

        while redirect_count <= self.max_redirects:
            try:
                parsed_url = parse_url(current_url)
                ip_address = resolve_host(parsed_url.host)
                tcp_socket = connect_tcp(
                    host=parsed_url.host,
                    port=parsed_url.port,
                    ip_address=ip_address,
                )
            except (URLError, DNSResolutionError, TCPConnectionError) as err:
                raise NetworkLoaderError(
                    f"Fallo al conectar con {current_url!r}: {err}"
                ) from err

            connection = tcp_socket
            try:
                if parsed_url.scheme == "https":
                    connection = establish_tls(tcp_socket, parsed_url.host)

                request = build_get_request(
                    host=parsed_url.host,
                    request_target=parsed_url.request_target,
                    port=parsed_url.port,
                    scheme=parsed_url.scheme,
                )

                raw_response = exchange_bytes(connection, request)
                response = parse_http_response(raw_response)
                status_decision = handle_http_status(response)

            except (TLSError, HTTPTransportError, HTTPResponseError) as err:
                raise NetworkLoaderError(
                    f"Error de protocolo al descargar {current_url!r}: {err}"
                ) from err
            finally:
                connection.close()

            # Evaluar decisión de estado
            if status_decision.is_redirect:
                redirect_count += 1
                if redirect_count > self.max_redirects:
                    raise NetworkLoaderError(
                        f"Demasiadas redirecciones ({redirect_count}) al intentar descargar {url!r}"
                    )
                if not status_decision.location:
                    raise NetworkLoaderError(
                        f"Redirección sin cabecera Location en {current_url!r}"
                    )

                try:
                    current_url = resolve_url(current_url, status_decision.location)
                except URLResolverError as err:
                    raise NetworkLoaderError(
                        f"No se pudo resolver la URL de redirección {status_decision.location!r}: {err}"
                    ) from err
            else:
                return FetchedResource(url=current_url, response=response)

        raise NetworkLoaderError(f"Se excedió el límite de redirecciones para {url!r}")
