"""
tcp_connection.py – Parte 3 del navegador: conexión TCP.

Recibe el host, la IP resuelta por dns_resolver y el puerto del URL
Parser.  Crea un socket TCP, se conecta a la IP:puerto y devuelve el
socket conectado para que la capa superior (TLS o HTTP) lo utilice.

Configura un timeout para evitar bloqueos indefinidos.
Maneja timeout, conexión rechazada, host vacío y puerto inválido.

No inicia TLS.
No solicita index.html.
No transmite HTTP.
No usa requests, httpx ni urllib.request.
"""

import socket

# ── Excepción ─────────────────────────────────────────────────────────
class TCPConnectionError(Exception):
    """No se pudo establecer la conexión TCP."""


# ── Constantes ────────────────────────────────────────────────────────
DEFAULT_TIMEOUT = 10  # segundos


# ── Función principal ─────────────────────────────────────────────────
def connect_tcp(
    host: str,
    port: int,
    ip_address: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> socket.socket:
    """
    Establece una conexión TCP hacia *ip_address*:*port* y devuelve el
    socket conectado.

    Parámetros:
        host:       nombre original del host (para mensajes y futuro TLS).
        port:       puerto destino (obtenido del URL Parser).
        ip_address: dirección IP resuelta (obtenida del DNS Resolver).
        timeout:    segundos máximos de espera (por defecto 10).

    Devuelve:
        socket.socket conectado y listo para enviar datos.

    Raises:
        TCPConnectionError: si la conexión falla por cualquier motivo.

    Ejemplo::

        >>> sock = connect_tcp("example.com", 443, "93.184.216.34")
        >>> sock.close()
    """
    # Validaciones básicas
    if not host or not host.strip():
        raise TCPConnectionError("El host no puede estar vacío.")

    if not isinstance(port, int) or not (1 <= port <= 65535):
        raise TCPConnectionError(
            f"Puerto inválido: {port!r}. Debe ser un entero entre 1 y 65535."
        )

    if not ip_address or not ip_address.strip():
        raise TCPConnectionError("La dirección IP no puede estar vacía.")

    print("[TCP] Conectando...")
    print(f"[TCP] Host: {host}")
    print(f"[TCP] Puerto: {port}")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip_address, port))
    except socket.timeout:
        raise TCPConnectionError(
            f"Tiempo de espera agotado al conectar a {host}:{port} "
            f"({ip_address})"
        )
    except ConnectionRefusedError:
        raise TCPConnectionError(
            f"Conexión rechazada por {host}:{port} ({ip_address})"
        )
    except OSError as err:
        raise TCPConnectionError(
            f"Error de red al conectar a {host}:{port} ({ip_address}): {err}"
        ) from err

    print("[TCP] Conexion establecida.")
    return sock
