#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, shutil, signal, socket, subprocess, sys, time
from pathlib import Path

HOME = Path(os.environ.get("PREFIX", "")) / "files" / "home" if os.environ.get("PREFIX") else Path.home()
STATE_DIR = HOME / ".freebuff-host"
STATE_FILE = STATE_DIR / "projects.json"
LOG_DIR = STATE_DIR / "logs"
PID_DIR = STATE_DIR / "pids"

def lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_state(state: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) != 0

def find_free_port(start: int = 8000) -> int:
    p = start
    while p < start + 200:
        if port_free(p):
            return p
        p += 1
    raise RuntimeError("no free port in range")

def detect_type(path: Path) -> str:
    if (path / "package.json").exists():
        pkg = {}
        try:
            pkg = json.loads((path / "package.json").read_text())
        except Exception:
            pass
        scripts = pkg.get("scripts", {})
        if "dev" in scripts or "start" in scripts:
            return "node"
        if (path / "dist" / "index.html").exists() or (path / "index.html").exists():
            return "static"
        return "node"
    if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists() \
       or (path / "app.py").exists() or (path / "main.py").exists():
        return "python"
    return "static"

def build_cmd(path: Path, kind: str, port: int, host: str) -> list[str]:
    if kind == "static":
        return [sys.executable, "-m", "http.server", str(port), "--bind", host]
    if kind == "node":
        return ["node", "server.js"] if (path / "server.js").exists() else ["npm", "start"]
    if kind == "python":
        if (path / "app.py").exists():
            return [sys.executable, "app.py"]
        if (path / "main.py").exists():
            return [sys.executable, "main.py"]
        return [sys.executable, "-m", "http.server", str(port), "--bind", host]
    raise ValueError(kind)

def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False

def wait_ready(port: int, timeout: float = 8.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.3)
    return False

def cmd_serve(args) -> int:
    path = Path(args.path or os.getcwd()).resolve()
    if not path.is_dir():
        print(f"error: not a directory: {path}", file=sys.stderr)
        return 1
    kind = args.type if args.type != "auto" else detect_type(path)
    port = args.port or find_free_port(8000)
    if not port_free(port):
        print(f"warning: port {port} already in use, picking next free port")
        port = find_free_port(port + 1)
    host = args.host
    name = re.sub(r"[^a-z0-9-]", "-", path.name.lower()) or "project"

    env = dict(os.environ, PORT=str(port), HOST=host)
    cmd = build_cmd(path, kind, port, host)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PID_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{name}-{port}.log"
    pid_path = PID_DIR / f"{name}-{port}.pid"

    print(f"Hosting {path.name} ({kind}) on http://{lan_ip()}:{port}  (localhost: http://127.0.0.1:{port})")
    print(f"  dir={path}  log={log_path}")

    if args.detach:
        log = open(log_path, "ab")
        proc = subprocess.Popen(cmd, cwd=path, env=env, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        pid_path.write_text(str(proc.pid))
        state = load_state()
        state[f"{name}:{port}"] = {
            "name": name, "path": str(path), "type": kind,
            "port": port, "host": host, "pid": proc.pid,
            "log": str(log_path), "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "url_local": f"http://127.0.0.1:{port}",
            "url_lan": f"http://{lan_ip()}:{port}",
        }
        save_state(state)
        if wait_ready(port):
            print(f"  [ok] ready - open on phone: http://127.0.0.1:{port}  | LAN: http://{lan_ip()}:{port}")
        else:
            print(f"  [!] not responding yet, check log: tail -f {log_path}", file=sys.stderr)
        return 0
    else:
        print("  (foreground — Ctrl+C to stop)")
        try:
            subprocess.run(cmd, cwd=path, env=env)
        except KeyboardInterrupt:
            pass
        return 0

def cmd_status(_args) -> int:
    state = load_state()
    if not state:
        print("No projects hosted yet. Start one:  freebuff-host serve [path]")
        return 0
    print(f"{'NAME':<20} {'TYPE':<8} {'PORT':<6} {'PID':<8} {'STATUS'}")
    for key, p in sorted(state.items(), key=lambda kv: kv[1].get("port", 0)):
        alive = pid_alive(p.get("pid", 0)) if p.get("pid") else False
        status = "running" if alive else "stopped"
        print(f"{p.get('name',''):<20} {p.get('type',''):<8} {p.get('port',''):<6} {p.get('pid',''):<8} {status}")
        if alive:
            print(f"  -> {p.get('url_lan')}  (log: {p.get('log')})")
    return 0

def cmd_stop(args) -> int:
    state = load_state()
    target = args.target
    found = None
    for key, p in state.items():
        if target in (p.get("name"), str(p.get("port")), key):
            found = (key, p)
            break
    if not found:
        print(f"error: no hosted project matching '{target}'", file=sys.stderr)
        return 1
    key, p = found
    pid = p.get("pid")
    if pid and pid_alive(pid):
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        print(f"Stopped {p['name']} (pid {pid}, port {p['port']})")
    else:
        print(f"{p['name']} already stopped")
    del state[key]
    save_state(state)
    return 0

def _which(name: str) -> bool:
    return shutil.which(name) is not None

def cmd_tunnel(args) -> int:
    port = args.port
    prov = args.provider
    candidates = []
    if prov in ("auto", "cloudflared"):
        candidates.append(("cloudflared", ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]))
    if prov in ("auto", "pinggy"):
        candidates.append(("pinggy", ["pinggy", "-p", str(port)]))
    if prov in ("auto", "ngrok"):
        candidates.append(("ngrok", ["ngrok", "http", str(port)]))
    for name, cmd in candidates:
        if _which(cmd[0]):
            print(f"Starting {name} tunnel for port {port} — Ctrl+C to stop")
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                pass
            return 0
    print("error: no tunnel provider found. Install one:", file=sys.stderr)
    print("  pkg install cloudflared", file=sys.stderr)
    return 1

def cmd_wakelock(args) -> int:
    if shutil.which("termux-wake-lock") is None:
        print("termux-wake-lock not found (install termux-api). Skipping.", file=sys.stderr)
        return 0
    cmd = "termux-wake-lock" if args.action == "acquire" else "termux-wake-unlock"
    subprocess.run([cmd], check=False)
    print(f"Wake lock {args.action} sent")
    return 0

def main() -> int:
    ap = argparse.ArgumentParser(prog="freebuff-host", description="Host projects on Termux")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("serve", help="serve a project")
    s.add_argument("path", nargs="?", help="project directory (default: cwd)")
    s.add_argument("--port", type=int, default=0, help="port (default: auto from 8000)")
    s.add_argument("--host", default="0.0.0.0", help="bind host (default: 0.0.0.0 = LAN)")
    s.add_argument("--type", choices=["auto", "static", "node", "python"], default="auto")
    s.add_argument("--detach", action="store_true", default=True, help="run in background (default)")
    s.add_argument("--foreground", dest="detach", action="store_false", help="run in foreground")
    s.set_defaults(fn=cmd_serve)

    sub.add_parser("status", help="list hosted projects").set_defaults(fn=cmd_status)

    st = sub.add_parser("stop", help="stop a hosted project")
    st.add_argument("target", help="project name or port")
    st.set_defaults(fn=cmd_stop)

    t = sub.add_parser("tunnel", help="expose port publicly")
    t.add_argument("--port", type=int, default=8000)
    t.add_argument("--provider", choices=["auto", "cloudflared", "pinggy", "ngrok"], default="auto")
    t.set_defaults(fn=cmd_tunnel)

    w = sub.add_parser("wakelock", help="termux wake lock")
    w.add_argument("action", choices=["acquire", "release"])
    w.set_defaults(fn=cmd_wakelock)

    sub.add_parser("lan-ip", help="print LAN IP").set_defaults(
        fn=lambda _a: (print(lan_ip()), 0)[1])

    args = ap.parse_args()
    return args.fn(args)

if __name__ == "__main__":
    raise SystemExit(main())
