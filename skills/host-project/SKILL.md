# Host a project on Termux

Use when the user wants to run/serve/host a project from their Android phone.

## Workflow

1. **Check environment** (Termux): `termux-info`, `pkg list-installed | grep -E 'python|node'`
2. **Locate project**: default to cwd; `ls` to confirm entry point (`index.html`, `package.json`, `app.py`, `main.py`).
3. **Serve it** — prefer detached so the agent can keep working:
   freebuff-host serve <path> --detach
   freebuff-host serve <path> --port 8000 --type auto --detach
   Type auto-detection: `package.json` → node, `requirements.txt`/`app.py` → python, else static.
4. **Verify**: `freebuff-host status`, then `curl -s http://127.0.0.1:<port> | head`
   Give the user both URLs: `http://127.0.0.1:<port>` (on phone) and `http://<LAN-IP>:<port>` (same Wi-Fi).
5. **Keep alive** (if long-running): `termux-wake-lock` (via `freebuff-host wakelock acquire`),
   disable battery optimization for Termux, keep phone plugged in.
6. **Public URL** (optional): `freebuff-host tunnel --port <port>`
   Providers tried in order: cloudflared → pinggy → ngrok. Share the printed URL.
7. **Stop**: `freebuff-host stop <name|port>`; logs: `tail -f ~/.freebuff-host/logs/<name>-<port>.log`

## Rules
- Bind `0.0.0.0` by default so LAN devices can reach it; use `127.0.0.1` only for phone-only.
- Never expose a tunnel on an untrusted network without warning the user.
- One port per project; the tool auto-picks from 8000 if taken.
- If Node deps are missing: `npm install` (or `pnpm install`) first, then re-serve.

## Tool equivalents (Freebuff agent)
`host_serve` = `freebuff-host serve`, `host_status` = `status`,
`host_stop` = `stop`, `host_tunnel` = `tunnel`, `host_wake_lock` = `wakelock`.
