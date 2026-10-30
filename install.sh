#!/bin/bash
# Installiert deltraceroute: pip-Abhängigkeiten, globalen Befehl in ~/.local/bin.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER="$HOME/.local/bin/deltraceroute"

echo "=== deltraceroute Installation ==="

if ! command -v traceroute &>/dev/null; then
    echo "WARNUNG: 'traceroute' ist nicht installiert."
    echo "  Debian/Ubuntu: sudo apt install traceroute"
fi

echo "Installiere Python-Abhängigkeiten..."
if ! pip install --user -r "$SCRIPT_DIR/requirements.txt" >/tmp/deltraceroute_pip_err.txt 2>&1; then
    if grep -q "externally-managed-environment" /tmp/deltraceroute_pip_err.txt; then
        echo "System schützt die Python-Umgebung (PEP 668) - installiere mit --break-system-packages..."
        pip install --user --break-system-packages -r "$SCRIPT_DIR/requirements.txt"
    else
        cat /tmp/deltraceroute_pip_err.txt
        exit 1
    fi
fi
rm -f /tmp/deltraceroute_pip_err.txt

echo "Erzeuge globalen Befehl: $WRAPPER"
mkdir -p "$HOME/.local/bin"
cat > "$WRAPPER" << EOF
#!/bin/bash
exec python3 "$SCRIPT_DIR/main.py" "\$@"
EOF
chmod +x "$WRAPPER"

echo ""
if echo "$PATH" | tr ':' '\n' | grep -qxF "$HOME/.local/bin"; then
    echo "Fertig! '$HOME/.local/bin' ist bereits im PATH."
    echo "Direkt loslegen: deltraceroute google.com"
else
    echo "'$HOME/.local/bin' ist noch nicht im PATH - trage es in ~/.bashrc ein..."
    if ! grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    echo "Fertig! Starte die Shell neu oder führe aus: source ~/.bashrc"
    echo "Danach: deltraceroute google.com"
fi
