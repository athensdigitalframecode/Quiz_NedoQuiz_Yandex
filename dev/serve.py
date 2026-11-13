"""Локальный сервер для проверки: python dev/serve.py [порт] [--mock]
--mock отдаёт dev/tests/mock_sdk.js вместо /sdk.js (подставной SDK Яндекса, НЕ доказательство работы на платформе)."""
import http.server, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
MOCK = "--mock" in sys.argv
port = int(next((a for a in sys.argv[1:] if a.isdigit()), 8791))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=str(ROOT), **k)
    def translate_path(s, path):
        if MOCK and path.split("?")[0] == "/sdk.js": return str(ROOT / "dev/tests/mock_sdk.js")
        return super().translate_path(path)
    def end_headers(s): s.send_header("Cache-Control", "no-store"); super().end_headers()
http.server.ThreadingHTTPServer(("localhost", port), H).serve_forever()
