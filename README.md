# deltracemap

A visual traceroute clone for the terminal written from Claude: hop table with GeoIP info, an ASCII coordinate map directly in the terminal (via `plotext`), and optionally an interactive HTML map in the browser (via `folium`).

## Requirements

| What | Version / Note |
|---|---|
| Python | 3.10 or newer (uses `X \| None` type hints, `dataclass`) |
| `traceroute` (system binary) | on Debian/Ubuntu via `apt install traceroute` |
| pip packages | see `requirements.txt`: `requests`, `rich`, `plotext==5.3.2`, `folium` |
| Internet access | for `traceroute` itself and for the GeoIP lookup (ip-api.com) |

No `sudo`/root required – `traceroute` runs in UDP mode by default on Linux without elevated privileges.

**Important note on the `plotext` version:** `plotext==5.3.2` is intentionally pinned. Newer versions (6.0+) completely restructured the internal API and no longer expose the functions used here (`scatter`, `plot`, `text`, `clf`, ...) under the same names.

## Installation

```bash
sudo apt install traceroute   # if not already installed
git clone <repo-url> deltracemap
cd deltracemap
bash install.sh
```

`install.sh` installs the pip dependencies and sets up the global `deltracemap` command in `~/.local/bin/` – the standard location for user-specific programs on Linux, already in `PATH` on most distributions (including Ubuntu). If not, the script appends the right line to `~/.bashrc` automatically.

Then simply run from anywhere:
```bash
deltracemap google.com
deltracemap 8.8.8.8 --gui
```

### Manual installation (without install.sh)

```bash
pip install --user -r requirements.txt
mkdir -p ~/.local/bin
cat > ~/.local/bin/deltracemap << 'EOF'
#!/bin/bash
exec python3 "/path/to/your/deltracemap/main.py" "$@"
EOF
chmod +x ~/.local/bin/deltracemap
```
Adjust the path on the second line to match where you actually cloned the repo.

### Uninstall

```bash
bash uninstall.sh
```

Removes the global command (`~/.local/bin/deltracemap`), the GeoIP cache, and asks whether generated maps in `~/Downloads/deltracemap/` should be deleted too. The project directory itself is left untouched.

## Usage

```bash
deltracemap <target-host-or-ip> [options]
```

| Option | Meaning |
|---|---|
| `--max-hops N` | maximum number of hops (default: 30) |
| `--map` | additionally show the terminal coordinate map (off by default) |
| `--gui` / `-g` | additionally open an interactive OpenStreetMap map in the browser |

Examples:
```bash
deltracemap google.com
deltracemap 8.8.8.8 --max-hops 15
deltracemap 1.1.1.1 --gui
```

## How it works

1. `traceroute_core.py` calls the system `traceroute` and parses hop number, IP, and round-trip time.
2. `geoip.py` resolves IPs via the free [ip-api.com](http://ip-api.com) batch API into country/city/ISP/coordinates, and caches results locally for 30 days under `~/.cache/deltracemap/`.
3. `map_terminal.py` draws the hops as points on a longitude/latitude coordinate grid directly in the terminal.
4. `gui_map.py` (only with `--gui`) generates an interactive HTML map with marker popups and a connecting line between the hops, saved under `~/Downloads/deltracemap/`. The page is briefly served through a local HTTP server (instead of `file://`) so that OpenStreetMap's tile usage policy (which requires a valid HTTP referrer) is satisfied.

## Limitations

- Private/local IPs (e.g. 192.168.x.x) cannot be geolocated and won't appear on the map.
- GeoIP data is approximate (usually city/region level, not an exact address).
- `ip-api.com` allows 45 free requests/minute – with very frequent use the limit may be hit (locations then stay empty; the cache helps here).
- Snap/Flatpak browsers (e.g. Snap Firefox) sometimes block access to hidden folders like `/tmp` or `~/.cache` – that's why the GUI map is stored in the visible `~/Downloads/deltracemap/` folder.

## Project structure

```
deltracemap/
├── main.py              # CLI entry point, argument parsing, table output
├── traceroute_core.py    # calls system traceroute, parses hops
├── geoip.py              # IP → country/city/ISP/coordinates, with caching
├── map_terminal.py       # terminal coordinate map via plotext
├── gui_map.py            # interactive HTML map via folium + local HTTP server
├── install.sh            # sets up pip dependencies + global command
├── uninstall.sh          # removes global command + cache
├── requirements.txt
└── README.md
```

## Troubleshooting

**"No route found" / `traceroute` not installed:**
```bash
sudo apt install traceroute
```

**GUI map: browser shows "file not found":**
Happens with Snap/Flatpak browsers that only have access to certain host folders. The map is intentionally placed in `~/Downloads/deltracemap/` (a visible folder), not in `/tmp` or `~/.cache`.

**GUI map: tiles don't load / tile policy error:**
`gui_map.py` serves the page through a short-lived local HTTP server (`http://127.0.0.1:<port>/...`) instead of via `file://` – this is necessary because OpenStreetMap's tile servers require a valid HTTP referrer, which `file://` pages don't send. The server runs for 10 seconds by default (configurable via `SERVE_DURATION_S` in `gui_map.py`).

**`ModuleNotFoundError` on startup:**
```bash
pip install --user -r requirements.txt
```

**`error: externally-managed-environment` during install:**
Newer Debian/Ubuntu versions (Python 3.11+) block `pip install` outside virtual environments (PEP 668). `install.sh` detects this automatically and installs with `--break-system-packages` instead – this only affects your `~/.local` directory, not system packages. Manually:
```bash
pip install --user --break-system-packages -r requirements.txt
```

**Terminal map shows nothing / "No geolocatable hops":**
All hops were either private IPs (e.g. on your home network) or didn't respond (`* * *`). This is normal for very nearby targets.

