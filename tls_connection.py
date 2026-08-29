"""
tls_connection.py – Parte 4 del navegador: negociación TLS.

Envuelve un socket TCP conectado (Parte 3) con TLS usando
ssl.create_default_context().  Mantiene activa la validación del
certificado: NO deshabilita check_hostname ni establece
verify_mode = CERT_NONE.

Pasa server_hostname al wrap_socket para:
  - Enviar la extensión SNI al servidor.
  - Verificar que el certificado corresponda al dominio.

Si el certificado no es válido, la conexión falla y el socket TCP
se cierra automáticamente.

Muestra información del handshake: versión TLS, cipher, sujeto,
emisor y vencimiento del certificado.

No envía solicitudes HTTP.
No usa requests, httpx ni urllib.request.
"""

import ssl
import socket
from datetime import datetime


# ── Excepción ─────────────────────────────────────────────────────────
class TLSError(Exception):
    """No se pudo establecer la conexión TLS."""


# ── Función principal ─────────────────────────────────────────────────
def establish_tls(
    tcp_socket: socket.socket,
    host: str,
) -> ssl.SSLSocket:
    """
    Envuelve *tcp_socket* con TLS y devuelve el SSLSocket resultante.

    Parámetros:
        tcp_socket: socket TCP ya conectado (obtenido de connect_tcp).
        host:       nombre de dominio original (para SNI y verificación
                    del certificado).

    Devuelve:
        ssl.SSLSocket con el handshake TLS completado.

    Raises:
        TLSError: si el handshake falla (certificado inválido, timeout,
                  etc.).

    Ejemplo::

        >>> tls_sock = establish_tls(tcp_sock, "example.com")
        >>> tls_sock.close()
    """
    if not host or not host.strip():
        tcp_socket.close()
        raise TLSError("El host no puede estar vacío para TLS.")

    print("[TLS] Iniciando handshake...")

    # Contexto seguro: valida certificados con las CAs del sistema
    context = ssl.create_default_context()

    try:
        tls_socket = context.wrap_socket(
            tcp_socket,
            server_hostname=host,
        )
    except ssl.SSLCertVerificationError as err:
        tcp_socket.close()
        raise TLSError(
            f"Certificado inválido para {host!r}: {err}"
        ) from err
    except ssl.SSLError as err:
        tcp_socket.close()
        raise TLSError(
            f"Error TLS al conectar a {host!r}: {err}"
        ) from err
    except OSError as err:
        tcp_socket.close()
        raise TLSError(
            f"Error de red durante el handshake TLS con {host!r}: {err}"
        ) from err

    # ── Información del handshake ─────────────────────────────────
    print("[TLS] Conexion segura establecida.")
    print(f"[TLS] Version: {tls_socket.version()}")

    cipher_info = tls_socket.cipher()
    if cipher_info:
        print(f"[TLS] Cipher: {cipher_info[0]}")

    cert = tls_socket.getpeercert()
    if cert:
        # Sujeto: buscar commonName
        subject = dict(x[0] for x in cert.get("subject", ()))
        cn = subject.get("commonName", "(desconocido)")
        print(f"[TLS] Certificado sujeto: {cn}")

        # Emisor
        issuer = dict(x[0] for x in cert.get("issuer", ()))
        issuer_cn = issuer.get("commonName", "")
        issuer_org = issuer.get("organizationName", "")
        issuer_display = issuer_cn or issuer_org or "(desconocido)"
        print(f"[TLS] Certificado emisor: {issuer_display}")

        # Vencimiento
        not_after = cert.get("notAfter", "")
        if not_after:
            print(f"[TLS] Certificado vence: {not_after}")

    return tls_socket
