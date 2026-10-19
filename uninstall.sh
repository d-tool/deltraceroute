#!/bin/bash
# Entfernt deltracemap wieder: globalen Befehl, Cache und generierte Karten.
# Das Projektverzeichnis selbst (Quellcode) wird NICHT gelöscht.

set -e

WRAPPER="$HOME/.local/bin/deltracemap"
CACHE_DIR="$HOME/.cache/deltracemap"
DOWNLOADS_DIR="$HOME/Downloads/deltracemap"

echo "=== deltracemap Deinstallation ==="

if [[ -f "$WRAPPER" ]]; then
    rm -f "$WRAPPER"
    echo "Entfernt: $WRAPPER"
else
    echo "Nicht gefunden (bereits entfernt?): $WRAPPER"
fi

if [[ -d "$CACHE_DIR" ]]; then
    rm -rf "$CACHE_DIR"
    echo "Entfernt: $CACHE_DIR (GeoIP-Cache)"
fi

if [[ -d "$DOWNLOADS_DIR" ]]; then
    read -r -p "Generierte Karten in $DOWNLOADS_DIR löschen? [j/N] " antwort
    if [[ "$antwort" =~ ^[jJ]$ ]]; then
        rm -rf "$DOWNLOADS_DIR"
        echo "Entfernt: $DOWNLOADS_DIR"
    else
        echo "Übersprungen: $DOWNLOADS_DIR"
    fi
fi

echo ""
echo "Fertig. Das Projektverzeichnis (Quellcode) wurde nicht angerührt."
echo "Falls gewünscht, kannst du es manuell löschen oder per pip die Pakete entfernen:"
echo "  pip uninstall requests rich plotext folium"
