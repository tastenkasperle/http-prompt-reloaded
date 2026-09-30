"""
HTTP Prompt Reloaded MCP Server: Stdio-basierter JSON-RPC 2.0 Server.
Ermöglicht autonomen KI-Agenten die stateful API-Navigation und Tests.
Anti-Carbonara Standard: Pure Core Integration.
"""

import sys
import json
import logging
from src.core.engine import SessionContext, RequestExecutor

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s [%(levelname)s] %(message)s")


class HTTPPromptMCPServer:
    def __init__(self):
        self.sessions: dict[str, SessionContext] = {}
        self.default_session = SessionContext()
        self.tools = [
            {
                "name": "http_prompt_init",
                "description": "Initializes or updates a stateful HTTP exploration session.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "default": "default"},
                        "base_url": {"type": "string", "description": "Base URL like http://localhost:8080"}
                    },
                    "required": ["base_url"]
                }
            },
            {
                "name": "http_prompt_cd",
                "description": "Navigates the API URL path like a directory (e.g., 'cd /api/v1', 'cd users', 'cd ..').",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "default": "default"},
                        "path": {"type": "string", "description": "Relative or absolute API path"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "http_prompt_configure",
                "description": "Sets persistent headers or query parameters for the session.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "default": "default"},
                        "headers": {"type": "object", "description": "Key-value headers to set"},
                        "params": {"type": "object", "description": "Key-value query parameters to set"}
                    }
                }
            },
            {
                "name": "http_prompt_execute",
                "description": "Executes an HTTP request on the current stateful path.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "default": "default"},
                        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"], "default": "GET"},
                        "body": {"type": "object", "description": "Optional JSON payload"}
                    }
                }
            }
        ]

    def _get_session(self, session_id: str) -> SessionContext:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionContext()
        return self.sessions[session_id]

    def handle_request(self, req: dict) -> dict:
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.tools}
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            session_id = args.get("session_id", "default")
            sess = self._get_session(session_id)

            try:
                if tool_name == "http_prompt_init":
                    sess.base_url = args.get("base_url").rstrip("/")
                    sess.current_path = "/"
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": f"Session '{session_id}' initialized at {sess.base_url}"}]}
                    }

                elif tool_name == "http_prompt_cd":
                    new_url = sess.cd(args.get("path", "/"))
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": f"Current path: {sess.current_path} -> URL: {new_url}"}]}
                    }

                elif tool_name == "http_prompt_configure":
                    headers = args.get("headers", {})
                    for k, v in headers.items():
                        sess.set_header(k, str(v))
                    params_dict = args.get("params", {})
                    for k, v in params_dict.items():
                        sess.set_param(k, str(v))
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": f"Session '{session_id}' configured."}]}
                    }

                elif tool_name == "http_prompt_execute":
                    method = args.get("method", "GET")
                    body = args.get("body", None)
                    res = RequestExecutor.execute(sess, method=method, override_body=body)
                    output = {
                        "status": res.status_code,
                        "method": res.method,
                        "url": res.url,
                        "time_ms": res.execution_time_ms,
                        "headers": res.headers,
                        "body": res.body
                    }
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": json.dumps(output, indent=2)}]}
                    }

                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method {tool_name} not found"}
                    }

            except Exception as e:
                logging.exception(f"Error executing tool {tool_name}")
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)}
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32600, "message": "Invalid Request"}
        }

    def run(self):
        logging.info("HTTP Prompt MCP Server running on stdio.")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception:
                pass


if __name__ == "__main__":
    server = HTTPPromptMCPServer()
    server.run()
