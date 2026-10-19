#!/usr/bin/env python3
"""pytraceroute – Visual-Traceroute-Klon mit Hop-Tabelle, Terminal-Karte und optionaler GUI-Karte."""

import argparse
import sys

from rich.console import Console
from rich.table import Table

from geoip import lookup_many
from map_terminal import render_ascii_map
from traceroute_core import Hop, run_traceroute

console = Console()


def build_table(hops: list[Hop], geo_by_ip: dict) -> Table:
    table = Table(title="Traceroute Hops")
    table.add_column("#", justify="right")
    table.add_column("IP")
    table.add_column("Hostname")
    table.add_column("RTT (ms)", justify="right")
    table.add_column("Land")
    table.add_column("Stadt")
    table.add_column("ISP")

    for hop in hops:
        if hop.timeout or hop.ip is None:
            table.add_row(str(hop.number), "*", "-", "-", "-", "-", "-")
            continue

        geo = geo_by_ip.get(hop.ip)
        rtt = f"{hop.avg_rtt:.1f}" if hop.avg_rtt is not None else "-"
        table.add_row(
            str(hop.number),
            hop.ip,
            hop.hostname or "-",
            rtt,
            geo.country if geo and geo.country else "-",
            geo.city if geo and geo.city else "-",
            geo.isp if geo and geo.isp else "-",
        )

    return table


def main() -> int:
    parser = argparse.ArgumentParser(description="Visual Traceroute mit Karten-Anzeige")
    parser.add_argument("target", help="Ziel-Host oder IP-Adresse")
    parser.add_argument("--max-hops", type=int, default=30, help="Maximale Anzahl Hops (Standard: 30)")
    parser.add_argument("--map", action="store_true", help="Terminal-Koordinatenkarte zusätzlich anzeigen (standardmäßig aus)")
    parser.add_argument("-g", "--gui", action="store_true", help="Zusätzlich interaktive HTML-Karte im Browser öffnen")
    args = parser.parse_args()

    console.print(f"[bold]Traceroute zu {args.target}...[/bold]")
    hops: list[Hop] = []
    with console.status("Ermittle Route..."):
        for hop in run_traceroute(args.target, max_hops=args.max_hops):
            hops.append(hop)

    if not hops:
        console.print("[red]Keine Route gefunden – ist 'traceroute' installiert? (sudo apt install traceroute)[/red]")
        return 1

    ips = [hop.ip for hop in hops if hop.ip]
    with console.status("Löse Standorte auf (GeoIP)..."):
        geo_by_ip = lookup_many(ips)

    console.print(build_table(hops, geo_by_ip))

    if args.map:
        render_ascii_map(hops, geo_by_ip)

    if args.gui:
        from gui_map import render_gui_map

        path = render_gui_map(hops, geo_by_ip, args.target)
        if path:
            console.print(f"[green]GUI-Karte gespeichert und im Browser geöffnet: {path}[/green]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
