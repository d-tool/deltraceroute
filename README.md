# deltracemap

Ein Visual-Traceroute-Klon für das Terminal - geschrieben mit Claude: Hop-Tabelle mit GeoIP-Infos, ASCII-Koordinatenkarte direkt im Terminal (via `plotext`), optional eine interaktive HTML-Karte im Browser (via `folium`).

## Voraussetzungen

| Was | Version / Hinweis |
|---|---|
| Python | 3.10 oder neuer (nutzt `X \| None` Type-Hints, `dataclass`) |
| `traceroute` (System-Binary) | unter Debian/Ubuntu via `apt install traceroute` |
| pip-Pakete | siehe `requirements.txt`: `requests`, `rich`, `plotext==5.3.2`, `folium` |
| Internetzugang | für `traceroute` selbst und für die GeoIP-Abfrage (ip-api.com) |

Kein `sudo`/root nötig – `traceroute` läuft unter Linux standardmäßig im UDP-Modus ohne erhöhte Rechte.

**Wichtig zur `plotext`-Version:** Es wird bewusst `plotext==5.3.2` gepinnt. Neuere Versionen (ab 6.0) haben die interne API komplett umgebaut und stellen die hier genutzten Funktionen (`scatter`, `plot`, `text`, `clf`, ...) nicht mehr unter denselben Namen bereit.

## Installation

```bash
sudo apt install traceroute   # falls noch nicht vorhanden
git clone <repo-url> deltracemap
cd deltracemap
bash install.sh
```

`install.sh` installiert die pip-Abhängigkeiten und richtet den globalen Befehl `deltracemap` in `~/.local/bin/` ein – das ist der Standard-Ort für benutzerspezifische Programme unter Linux und liegt bei den meisten Distributionen (inkl. Ubuntu) bereits im `PATH`. Falls nicht, gibt das Skript die passende Zeile für `~/.bashrc` aus.

Danach einfach von überall:
```bash
deltracemap google.com
deltracemap 8.8.8.8 --gui
```

### Manuelle Installation (ohne install.sh)

```bash
pip install --user -r requirements.txt
mkdir -p ~/.local/bin
cat > ~/.local/bin/deltracemap << 'EOF'
#!/bin/bash
exec python3 "/pfad/zu/deinem/deltracemap/main.py" "$@"
EOF
chmod +x ~/.local/bin/deltracemap
```
Pfad in der zweiten Zeile auf deinen tatsächlichen Klon-Ort anpassen.

### Deinstallation

```bash
bash uninstall.sh
```

Entfernt den globalen Befehl (`~/.local/bin/deltracemap`), den GeoIP-Cache und fragt nach ob generierte Karten in `~/Downloads/deltracemap/` ebenfalls gelöscht werden sollen. Das Projektverzeichnis selbst bleibt erhalten.

## Benutzung

```bash
deltracemap <ziel-host-oder-ip> [optionen]
```

| Option | Bedeutung |
|---|---|
| `--max-hops N` | maximale Hop-Anzahl (Standard: 30) |
| `--map` | Terminal-Koordinatenkarte zusätzlich anzeigen (standardmäßig aus) |
| `--gui` / `-g` | zusätzlich eine interaktive OpenStreetMap-Karte im Browser öffnen |

Beispiele:
```bash
deltracemap google.com
deltracemap 8.8.8.8 --max-hops 15
deltracemap 1.1.1.1 --gui
```



## Funktionsweise

1. `traceroute_core.py` ruft das System-`traceroute` auf und parst Hop-Nummer, IP und Round-Trip-Time.
2. `geoip.py` löst die IPs über die kostenlose [ip-api.com](http://ip-api.com) Batch-API in Land/Stadt/ISP/Koordinaten auf und cached Ergebnisse 30 Tage lokal unter `~/.cache/deltracemap/`.
3. `map_terminal.py` zeichnet die Hops als Punkte auf einem Längen-/Breitengrad-Koordinatengitter direkt im Terminal.
4. `gui_map.py` (nur mit `--gui`) erzeugt eine interaktive HTML-Karte mit Marker-Popups und Verbindungslinie zwischen den Hops, gespeichert unter `~/Downloads/deltracemap/`. Die Seite wird kurz über einen lokalen HTTP-Server ausgeliefert (nicht per `file://`), damit OpenStreetMaps Tile-Nutzungsrichtlinie (gültiger Referrer-Header) erfüllt ist.

## Einschränkungen

- Private/lokale IPs (z.B. 192.168.x.x) werden nicht geolokalisiert und erscheinen nicht auf der Karte.
- GeoIP-Daten sind näherungsweise (meist Stadt-/Regionsebene, keine exakte Adresse).
- `ip-api.com` erlaubt kostenlos 45 Anfragen/Minute – bei sehr häufigem Gebrauch kann das Limit greifen (dann bleiben Standorte leer, Cache hilft hier).
- Snap-/Flatpak-Browser (z.B. Snap-Firefox) blocken teils den Zugriff auf versteckte Ordner wie `/tmp` oder `~/.cache` – deshalb liegt die GUI-Karte sichtbar unter `~/Downloads/deltracemap/`.

## Projektstruktur

```
deltracemap/
├── main.py              # CLI-Einstiegspunkt, Argument-Parsing, Tabellen-Ausgabe
├── traceroute_core.py    # ruft System-traceroute auf, parst Hops
├── geoip.py              # IP → Land/Stadt/ISP/Koordinaten, mit Cache
├── map_terminal.py       # Terminal-Koordinatenkarte via plotext
├── gui_map.py            # interaktive HTML-Karte via folium + lokaler HTTP-Server
├── install.sh            # pip-Abhängigkeiten + globalen Befehl einrichten
├── uninstall.sh          # globalen Befehl + Cache wieder entfernen
├── requirements.txt
└── README.md
```

## Troubleshooting

**"Keine Route gefunden" / `traceroute` nicht installiert:**
```bash
sudo apt install traceroute
```

**GUI-Karte: Browser zeigt "Datei nicht gefunden":**
Tritt bei Snap-/Flatpak-Browsern auf, die nur Zugriff auf bestimmte Host-Ordner haben. Die Karte liegt absichtlich in `~/Downloads/deltracemap/` (sichtbarer Ordner), nicht in `/tmp` oder `~/.cache`.

**GUI-Karte: Kartenkacheln laden nicht / Tile-Policy-Fehler:**
`gui_map.py` liefert die Seite über einen kurzlebigen lokalen HTTP-Server (`http://127.0.0.1:<port>/...`) statt per `file://` aus – das ist nötig, da OpenStreetMaps Tile-Server einen gültigen HTTP-Referrer verlangt, den `file://`-Seiten nicht mitschicken. Der Server läuft standardmäßig 10 Sekunden (einstellbar über `SERVE_DURATION_S` in `gui_map.py`).

**`ModuleNotFoundError` beim Start:**
```bash
pip install --user -r requirements.txt
```

**`error: externally-managed-environment` beim Installieren:**
Neuere Debian/Ubuntu-Versionen (Python 3.11+) blocken `pip install` außerhalb von virtuellen Umgebungen (PEP 668). `install.sh` erkennt das automatisch und installiert stattdessen mit `--break-system-packages` – das betrifft nur dein `~/.local`-Verzeichnis, nicht die Systempakete. Manuell:
```bash
pip install --user --break-system-packages -r requirements.txt
```

**Terminal-Karte zeigt nichts / "Keine geolokalisierbaren Hops":**
Alle Hops waren entweder private IPs (z.B. im eigenen Heimnetz) oder haben nicht geantwortet (`* * *`). Das ist normal bei sehr nahen Zielen.

