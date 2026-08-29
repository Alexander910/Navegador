"""
http_transport.py – Parte 6 del navegador: envío y recepción de bytes HTTP.

Transmite solicitudes HTTP a través de un socket conectado (TCP o TLS)
usando socket.sendall() y recibe la respuesta mediante llamadas
iterativas a socket.recv(4096) hasta recibir b"".

Controles:
  - Ensambla fragmentos en orden.
  - Limita el tamaño total de la respuesta (10 MiB por defecto).
  - Maneja timeout, conexión rota y respuesta vacía.
  - No interpreta cabeceras ni cuerpo.
"""

import socket
import ssl
from typing import Union
from http_request import HTTPRequest


# ── Excepciones ───────────────────────────────────────────────────────
class HTTPTransportError(Exception):
    """Error general durante el transporte HTTP (envío o recepción)."""


class EmptyResponseError(HTTPTransportError):
    """El servidor cerró la conexión sin enviar datos."""


class ResponseTooLargeError(HTTPTransportError):
    """La respuesta excedió el tamaño máximo permitido."""


# ── Constantes ────────────────────────────────────────────────────────
DEFAULT_MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MiB
BUFFER_SIZE = 4096


# ── Función Principal ─────────────────────────────────────────────────
def exchange_bytes(
    connection: Union[socket.socket, ssl.SSLSocket],
    request: Union[HTTPRequest, bytes],
    max_response_size: int = DEFAULT_MAX_RESPONSE_SIZE,
    chunk_size: int = BUFFER_SIZE,
) -> bytes:
    """
    Envía la petición HTTP (*request*) y recibe la respuesta completa como bytes.

    Parámetros:
        connection:        socket TCP o SSLSocket conectado.
        request:           objeto HTTPRequest o bytes crudos de la petición.
        max_response_size: límite de tamaño de respuesta en bytes (por defecto 10 MiB).
        chunk_size:        tamaño de cada lectura recv() en bytes (por defecto 4096).

    Devuelve:
        bytes crudos acumulados de la respuesta HTTP.

    Raises:
        HTTPTransportError: si falla el envío/recepción o se supera el límite.
        EmptyResponseError: si la respuesta está vacía.
        ResponseTooLargeError: si se excede el límite max_response_size.
    """
    # Convertir a bytes si es un HTTPRequest
    if isinstance(request, HTTPRequest):
        request_bytes = request.to_bytes()
    elif isinstance(request, bytes):
        request_bytes = request
    else:
        raise HTTPTransportError(
            f"Tipo de petición no soportado: {type(request).__name__}"
        )

    # 1. Envío completo de la petición
    print(f"[HTTP] Enviando {len(request_bytes)} bytes...")
    try:
        connection.sendall(request_bytes)
    except socket.timeout:
        raise HTTPTransportError("Tiempo de espera agotado al enviar la petición HTTP.")
    except OSError as err:
        raise HTTPTransportError(f"Error de socket al enviar petición: {err}") from err

    print("[HTTP] Peticion enviada.")

    # 2. Recepción iterativa de la respuesta
    print("[HTTP] Recibiendo respuesta...")
    fragments = []
    total_received = 0

    try:
        while True:
            fragment = connection.recv(chunk_size)
            if fragment == b"":
                break

            fragment_len = len(fragment)
            print(f"[HTTP] Fragmento recibido: {fragment_len} bytes")
            fragments.append(fragment)
            total_received += fragment_len

            if total_received > max_response_size:
                raise ResponseTooLargeError(
                    f"La respuesta excedió el límite máximo de {max_response_size} bytes."
                )
    except socket.timeout:
        # Si ya recibimos algunos fragmentos antes del timeout, los podemos conservar o fallar.
        if not fragments:
            raise HTTPTransportError("Tiempo de espera agotado al recibir respuesta HTTP.")
    except OSError as err:
        if not fragments:
            raise HTTPTransportError(f"Error de socket al recibir respuesta: {err}") from err

    if not fragments:
        raise EmptyResponseError("El servidor cerró la conexión sin enviar respuesta.")

    response_bytes = b"".join(fragments)
    print(f"[HTTP] Respuesta recibida: {len(response_bytes)} bytes")
    return response_bytes
