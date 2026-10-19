"""GeoIP-Lookup über die kostenlose ip-api.com API, mit lokalem Datei-Cache."""

import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests

CACHE_PATH = Path.home() / ".cache" / "deltracemap" / "geoip_cache.json"
CACHE_MAX_AGE_S = 30 * 24 * 60 * 60  # 30 Tage
BATCH_URL = "http://ip-api.com/batch"


@dataclass
class GeoInfo:
    ip: str
    country: str | None
    city: str | None
    isp: str | None
    lat: float | None
    lon: float | None


def _load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache))


def _is_private_ip(ip: str) -> bool:
    octets = [int(o) for o in ip.split(".")]
    if octets[0] == 10:
        return True
    if octets[0] == 172 and 16 <= octets[1] <= 31:
        return True
    if octets[0] == 192 and octets[1] == 168:
        return True
    if octets[0] == 127:
        return True
    return False


def lookup_many(ips: list[str]) -> dict[str, GeoInfo]:
    """Löst mehrere IPs in einem Batch-Request auf (ip-api.com erlaubt bis zu 100 pro Anfrage)."""
    cache = _load_cache()
    now = time.time()
    result: dict[str, GeoInfo] = {}
    to_fetch: list[str] = []

    for ip in ips:
        if _is_private_ip(ip):
            result[ip] = GeoInfo(ip=ip, country="Lokal", city=None, isp=None, lat=None, lon=None)
            continue

        cached = cache.get(ip)
        if cached and now - cached.get("_fetched_at", 0) < CACHE_MAX_AGE_S:
            result[ip] = GeoInfo(
                ip=ip,
                country=cached.get("country"),
                city=cached.get("city"),
                isp=cached.get("isp"),
                lat=cached.get("lat"),
                lon=cached.get("lon"),
            )
        else:
            to_fetch.append(ip)

    if to_fetch:
        try:
            payload = [{"query": ip, "fields": "query,country,city,isp,lat,lon,status"} for ip in to_fetch]
            response = requests.post(BATCH_URL, json=payload, timeout=10)
            response.raise_for_status()
            for entry in response.json():
                ip = entry.get("query")
                if not ip:
                    continue
                info = GeoInfo(
                    ip=ip,
                    country=entry.get("country"),
                    city=entry.get("city"),
                    isp=entry.get("isp"),
                    lat=entry.get("lat"),
                    lon=entry.get("lon"),
                )
                result[ip] = info
                cache[ip] = {
                    "country": info.country,
                    "city": info.city,
                    "isp": info.isp,
                    "lat": info.lat,
                    "lon": info.lon,
                    "_fetched_at": now,
                }
            _save_cache(cache)
        except requests.RequestException:
            for ip in to_fetch:
                result.setdefault(ip, GeoInfo(ip=ip, country=None, city=None, isp=None, lat=None, lon=None))

    return result
