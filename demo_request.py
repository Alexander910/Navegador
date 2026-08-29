from url_parser import parse_url
from http_request import build_get_request, print_http_request

parsed_url = parse_url("https://example.com/index.html")

request = build_get_request(
    host=parsed_url.host,
    request_target=parsed_url.request_target,
    port=parsed_url.port,
    scheme=parsed_url.scheme,
)

print_http_request(request)
