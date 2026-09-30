"""
HTTP Prompt Reloaded Core Engine: Stateful API Session & Execution.
Pure Python, Zero External Dependencies, 100% In-Memory.
Anti-Carbonara: Pure Logic, No CLI, No print(), No sys.exit().
"""

import urllib.request
import urllib.parse
import json
from typing import Dict, Any, List, Optional, NamedTuple


class ExecutionResult(NamedTuple):
    status_code: int
    headers: Dict[str, str]
    body: str
    url: str
    method: str
    execution_time_ms: float


class SessionContext:
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url.rstrip("/")
        self.current_path = "/"
        self.headers: Dict[str, str] = {
            "User-Agent": "HTTP-Prompt-Reloaded/1.0",
            "Accept": "application/json, text/plain, */*"
        }
        self.query_params: Dict[str, str] = {}
        self.body_data: Optional[Dict[str, Any]] = None

    def cd(self, path: str) -> str:
        """Navigates the API URL structure like a file system directory."""
        path = path.strip()
        if not path:
            return self.get_full_url()

        if path.startswith("/"):
            self.current_path = path
        elif path == "..":
            parts = [p for p in self.current_path.strip("/").split("/") if p]
            if parts:
                parts.pop()
            self.current_path = "/" + "/".join(parts) if parts else "/"
        else:
            if not self.current_path.endswith("/"):
                self.current_path += "/"
            self.current_path += path

        # Clean multiple slashes
        clean_parts = [p for p in self.current_path.split("/") if p]
        self.current_path = "/" + "/".join(clean_parts) if clean_parts else "/"
        return self.get_full_url()

    def set_header(self, key: str, value: str):
        self.headers[key.strip()] = value.strip()

    def remove_header(self, key: str):
        self.headers.pop(key.strip(), None)

    def set_param(self, key: str, value: str):
        self.query_params[key.strip()] = value.strip()

    def remove_param(self, key: str):
        self.query_params.pop(key.strip(), None)

    def set_body(self, data: Dict[str, Any]):
        self.body_data = data

    def clear_body(self):
        self.body_data = None

    def get_full_url(self) -> str:
        url = self.base_url + self.current_path
        if self.query_params:
            qs = urllib.parse.urlencode(self.query_params)
            url += f"?{qs}"
        return url


class RequestExecutor:
    @staticmethod
    def execute(context: SessionContext, method: str = "GET", override_body: Optional[Any] = None) -> ExecutionResult:
        import time
        method = method.upper()
        url = context.get_full_url()

        data_bytes = None
        headers = dict(context.headers)

        payload = override_body if override_body is not None else context.body_data
        if payload is not None:
            if isinstance(payload, (dict, list)):
                data_bytes = json.dumps(payload).encode("utf-8")
                headers["Content-Type"] = "application/json"
            elif isinstance(payload, str):
                data_bytes = payload.encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                status_code = resp.status
                resp_headers = dict(resp.getheaders())
                raw_body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            status_code = e.code
            resp_headers = dict(e.headers)
            raw_body = e.read().decode("utf-8", errors="replace")
        except Exception as e:
            status_code = 599
            resp_headers = {}
            raw_body = f"Network or Connection Error: {str(e)}"

        duration_ms = (time.perf_counter() - start) * 1000.0

        return ExecutionResult(
            status_code=status_code,
            headers=resp_headers,
            body=raw_body,
            url=url,
            method=method,
            execution_time_ms=round(duration_ms, 2)
        )
