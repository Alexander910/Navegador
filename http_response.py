"""
http_response.py – Parte 7 del navegador: parser de respuestas HTTP.

Analiza respuestas HTTP/1.0 y HTTP/1.1 crudas (bytes), extrayendo:
  - Versión de HTTP
  - Código de estado (status)
  - Frase de razón (reason)
  - Cabeceras (headers) con acceso insensible a mayúsculas/minúsculas
  - Cuerpo (body) en bytes, decodificando Transfer-Encoding: chunked o respetando Content-Length

No realiza decodificación de HTML/CSS/JS (permanece en bytes).
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Iterator, Mapping, Any, Optional


# ── Excepciones ───────────────────────────────────────────────────────
class HTTPResponseError(Exception):
    """Error al parsear la respuesta HTTP."""


# ── Diccionario Insensible a Mayúsculas/Minúsculas ──────────────────
class CaseInsensitiveDict(Mapping[str, str]):
    """
    Diccionario para cabeceras HTTP donde la búsqueda de claves no
    distingue entre mayúsculas y minúsculas.
    """

    def __init__(self, data: Optional[Dict[str, str]] = None) -> None:
        self._store: Dict[str, tuple[str, str]] = {}
        if data:
            for k, v in data.items():
                self[k] = v

    def __setitem__(self, key: str, value: str) -> None:
        lower_key = key.lower()
        if lower_key in self._store:
            # Si la cabecera ya existe, se pueden combinar con coma según RFC 7230
            existing_orig_key, existing_val = self._store[lower_key]
            self._store[lower_key] = (existing_orig_key, f"{existing_val}, {value}")
        else:
            self._store[lower_key] = (key, value)

    def __getitem__(self, key: str) -> str:
        lower_key = key.lower()
        if lower_key not in self._store:
            raise KeyError(key)
        return self._store[lower_key][1]

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            return key.lower() in self._store
        return False

    def __iter__(self) -> Iterator[str]:
        return (orig_key for orig_key, _ in self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __repr__(self) -> str:
        return repr(dict(self))


# ── Estructura de Respuesta HTTP ─────────────────────────────────────
@dataclass
class HTTPResponse:
    """Respuesta HTTP/1.1 parseada."""
    version: str
    status: int
    reason: str
    headers: CaseInsensitiveDict = field(default_factory=CaseInsensitiveDict)
    body: bytes = b""


# ── Parsing de Respuestas HTTP ───────────────────────────────────────
def parse_http_response(raw_bytes: bytes) -> HTTPResponse:
    """
    Parsea *raw_bytes* en un objeto ``HTTPResponse``.

    Raises:
        HTTPResponseError: si la estructura del mensaje o los chunks son inválidos.
    """
    if not raw_bytes:
        raise HTTPResponseError("La respuesta recibida está vacía.")

    # 1. Separar cabeceras de cuerpo (\r\n\r\n o \n\n)
    delimiter = b"\r\n\r\n"
    delimiter_len = 4
    pos = raw_bytes.find(delimiter)

    if pos == -1:
        delimiter = b"\n\n"
        delimiter_len = 2
        pos = raw_bytes.find(delimiter)

    if pos == -1:
        raise HTTPResponseError(
            "Respuesta HTTP malformada: no se encontró el delimitador de cabeceras."
        )

    header_bytes = raw_bytes[:pos]
    body_bytes = raw_bytes[pos + delimiter_len:]

    # Decodificar cabeceras en ASCII/Latin-1
    try:
        header_text = header_bytes.decode("iso-8859-1")
    except UnicodeDecodeError as err:
        raise HTTPResponseError(
            f"Error al decodificar las cabeceras HTTP: {err}"
        ) from err

    lines = header_text.splitlines()
    if not lines:
        raise HTTPResponseError("Línea de estado (status line) ausente.")

    # 2. Parsear Status Line
    status_line = lines[0].strip()
    status_parts = status_line.split(" ", 2)

    if len(status_parts) < 2:
        raise HTTPResponseError(f"Línea de estado inválida: {status_line!r}")

    version, status_str = status_parts[0], status_parts[1]
    reason = status_parts[2] if len(status_parts) > 2 else ""

    if not version.startswith("HTTP/"):
        raise HTTPResponseError(f"Versión HTTP no soportada o inválida: {version!r}")

    try:
        status = int(status_str)
        if not (100 <= status <= 599):
            raise ValueError
    except ValueError:
        raise HTTPResponseError(f"Código de estado inválido: {status_str!r}")

    # 3. Parsear Cabeceras
    headers = CaseInsensitiveDict()
    for line in lines[1:]:
        if not line or line.strip() == "":
            continue
        if ":" not in line:
            raise HTTPResponseError(f"Cabecera malformada (sin ':'): {line!r}")
        key, val = line.split(":", 1)
        headers[key.strip()] = val.strip()

    # 4. Procesar el Cuerpo (Body)
    transfer_encoding = headers.get("transfer-encoding", "").lower()

    if "chunked" in transfer_encoding:
        body = _parse_chunked_body(body_bytes)
    elif "content-length" in headers:
        try:
            content_length = int(headers["content-length"])
            if content_length < 0:
                raise ValueError
        except ValueError:
            raise HTTPResponseError(
                f"Valor de Content-Length inválido: {headers['content-length']!r}"
            )

        if len(body_bytes) < content_length:
            raise HTTPResponseError(
                f"Cuerpo incompleto: se esperaban {content_length} bytes, "
                f"pero se recibieron {len(body_bytes)} bytes."
            )
        body = body_bytes[:content_length]
    else:
        # Delimitado por cierre de conexión
        body = body_bytes

    return HTTPResponse(
        version=version,
        status=status,
        reason=reason,
        headers=headers,
        body=body,
    )


def _parse_chunked_body(chunked_bytes: bytes) -> bytes:
    """Descodifica un cuerpo HTTP codificado con Transfer-Encoding: chunked."""
    chunks = []
    idx = 0
    total_len = len(chunked_bytes)

    while idx < total_len:
        # Buscar el final del tamaño del chunk (\r\n o \n)
        eol_idx = chunked_bytes.find(b"\n", idx)
        if eol_idx == -1:
            raise HTTPResponseError("Chunk malformado: no se encontró fin de línea de tamaño.")

        line = chunked_bytes[idx:eol_idx].strip(b"\r")
        # El tamaño del chunk puede incluir parámetros divididos por ';'
        size_str = line.split(b";", 1)[0].strip()

        try:
            chunk_size = int(size_str, 16)
        except ValueError:
            raise HTTPResponseError(f"Tamaño de chunk hexadecimal inválido: {size_str!r}")

        idx = eol_idx + 1

        if chunk_size == 0:
            # Chunk final de tamaño 0 alcanzado
            break

        if idx + chunk_size > total_len:
            raise HTTPResponseError(
                f"Chunk incompleto: se esperaban {chunk_size} bytes."
            )

        chunks.append(chunked_bytes[idx : idx + chunk_size])
        idx += chunk_size

        # Consumir el \r\n tras el contenido del chunk
        if idx < total_len and chunked_bytes[idx:idx+1] == b"\r":
            idx += 1
        if idx < total_len and chunked_bytes[idx:idx+1] == b"\n":
            idx += 1

    return b"".join(chunks)
