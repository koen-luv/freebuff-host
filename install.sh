#!/usr/bin/env bash
set -euo pipefail
PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${PREFIX:-$HOME/.termux}/bin"
if [ -n "${PREFIX:-}" ]; then BIN_DIR="$PREFIX/bin"; else BIN_DIR="$HOME/.local/bin"; fi
mkdir -p "$BIN_DIR"

echo "==> Installing freebuff-termux-host from $PLUGIN_DIR"
ln -sf "$PLUGIN_DIR/bin/freebuff-host" "$BIN_DIR/freebuff-host"
chmod +x "$PLUGIN_DIR/bin/freebuff-host" "$PLUGIN_DIR/src/host.py"

if [ "${1:-}" != "--no-deps" ]; then
  echo "==> Installing Termux packages (python, node, termux-services, cloudflared if available)"
  pkg update -y || true
  pkg install -y python nodejs termux-services termux-api git || \
    pkg install -y python nodejs git
  pkg install -y cloudflared 2>/dev/null || echo "  (cloudflared not in repo — use pinggy/ngrok, or skip tunnel)"
fi
if command -v sv >/dev/null 2>&1; then
  mkdir -p "$HOME/.termux/service/freebuff-host"
  cat > "$HOME/.termux/service/freebuff-host/run" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
exec $HOME/freebuff-termux-host/bin/freebuff-host status >/dev/null 2>&1 || true
exec sleep infinity
EOF
  chmod +x "$HOME/.termux/service/freebuff-host/run"
  echo "  termux-services entry created"
fi
if [ -d "$HOME/.termux/boot" ] || command -v termux-setup-storage >/dev/null 2>&1; then
  mkdir -p "$HOME/.termux/boot"
  cat > "$HOME/.termux/boot/freebuff-host" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock 2>/dev/null || true
$BIN_DIR/freebuff-host status >/dev/null 2>&1 || true
EOF
  chmod +x "$HOME/.termux/boot/freebuff-host"
  echo "  termux-boot script created (install Termux:Boot app to enable)"
fi

echo ""
echo "Done. Try:"
echo "  freebuff-host serve ~/projects/my-app --detach"
echo "  freebuff-host status"
echo "  freebuff-host tunnel --port 8000"
