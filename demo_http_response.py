from url_parser import parse_url
from dns_resolver import resolve_host
from tcp_connection import connect_tcp
from tls_connection import establish_tls
from http_request import build_get_request, print_http_request
from http_transport import exchange_bytes
from http_response import parse_http_response


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

    response = parse_http_response(raw_response)

    print("\n========== HTTP RESPONSE ==========")
    print("Version:", response.version)
    print("Status:", response.status)
    print("Reason:", response.reason)
    print("Headers:", dict(response.headers))
    print("Body:", response.body[:500])
    print("===================================")

finally:
    connection.close()
