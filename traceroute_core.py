"""Führt den System-Traceroute aus und parst die Ausgabe in Hop-Objekte."""

import re
import subprocess
from dataclasses import dataclass, field


@dataclass
class Hop:
    number: int
    ip: str | None
    hostname: str | None
    rtts_ms: list[float] = field(default_factory=list)
    timeout: bool = False

    @property
    def avg_rtt(self) -> float | None:
        return sum(self.rtts_ms) / len(self.rtts_ms) if self.rtts_ms else None


# Beispielzeilen (mit Hostnamen, DNS aktiv):
#  1  _gateway (192.168.1.1)  0.345 ms  0.312 ms  0.298 ms
# Beispielzeilen (rein numerisch, -n Flag):
#  2  10.0.0.1  1.234 ms  1.100 ms  1.050 ms
#  3  * * *
_HOP_LINE_RE = re.compile(r"^\s*(\d+)\s+(.*)$")
_HOST_IP_RE = re.compile(r"([^\s()]+)\s+\(([\d.]+)\)")
_PLAIN_IP_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3})\b")
_RTT_RE = re.compile(r"([\d.]+)\s*ms")


def parse_hop_line(line: str) -> Hop | None:
    match = _HOP_LINE_RE.match(line)
    if not match:
        return None

    number = int(match.group(1))
    rest = match.group(2)

    host_ip_match = _HOST_IP_RE.search(rest)
    if host_ip_match:
        hostname = host_ip_match.group(1)
        ip = host_ip_match.group(2)
    else:
        plain_ip_match = _PLAIN_IP_RE.match(rest)
        hostname = None
        ip = plain_ip_match.group(1) if plain_ip_match else None

    if ip is None:
        return Hop(number=number, ip=None, hostname=None, timeout=True)

    rtts = [float(v) for v in _RTT_RE.findall(rest)]
    return Hop(number=number, ip=ip, hostname=hostname, rtts_ms=rtts)


def run_traceroute(target: str, max_hops: int = 30, timeout_s: int = 2):
    """Startet `traceroute` und liefert Hop-Objekte sobald eine Zeile fertig ist (Generator)."""
    # -4 erzwingt IPv4: Hop-Parsing und GeoIP unterstuetzen nur IPv4-Adressen
    cmd = ["traceroute", "-4", "-n", "-m", str(max_hops), "-w", str(timeout_s), target]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None
    for line in process.stdout:
        hop = parse_hop_line(line)
        if hop is not None:
            yield hop

    process.wait()
