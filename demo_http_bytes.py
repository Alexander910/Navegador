from url_parser import parse_url
from dns_resolver import resolve_host
from tcp_connection import connect_tcp
from tls_connection import establish_tls
from http_request import build_get_request, print_http_request
from http_transport import exchange_bytes


url = parse_url("https://example.com/")

ip_address = resolve_host(url.host)

tcp_socket = connect_tcp(
    host=url.host,
    port=url.port,
    ip_address=ip_address,
)

connection = tcp_socket

try:
    if url.scheme == "https":
        connection = establish_tls(tcp_socket, url.host)

    request = build_get_request(
        host=url.host,
        request_target=url.request_target,
        port=url.port,
        scheme=url.scheme,
    )

    print_http_request(request)

    raw_response = exchange_bytes(
        connection,
        request,
    )

    print("\n========== RESPUESTA EN BYTES ==========")
    print(raw_response[:500])
    print("========================================")

finally:
    connection.close()
