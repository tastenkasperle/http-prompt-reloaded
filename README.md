# 🌐 HTTP Prompt Reloaded

[![PyPI version](https://img.shields.io/pypi/v/http-prompt-reloaded.svg?color=blue)](https://pypi.org/project/http-prompt-reloaded/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Glama Score](https://glama.ai/mcp/servers/tastenkasperle/http-prompt-reloaded/badges/score.svg)](https://glama.ai/mcp/servers/tastenkasperle/http-prompt-reloaded)
[![MCP Protocol](https://img.shields.io/badge/MCP-2025--09--29-brightgreen.svg)](https://modelcontextprotocol.io/)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Pure%20Python)-brightgreen.svg)]()
[![Raptor Guard Certified](https://img.shields.io/badge/SAST%20Audit-0%20Vulnerabilities-success.svg)]()
[![WDAS Agent Ready](https://img.shields.io/badge/WDAS%20Audit-Grade%20A%20(Agentic)-purple.svg)]()

> **Stateful Interactive API Navigation & Agentic MCP Engine.**  
> *The legendary 9.1k-star CLI REPL resurrected for modern Python (3.10–3.13) and upgraded into an autonomous AI Agent tool.*

---

## ⚡ What is HTTP Prompt Reloaded?

Modern API exploration is broken: developers drown in bloated Electron apps (Postman/Insomnia) or struggle with massive, fragile cURL commands. The original `httpie/http-prompt` was brilliant, but broke down under ancient `prompt_toolkit < 2.0` constraints.

**HTTP Prompt Reloaded** revives this concept as a **zero-dependency, pure Python engine** that bridges human developers and autonomous AI agents:

1. **Navigate APIs like a File System:** `cd /api/v1/users`, `cd 42`, `cd ..`
2. **Persistent Session Context:** Headers (Bearer tokens, cookies) and query parameters persist across requests.
3. **Dual Operation:**
   - **Interactive CLI REPL** for human terminal power users.
   - **Native Model Context Protocol (MCP)** JSON-RPC 2.0 Server for AI Agents (Claude Desktop, Cursor, Antigravity, Open-WebUI).
4. **Hardened Security:** Built-in SSRF protection (blocks cloud metadata endpoints like `169.254.169.254`), CRLF header injection guards, and canonical URL traversal sanitization.

---

## 📦 Installation

```bash
# Via pip
pip install http-prompt-reloaded

# Or run instantly via uv / pipx
uvx http-prompt-reloaded http://localhost:8080
```

---

## 🚀 Human CLI Quickstart

```bash
# Start an interactive session on your API
http-prompt-reloaded https://api.github.com

# In the prompt:
/> cd /users/tastenkasperle
/users/tastenkasperle> header User-Agent MyDevAgent/1.0
/users/tastenkasperle> get
--> 200 https://api.github.com/users/tastenkasperle (112ms)
{
  "login": "tastenkasperle",
  ...
}

/users/tastenkasperle> cd /repos
/repos> param sort updated
/repos> get
```

---

## 🤖 MCP Integration for AI Agents

Give your AI coding assistants the power to test, explore, and debug live REST APIs with memory instead of spitting out static cURL strings!

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "http-prompt": {
      "command": "python",
      "args": ["-m", "src.mcp.server"]
    }
  }
}
```

### Provided MCP Tools

| Tool | Purpose |
| :--- | :--- |
| `http_prompt_init` | Initialize or update a stateful session with a target `base_url`. |
| `http_prompt_cd` | Move through API endpoints hierarchically (`cd /api/v1`, `cd ..`). |
| `http_prompt_configure`| Set persistent headers (e.g. `Authorization: Bearer ...`) or query params. |
| `http_prompt_execute` | Execute an HTTP method (`GET`, `POST`, `PUT`, `DELETE`) with optional payload. |

---

## 🧪 Testing & Verification

Hermetic tests run in sub-second time without external network access using an ephemeral local test server:

```bash
python -m unittest discover tests
```

---

## 🛡️ License

MIT License. Based on the concept of `httpie/http-prompt` (9.1k Stars).
