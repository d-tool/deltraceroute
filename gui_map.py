"""Erzeugt eine interaktive HTML-Karte (Leaflet via folium) und öffnet sie im Browser."""

import functools
import http.server
import threading
import time
import webbrowser
from pathlib import Path

import folium

from geoip import GeoInfo
from traceroute_core import Hop

# Snap-Browser (z.B. Firefox) blocken versteckte Ordner (".cache" etc.) im Sandbox,
# daher sichtbaren Ordner wie Downloads verwenden
OUTPUT_DIR = Path.home() / "Downloads" / "deltracemap"

# Wie lange der lokale HTTP-Server offen bleibt, damit Seite + Kartenkacheln laden können
SERVE_DURATION_S = 10


def render_gui_map(hops: list[Hop], geo_by_ip: dict[str, GeoInfo], target: str) -> Path | None:
    points: list[tuple[float, float, str]] = []

    for hop in hops:
        if hop.ip is None:
            continue
        geo = geo_by_ip.get(hop.ip)
        if geo is None or geo.lat is None or geo.lon is None:
            continue
        label = f"Hop {hop.number}: {hop.ip}"
        if geo.city or geo.country:
            label += f" ({geo.city or '?'}, {geo.country or '?'})"
        if geo.isp:
            label += f" – {geo.isp}"
        if hop.avg_rtt is not None:
            label += f" – {hop.avg_rtt:.1f} ms"
        points.append((geo.lat, geo.lon, label))

    if not points:
        print("Keine geolokalisierbaren Hops gefunden – GUI-Karte wird nicht erzeugt.")
        return None

    center_lat = sum(p[0] for p in points) / len(points)
    center_lon = sum(p[1] for p in points) / len(points)

    # Standard-OSM-Tiles verwenden (Default von folium), kein API-Key noetig
    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=3)

    for lat, lon, label in points:
        folium.Marker(location=[lat, lon], popup=label).add_to(fmap)

    folium.PolyLine(locations=[(p[0], p[1]) for p in points], color="red", weight=2).add_to(fmap)

    output_path = OUTPUT_DIR / f"deltracemap_{target.replace('.', '_')}.html"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fmap.save(str(output_path))

    # Über echten http://-Server ausliefern statt file:// zu oeffnen: file:// schickt
    # keinen Referrer mit, den OSMs Tile-Nutzungsrichtlinie verlangt -> Tiles werden sonst blockiert
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUTPUT_DIR))
    server = http.server.HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    url = f"http://127.0.0.1:{port}/{output_path.name}"
    webbrowser.open(url)
    print(f"Karte wird {SERVE_DURATION_S}s lokal bereitgestellt unter: {url}")
    time.sleep(SERVE_DURATION_S)

    server.shutdown()
    return output_path
