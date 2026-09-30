"""
HTTP Prompt Reloaded CLI: Interactive and Batch REPL.
Anti-Carbonara: Thin CLI wrapper around src.core.engine.
"""

import sys
import argparse
import json
from src.core.engine import SessionContext, RequestExecutor


def main() -> int:
    parser = argparse.ArgumentParser(description="HTTP Prompt Reloaded - Stateful API Exploration")
    parser.add_argument("base_url", nargs="?", default="http://localhost", help="Target Base URL")
    parser.add_argument("--exec", help="Run a single command like 'cd /users && GET'", default=None)
    args = parser.parse_args()

    session = SessionContext(base_url=args.base_url)

    if args.exec:
        parts = [p.strip() for p in args.exec.split("&&")]
        for part in parts:
            if part.startswith("cd "):
                session.cd(part[3:])
            elif part.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"]:
                res = RequestExecutor.execute(session, method=part)
                print(f"[{res.status_code}] {res.method} {res.url} ({res.execution_time_ms}ms)")
                print(res.body)
        return 0

    print(f"HTTP Prompt Reloaded [Target: {session.base_url}]")
    print("Commands: cd <path> | header <k> <v> | param <k> <v> | get | post | exit")

    while True:
        try:
            line = input(f"{session.current_path}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting HTTP Prompt.")
            break

        if not line:
            continue
        if line.lower() in ["exit", "quit", "q"]:
            break

        tokens = line.split()
        cmd = tokens[0].lower()

        if cmd == "cd":
            target = tokens[1] if len(tokens) > 1 else "/"
            session.cd(target)
        elif cmd == "header" and len(tokens) >= 3:
            session.set_header(tokens[1], " ".join(tokens[2:]))
        elif cmd == "param" and len(tokens) >= 3:
            session.set_param(tokens[1], " ".join(tokens[2:]))
        elif cmd in ["get", "post", "put", "delete", "patch", "head"]:
            res = RequestExecutor.execute(session, method=cmd)
            print(f"--> {res.status_code} {res.url} ({res.execution_time_ms}ms)")
            try:
                formatted = json.dumps(json.loads(res.body), indent=2)
                print(formatted)
            except Exception:
                print(res.body)
        else:
            print(f"Unknown command: {cmd}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
