"""Zeichnet die Traceroute-Hops auf einem Lon/Lat-Koordinatengitter im Terminal (mit plotext).

Hinweis: plotext hat keine eingebaute Weltkarten-Silhouette, daher wird ein
einfaches Längen-/Breitengrad-Gitter mit den Hop-Punkten und Verbindungslinie gezeichnet.
"""

import plotext as plt

from geoip import GeoInfo
from traceroute_core import Hop


def render_ascii_map(hops: list[Hop], geo_by_ip: dict[str, GeoInfo]) -> None:
    lats: list[float] = []
    lons: list[float] = []
    labels: list[str] = []

    for hop in hops:
        if hop.ip is None:
            continue
        geo = geo_by_ip.get(hop.ip)
        if geo is None or geo.lat is None or geo.lon is None:
            continue
        lats.append(geo.lat)
        lons.append(geo.lon)
        labels.append(str(hop.number))

    if not lats:
        print("Keine geolokalisierbaren Hops gefunden (nur lokale/private IPs?).")
        return

    plt.clf()
    plt.plot_size(100, 30)
    plt.title("Traceroute - Routenverlauf (Laengen-/Breitengrad)")
    plt.xlim(-180, 180)
    plt.ylim(-90, 90)
    plt.xlabel("Laengengrad")
    plt.ylabel("Breitengrad")
    plt.grid(True, True)

    plt.plot(lons, lats, color="red")
    plt.scatter(lons, lats, marker="hd", color="red")
    for lon, lat, label in zip(lons, lats, labels):
        plt.text(label, x=lon, y=lat, color="white")

    plt.show()

