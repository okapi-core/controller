import http.client
import urllib.parse


def http_ok(url: str, *, timeout: int = 5) -> bool:
    parsed = urllib.parse.urlparse(url)
    conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    port = parsed.port
    conn = conn_cls(parsed.hostname, port=port, timeout=timeout)
    path = parsed.path or "/"
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        resp.read()
        return 200 <= resp.status < 500
    finally:
        conn.close()
