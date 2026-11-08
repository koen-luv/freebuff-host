# Freebuff Termux Host Plugin

Host projects **on your phone** with [Termux](https://termux.dev/) — serve static
sites, Node and Python apps on localhost / your Wi-Fi LAN, and optionally get a
public URL with a tunnel. Works with the [Freebuff mobile app](https://freebuff.com/)
and the Freebuff terminal CLI (`npm install -g freebuff`).

No root. No Docker. Python-stdlib only.

## Quick start (on Android)

1. Install [Termux from F-Droid](https://f-droid.org/packages/com.termux/) (not Play Store).
2. Copy this folder to your phone (USB, `adb push`, cloud drive, or `git clone`).
3. In Termux:
   bash install.sh
4. Serve a project:
   freebuff-host serve ~/projects/my-app --detach
   freebuff-host status
   Open `http://127.0.0.1:8000` in your phone browser, or
   `http://<PHONE-LAN-IP>:8000` from any device on the same Wi-Fi.

## Commands

| Command | What it does |
|---|---|
| `freebuff-host serve [path] [--port 8000] [--type auto\|static\|node\|python] [--detach]` | Serve a project (auto-detects type). Detached by default; logs in `~/.freebuff-host/logs/`. |
| `freebuff-host status` | List hosted projects, ports, PIDs, LAN URLs. |
| `freebuff-host stop <name\|port>` | Stop a hosted project. |
| `freebuff-host tunnel [--port 8000] [--provider auto\|cloudflared\|pinggy\|ngrok]` | Public HTTPS URL via tunnel (first available provider). |
| `freebuff-host wakelock acquire\|release` | `termux-wake-lock` so Android doesn't kill the server. |
| `freebuff-host lan-ip` | Print phone's LAN IP. |

Examples:
freebuff-host serve ~/site
freebuff-host serve ~/api --type node --port 3000
freebuff-host serve ~/py-app --type python
freebuff-host tunnel --port 3000

## How it works

Freebuff app / terminal
        │
        ▼  plugin.json → tools: host_serve / host_status / host_stop / host_tunnel / host_wake_lock
bin/freebuff-host  (bash wrapper)
        │
        ▼
src/host.py  (Python stdlib: detect type → spawn server → track PID/port in ~/.freebuff-host/)
        │
        ▼
Termux:  python -m http.server │ npm start │ python app.py
        + termux-services / termux-boot keep-alive (installed by install.sh)
        + cloudflared / pinggy / ngrok for public tunnels

State lives in `~/.freebuff-host/` (`projects.json`, `logs/`, `pids/`).

## Freebuff integration

- `plugin.json` declares the `freebuff-host` command + agent tools
  (`host_serve`, `host_status`, `host_stop`, `host_tunnel`, `host_wake_lock`)
  and the `host-project` skill, so the Freebuff agent can host projects for you
  from the mobile app: *"host this project and give me the link"*.
- The skill (`skills/host-project/SKILL.md`) tells the agent the full workflow:
  detect → serve → verify with curl → report LAN/local URL → tunnel if asked.

## Keep it alive on Android

- Run `freebuff-host wakelock acquire` and keep the phone plugged in.
- Turn **off battery optimization** for Termux (Android Settings → Apps → Termux → Battery → Unrestricted).
- Install the **Termux:Boot** app and grant storage access so `~/.termux/boot/freebuff-host`
  restarts your servers after a reboot.
- Close the "Termux is running in background" notification swipe-guard: don't swipe it away.

## Project structure

plugin.json
install.sh
bin/freebuff-host
src/host.py
skills/host-project/SKILL.md

## Troubleshooting

| Symptom | Fix |
|---|---|
| `command not found: freebuff-host` | Re-run `bash install.sh`, then `hash -r` or reopen Termux. |
| Port already in use | Tool auto-picks the next free port; check `freebuff-host status`. |
| Other devices can't reach it | Must be same Wi-Fi; your server binds `0.0.0.0`. Check phone hotspot client isolation. |
| Server dies when screen off | `freebuff-host wakelock acquire` + disable battery optimization. |
| `cloudflared` not found | `pkg install cloudflared`, or use pinggy/ngrok for tunnels. |
| Node app won't start | Run `npm install` in the project dir first. |

## License

MIT
