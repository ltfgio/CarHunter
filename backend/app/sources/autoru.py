import json
import re
from html import unescape
from typing import Any
from urllib.parse import urlencode

import httpx

from app.domain.models import Listing, SearchQuery, FuelType, TransmissionType, DrivetrainType
from app.sources.base import MarketplaceAdapter

BASE_URL = "https://auto.ru/cars/used/"


class AutoRuAdapter(MarketplaceAdapter):
    name = "autoru"
    # Auto.ru's official public API exposes catalog/statistical data, not a
    # general listing-search endpoint. Listing discovery therefore uses the
    # public web listing and keeps parsing isolated from the official catalog client.
    capabilities = {"listing_search": True, "catalog": True}

    def __init__(self) -> None:
        self.last_status: dict[str, Any] = {"state": "idle"}

    def _url(self, query: SearchQuery) -> str:
        native = query.source_params.get(self.name, {})
        if native.get("url"):
            return str(native["url"])

        params: list[tuple[str, str]] = [("currency", "RUR")]
        mapping = {
            "year_min": "year_from", "year_max": "year_to",
            "price_min": "price_from", "price_max": "price_to",
            "mileage_min": "km_age_from", "mileage_max": "km_age_to",
            "displacement_min_l": "engine_volume_from",
            "displacement_max_l": "engine_volume_to",
            "power_min_hp": "engine_power_from",
            "power_max_hp": "engine_power_to",
        }
        for field, key in mapping.items():
            value = getattr(query, field)
            if value is not None:
                if "volume" in key:
                    value = int(float(value) * 1000)
                params.append((key, str(value)))

        if query.brand or query.model:
            mark = (query.brand or "").upper().replace(" ", "_")
            model = (query.model or "").upper().replace(" ", "_")
            params.append(("mark_model", f"{mark}#{model}" if model else mark))

        if query.fuel:
            params.append(("engine_type", {
                FuelType.petrol: "GASOLINE", FuelType.diesel: "DIESEL",
                FuelType.hybrid: "HYBRID", FuelType.electric: "ELECTRO",
            }.get(query.fuel, query.fuel.value)))
        if query.transmission:
            params.append(("transmission", {
                TransmissionType.automatic: "AUTOMATIC", TransmissionType.manual: "MECHANICAL",
                TransmissionType.robot: "ROBOT", TransmissionType.cvt: "VARIATOR",
            }.get(query.transmission, query.transmission.value)))
        if query.drivetrain:
            params.append(("drive", {
                DrivetrainType.awd: "ALL_WHEEL_DRIVE", DrivetrainType.fwd: "FORWARD_CONTROL",
                DrivetrainType.rwd: "REAR_DRIVE",
            }.get(query.drivetrain, query.drivetrain.value)))
        if query.region:
            params.append(("rid", query.region))

        params.extend([("section", "USED"), ("output_type", "list")])
        return BASE_URL + "?" + urlencode(params)

    @staticmethod
    def _html_rows(html: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        # JSON-LD is the most stable machine-readable representation when present.
        for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
            try:
                payload = json.loads(unescape(block.strip()))
            except (ValueError, TypeError):
                continue
            objects = payload if isinstance(payload, list) else [payload]
            for obj in objects:
                if isinstance(obj, dict) and (obj.get("@type") in {"Car", "Vehicle", "Product"} or obj.get("offers")):
                    rows.append(obj)

        # Fallback: extract serialized offer-like objects from page state.
        for match in re.finditer(r'"(?:url|link)"\s*:\s*"(https://auto\\.ru/[^"]+)"', html):
            url = match.group(1).replace("\/", "/")
            if any(row.get("url") == url for row in rows):
                continue
            start = max(0, match.start() - 2500)
            end = min(len(html), match.end() + 2500)
            chunk = html[start:end]
            def field(name: str) -> str | None:
                m = re.search(r'"' + re.escape(name) + r'"\s*:\s*(".*?"|-?\d+(?:\.\d+)?)', chunk, re.S)
                return m.group(1).strip('"') if m else None
            rows.append({"url": url, "name": field("name") or field("title"),
                         "price": field("price"), "year": field("year"),
                         "mileage": field("km_age") or field("mileage")})
        return rows

    def search(self, query: SearchQuery) -> list[Listing]:
        url = self._url(query)
        self.last_status = {"state": "fetching", "url": url}
        try:
            response = httpx.get(
                url,
                timeout=20.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36 CarHunter/0.1",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.6",
                    "Referer": "https://auto.ru/",
                },
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            self.last_status = {"state": "timeout", "url": url, "error": str(exc)}
            return []
        except httpx.HTTPStatusError as exc:
            self.last_status = {
                "state": "http_error", "url": url,
                "status_code": exc.response.status_code,
                "error": str(exc),
            }
            return []
        except httpx.HTTPError as exc:
            self.last_status = {"state": "network_error", "url": url, "error": str(exc)}
            return []

        final_url = str(response.url)
        if any(marker in final_url.lower() for marker in ("/auth/", "/login", "passport.yandex")):
            self.last_status = {
                "state": "blocked_or_auth", "url": url, "final_url": final_url,
                "status_code": response.status_code,
            }
            return []

        rows = [row for row in self._html_rows(response.text) if row.get("url")]
        listings = [self._listing(row) for row in rows]
        self.last_status = {
            "state": "ok" if listings else "empty",
            "url": url,
            "final_url": final_url,
            "status_code": response.status_code,
            "parsed_rows": len(rows),
        }
        return listings

    def _listing(self, row: dict[str, Any]) -> Listing:
        offers = row.get("offers") if isinstance(row.get("offers"), dict) else {}
        price = row.get("price") or offers.get("price")
        url = str(row.get("url") or row.get("link") or "")
        source_id = self._source_id(url, row)
        return Listing(
            source=self.name,
            source_id=source_id,
            url=url,
            raw_url=url,
            title=str(row.get("name") or row.get("title") or "Auto.ru объявление"),
            price_rub=self._int(price),
            year=self._int(row.get("year") or row.get("productionDate")),
            mileage_km=self._int(row.get("mileage") or row.get("km_age") or self._nested_value(row.get("mileageFromOdometer"), "value")),
            brand=self._str(row.get("brand") or row.get("mark")),
            model=self._str(row.get("model")),
            generation=self._str(row.get("generation")),
            body_type=self._str(row.get("bodyType") or row.get("body_type")),
            fuel=self._fuel(row.get("fuelType") or row.get("engine_type")),
            displacement_l=self._float(row.get("engineDisplacement") or row.get("displacement")),
            power_hp=self._int(row.get("enginePower") or row.get("power")),
            transmission=self._transmission(row.get("transmission")),
            drivetrain=self._drive(row.get("drive") or row.get("driveType")),
            region=self._str(row.get("region") or row.get("address")),
            description=self._str(row.get("description")),
            images=self._images(row),
        )

    @staticmethod
    def _nested_value(v: Any, key: str) -> Any:
        return v.get(key) if isinstance(v, dict) else None

    @staticmethod
    def _source_id(url: str, row: dict[str, Any]) -> str:
        for key in ("id", "offerId", "inner_id"):
            if row.get(key) is not None:
                return str(row[key])
        match = re.search(r"/(?:sale|cars)/[^/]+/[^/]+/([^/?#]+)", url)
        return match.group(1) if match else url

    @staticmethod
    def _images(row: dict[str, Any]) -> list[str]:
        values = row.get("image") or row.get("images") or []
        if isinstance(values, str):
            return [values]
        if isinstance(values, dict):
            values = list(values.values())
        return [str(x.get("url") or x) if isinstance(x, dict) else str(x) for x in values][:20]

    @staticmethod
    def _str(v: Any) -> str | None:
        return str(v) if v not in (None, "") else None

    @staticmethod
    def _int(v: Any) -> int | None:
        try: return int(float(v)) if v not in (None, "") else None
        except (TypeError, ValueError): return None

    @staticmethod
    def _float(v: Any) -> float | None:
        try: return float(v) if v not in (None, "") else None
        except (TypeError, ValueError): return None

    @staticmethod
    def _fuel(v: Any) -> FuelType | None:
        s = str(v).lower()
        if "diesel" in s or "диз" in s: return FuelType.diesel
        if "electric" in s or "electro" in s or "элект" in s: return FuelType.electric
        if "hybrid" in s or "гибрид" in s: return FuelType.hybrid
        if "gasoline" in s or "petrol" in s or "бенз" in s: return FuelType.petrol
        return None

    @staticmethod
    def _transmission(v: Any) -> TransmissionType | None:
        s = str(v).lower()
        if "manual" in s or "mechan" in s: return TransmissionType.manual
        if "robot" in s or "робот" in s: return TransmissionType.robot
        if "variator" in s or "cvt" in s: return TransmissionType.cvt
        if "automatic" in s or "auto" in s or "автомат" in s: return TransmissionType.automatic
        return None

    @staticmethod
    def _drive(v: Any) -> DrivetrainType | None:
        s = str(v).lower()
        if "all_wheel" in s or "awd" in s or "4wd" in s or "пол" in s: return DrivetrainType.awd
        if "forward" in s or "front" in s or "перед" in s: return DrivetrainType.fwd
        if "rear" in s or "зад" in s: return DrivetrainType.rwd
        return None


adapter = AutoRuAdapter()
