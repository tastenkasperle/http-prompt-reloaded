"""
HTTP Prompt Reloaded Core Engine: Stateful API Session & Execution.
Pure Python, Zero External Dependencies, 100% In-Memory.
Anti-Carbonara: Pure Logic, No CLI, No print(), No sys.exit().
"""

import urllib.request
import urllib.parse
import json
import re
from typing import Dict, Any, List, Optional, NamedTuple


class SecurityError(ValueError):
    """Raised when security boundaries (SSRF, CRLF injection, invalid scheme) are breached."""
    pass


class ExecutionResult(NamedTuple):
    status_code: int
    headers: Dict[str, str]
    body: str
    url: str
    method: str
    execution_time_ms: float


class SessionContext:
    # Regex to detect CRLF header injection attempts
    CRLF_REGEX = re.compile(r"[\r\n]")

    # Blocked dangerous cloud metadata addresses for SSRF protection
    BLOCKED_HOSTS = {
        "169.254.169.254",   # AWS/GCP/Azure link-local metadata
        "metadata.google.internal",
        "instance-data"
    }

    def __init__(self, base_url: str = "http://localhost", allow_private_networks: bool = True):
        self.allow_private_networks = allow_private_networks
        self.base_url = self._validate_and_sanitize_url(base_url)
        self.current_path = "/"
        self.headers: Dict[str, str] = {
            "User-Agent": "HTTP-Prompt-Reloaded/1.0",
            "Accept": "application/json, text/plain, */*"
        }
        self.query_params: Dict[str, str] = {}
        self.body_data: Optional[Dict[str, Any]] = None

    def _validate_and_sanitize_url(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url.strip())
        if parsed.scheme.lower() not in ("http", "https"):
            raise SecurityError(f"Unsupported or dangerous URL scheme: '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

        host = (parsed.hostname or "").lower()
        if host in self.BLOCKED_HOSTS:
            raise SecurityError(f"SSRF Protection: Requests to cloud metadata endpoint '{host}' are forbidden.")

        return url.rstrip("/")

    def cd(self, path: str) -> str:
        """Navigates the API URL structure like a file system directory."""
        path = path.strip()
        if not path:
            return self.get_full_url()

        # Sanitize against path traversal escapes
        # Decode first to catch encoded traversal like %2e%2e
        unquoted = urllib.parse.unquote(path)

        if unquoted.startswith("/"):
            self.current_path = unquoted
        elif unquoted == "..":
            parts = [p for p in self.current_path.strip("/").split("/") if p]
            if parts:
                parts.pop()
            self.current_path = "/" + "/".join(parts) if parts else "/"
        else:
            if not self.current_path.endswith("/"):
                self.current_path += "/"
            self.current_path += unquoted

        # Clean redundant or traversal parts safely
        clean_parts: List[str] = []
        for segment in self.current_path.split("/"):
            if not segment or segment == ".":
                continue
            if segment == "..":
                if clean_parts:
                    clean_parts.pop()
            else:
                clean_parts.append(segment)

        self.current_path = "/" + "/".join(clean_parts) if clean_parts else "/"
        return self.get_full_url()

    def set_header(self, key: str, value: str):
        key = key.strip()
        value = value.strip()
        if self.CRLF_REGEX.search(key) or self.CRLF_REGEX.search(value):
            raise SecurityError("Header Injection Detected: Header keys and values must not contain CRLF characters (\\r or \\n).")
        self.headers[key] = value

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
