from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse


class _ResultStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[str, threading.Event] = {}
        self._data: dict[str, dict[str, Any]] = {}

    def put(self, execution_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._data[execution_id] = payload
            if execution_id not in self._events:
                self._events[execution_id] = threading.Event()
            self._events[execution_id].set()

    def wait(self, execution_id: str, timeout: float) -> dict[str, Any] | None:
        with self._lock:
            event = self._events.setdefault(execution_id, threading.Event())
        done = event.wait(timeout)
        if not done:
            return None
        with self._lock:
            return self._data.get(execution_id)


class CallbackServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self._store = _ResultStore()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._server is not None:
            return

        store = self._store

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                return

            def do_POST(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if not parsed.path.startswith("/result/"):
                    self.send_response(404)
                    self.end_headers()
                    return

                execution_id = parsed.path.rsplit("/", 1)[-1]
                content_length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(content_length)
                try:
                    payload = json.loads(body.decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError("payload must be object")
                except Exception:
                    self.send_response(400)
                    self.end_headers()
                    return

                store.put(execution_id, payload)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": true}')

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None

    def await_result(self, execution_id: str, timeout: float) -> dict[str, Any] | None:
        return self._store.wait(execution_id, timeout)


if __name__ == "__main__":
    server = CallbackServer()
    server.start()
    print(f"callback server listening on {server.host}:{server.port}")
    threading.Event().wait()
