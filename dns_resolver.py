"""
dns_resolver.py – Parte 2 del navegador: resolución DNS.

Recibe exclusivamente el nombre del host (obtenido del URL Parser).
Utiliza el resolvedor DNS del sistema mediante socket.gethostbyname().
Devuelve la dirección IP como cadena.
Muestra los mensajes de diagnóstico exigidos por el PDF.
Detecta si el host ya es una dirección IP y evita una consulta DNS
innecesaria.
Convierte errores de resolución en DNSResolutionError.
No abre conexiones TCP.
No inicia TLS.
No envía solicitudes HTTP.
"""

import socket


# ── Excepción ─────────────────────────────────────────────────────────
class DNSResolutionError(Exception):
    """No se pudo resolver el nombre de host a una dirección IP."""


# ── Utilidad: detectar si ya es una IP ────────────────────────────────
def _is_ip_address(host: str) -> bool:
    """Devuelve True si *host* ya es una dirección IPv4 o IPv6 válida."""
    # Intentar IPv4
    try:
        socket.inet_aton(host)
        return True
    except OSError:
        pass
    # Intentar IPv6
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True
    except OSError:
        pass
    return False


# ── Función principal ─────────────────────────────────────────────────
def resolve_host(host: str) -> str:
    """
    Resuelve *host* a una dirección IP usando el DNS del sistema.

    Si *host* ya es una dirección IP, la devuelve directamente sin
    realizar una consulta DNS.

    Ejemplo::

        >>> resolve_host("example.com")   # doctest: +SKIP
        '93.184.216.34'

    Raises:
        DNSResolutionError: si el nombre no se puede resolver.
    """
    # Si ya es una IP, no hace falta resolver
    if _is_ip_address(host):
        print(f"[DNS] {host} ya es una dirección IP, no se necesita resolución.")
        return host

    print(f"[DNS] Resolviendo {host}...")

    try:
        ip_address = socket.gethostbyname(host)
    except socket.gaierror as err:
        raise DNSResolutionError(
            f"No se pudo resolver el host {host!r}: {err}"
        ) from err

    print(f"[DNS] Direccion encontrada: {ip_address}")
    return ip_address
