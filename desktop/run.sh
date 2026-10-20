#!/usr/bin/env bash
# Runner for paste, write. Desktop Edition
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=================================================="
echo " 📋 paste, write. — Universal Input Typist"
echo "=================================================="

export LD_LIBRARY_PATH="${HOME}/.local/lib:${LD_LIBRARY_PATH}"

# Check for DISPLAY
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

# Locate Xwayland authority if not set
if [ -z "$XAUTHORITY" ]; then
    AUTH_FILE=$(ls -t /run/user/$(id -u)/.*Xwaylandauth* 2>/dev/null | head -n 1 || true)
    if [ -n "$AUTH_FILE" ]; then
        export XAUTHORITY="$AUTH_FILE"
    elif [ -f "$HOME/.Xauthority" ]; then
        export XAUTHORITY="$HOME/.Xauthority"
    fi
fi

chmod +x pastewrite.py
if command -v python3.12 >/dev/null 2>&1; then
    exec python3.12 "${DIR}/pastewrite.py" "$@"
else
    exec python3 "${DIR}/pastewrite.py" "$@"
fi
