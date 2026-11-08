# Freebuff Termux Host Plugin

Host projects **on your phone** with [Termux](https://termux.dev/). Serve static sites, Node.js and Python applications on localhost or your Wi-Fi LAN, and optionally expose them to the internet using a tunnel.

Works with the [Freebuff mobile app](https://freebuff.com/) and the Freebuff terminal CLI (`npm install -g freebuff`).

- **No root required**
- **No Docker**
- **Python standard library only**

---

## Quick Start

### 1. Install Termux

Install [Termux from F-Droid](https://f-droid.org/packages/com.termux/).

> Avoid the outdated Google Play Store version.

### 2. Copy the plugin to your phone

Transfer this folder using USB, `adb push`, a cloud drive, or `git clone`.

### 3. Install the plugin

Open Termux and run:

```bash
bash install.sh
```

### 4. Host your project

```bash
freebuff-host serve ~/projects/my-app --detach
freebuff-host status
```

Open your hosted project:

- **On your phone:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **On another device:** `http://<PHONE-LAN-IP>:8000`

Both devices must be connected to the same Wi-Fi network for LAN access.

---

## Commands

| Command | Description |
|---|---|
| `freebuff-host serve [path] [--port 8000] [--type auto\|static\|node\|python] [--detach]` | Host a project. Automatically detects the project type. Detached by default, with logs stored in `~/.freebuff-host/logs/`. |
| `freebuff-host status` | List hosted projects, ports, PIDs, and LAN URLs. |
| `freebuff-host stop <name\|port>` | Stop a hosted project. |
| `freebuff-host tunnel [--port 8000] [--provider auto\|cloudflared\|pinggy\|ngrok]` | Generate a public HTTPS URL using an available tunnel provider. |
| `freebuff-host wakelock acquire\|release` | Acquire or release a Termux wake lock. |
| `freebuff-host lan-ip` | Display the phone's LAN IP address. |

### Examples

**Host a static website:**

```bash
freebuff-host serve ~/site
```

**Host a Node.js application:**

```bash
freebuff-host serve ~/api --type node --port 3000
```

**Host a Python application:**

```bash
freebuff-host serve ~/py-app --type python
```

**Expose a project to the internet:**

```bash
freebuff-host tunnel --port 3000
```

---

## How It Works

```text
Freebuff App / Terminal CLI
          │
          ▼
    plugin.json
    ├── host_serve
    ├── host_status
    ├── host_stop
    ├── host_tunnel
    └── host_wake_lock
          │
          ▼
    bin/freebuff-host
       (Bash wrapper)
          │
          ▼
      src/host.py
    (Python standard library)
          │
          ├── Detect project type
          ├── Spawn server processes
          └── Track PID and port
          │
          ▼
       Termux
          │
          ├── python -m http.server
          ├── npm start
          └── python app.py
          │
          ├── termux-services / termux-boot
          │   └── Keep servers running
          │
          └── Tunnel providers
              ├── cloudflared
              ├── pinggy
              └── ngrok
```

### State and Storage

All plugin state is stored in:

```text
~/.freebuff-host/
├── projects.json
├── logs/
└── pids/
```

---

## Freebuff Integration

The plugin integrates directly with Freebuff through `plugin.json`.

### Agent Tools

| Tool | Purpose |
|---|---|
| `host_serve` | Start hosting a project. |
| `host_status` | Check currently hosted projects. |
| `host_stop` | Stop a hosted project. |
| `host_tunnel` | Create a public tunnel. |
| `host_wake_lock` | Manage Android wake locks. |

The plugin also provides the `host-project` skill, allowing the Freebuff agent to host projects directly from the mobile app.

For example:

> "Host this project and give me the link."

### Agent Workflow

The skill at `skills/host-project/SKILL.md` guides the agent through:

1. Detecting the project type.
2. Starting the appropriate server.
3. Verifying the server using `curl`.
4. Reporting the localhost and LAN URLs.
5. Creating a public tunnel if requested.

---

## Keeping Servers Alive on Android

Android aggressively manages background processes. Follow these steps to improve reliability.

### 1. Acquire a wake lock

```bash
freebuff-host wakelock acquire
```

Keep your phone plugged in while hosting.

### 2. Disable battery optimization

Navigate to:

**Android Settings → Apps → Termux → Battery → Unrestricted**

This prevents Android from aggressively restricting Termux.

### 3. Enable automatic startup

Install the **Termux:Boot** app and grant the necessary storage permissions.

The plugin uses:

```text
~/.termux/boot/freebuff-host
```

to restart your servers after a reboot.

### 4. Keep Termux running

Avoid swiping away Termux's persistent background notification, as this can interfere with background execution.

---

## Project Structure

```text
freebuff-termux-host/
├── plugin.json
├── install.sh
├── bin/
│   └── freebuff-host
├── src/
│   └── host.py
└── skills/
    └── host-project/
        └── SKILL.md
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `command not found: freebuff-host` | Re-run `bash install.sh`, then execute `hash -r` or reopen Termux. |
| Port already in use | The plugin automatically selects the next available port. Check `freebuff-host status`. |
| Other devices cannot access the server | Ensure both devices are on the same Wi-Fi network. The server must bind to `0.0.0.0`. Check for hotspot client isolation. |
| Server stops when the screen turns off | Run `freebuff-host wakelock acquire` and disable battery optimization for Termux. |
| `cloudflared` not found | Install it using `pkg install cloudflared`, or use Pinggy or ngrok. |
| Node.js application fails to start | Run `npm install` inside the project directory first. |

---

## License

This project is licensed under the [MIT License](LICENSE).
