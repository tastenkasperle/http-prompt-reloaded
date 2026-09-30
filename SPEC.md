# SPEC: HTTP Prompt Reloaded (Stateful Interactive API REPL & MCP Engine)
**Status:** In Schmiede (Gang 1 - Architektur & Spezifikation)  
**Basis:** `httpie/http-prompt` (9.1k Stars, MIT)  
**Standard:** Anti-Carbonara Pure Clean Code & AYA-Protokoll

---

## 1. Vision & Core Value Proposition
HTTP Prompt Reloaded belebt das legendäre 9.1k-Sterne CLI-Werkzeug wieder und befreit es von den antiken Abhängigkeiten (`prompt_toolkit < 2.0`).
- **Problem:** Entwickler ersticken in trägen Postman- oder Electron-GUIs. Die originale HTTP-Prompt-Version bricht auf modernem Python (3.10-3.13) sofort mit Dependency-Fehlern ab.
- **Lösung:** Headless-fähige, moderne HTTP-State-Engine:
  - Navigation durch APIs wie im Dateisystem (`cd /api/v1/users`, `cd 42`).
  - Zustandserhalt von Base-URL, Headers, Bearer-Tokens und Query-Params über Sessions hinweg.
  - Native Stdio-basierte JSON-RPC 2.0 MCP-Schnittstelle für KI-Agenten zum interaktiven API-Debugging.
- **Anti-Carbonara Doktrin:**
  - `src/core/`: Reine Zustands- und HTTP-Logik (`SessionContext`, `UrlNavigator`, `RequestExecutor`), 0 CLI-Prints, 0 `sys.exit()`.
  - `src/cli/`: Dünne interaktive REPL-Schicht für das Terminal.
  - `src/mcp/`: Nativer MCP-Server (`http_prompt_session`, `http_prompt_cd`, `http_prompt_exec`).
  - `tests/`: 100% hermetische Unittests & Fire Team Elite Pen-Tests.
