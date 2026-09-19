import httpx
from typing import Any
from app.sources.base import MarketplaceAdapter
from app.domain.models import Listing, SearchQuery, FuelType, TransmissionType, DrivetrainType

API_URL = "https://api.drom.ru/v1.2/bulls/search"

class DromAdapter(MarketplaceAdapter):
    name = "drom"

    def _params(self, query: SearchQuery) -> dict[str, Any]:
        p: dict[str, Any] = {"page": 1}
        if query.year_min is not None: p["minYear"] = query.year_min
        if query.year_max is not None: p["maxYear"] = query.year_max
        if query.price_min is not None: p["minPrice"] = query.price_min
        if query.price_max is not None: p["maxPrice"] = query.price_max
        if query.displacement_min_l is not None: p["minEngineVolume"] = query.displacement_min_l
        if query.displacement_max_l is not None: p["maxEngineVolume"] = query.displacement_max_l
        if query.power_min_hp is not None: p["minEnginePower"] = query.power_min_hp
        if query.power_max_hp is not None: p["maxEnginePower"] = query.power_max_hp
        if query.mileage_min is not None: p["minMileageKm"] = query.mileage_min
        if query.mileage_max is not None: p["maxMileageKm"] = query.mileage_max
        if query.region: p["regionId"] = query.region
        if query.model: p["modelId"] = query.model
        if query.brand: p["firmId"] = query.brand
        return p

    def search(self, query: SearchQuery) -> list[Listing]:
        try:
            r = httpx.get(API_URL, params=self._params(query), timeout=15.0, headers={"User-Agent": "CarHunter/0.1"})
            r.raise_for_status()
            payload = r.json()
        except (httpx.HTTPError, ValueError):
            return []
        rows = payload.get("offers") or payload.get("items") or payload.get("results") or []
        if isinstance(rows, dict): rows = rows.get("offers") or rows.get("items") or []
        return [self._listing(row) for row in rows if isinstance(row, dict)]

    def _listing(self, row: dict[str, Any]) -> Listing:
        oid = str(row.get("id") or row.get("offerId") or row.get("offer_id") or "")
        url = row.get("url") or (f"https://auto.drom.ru/offer/{oid}/" if oid else "https://auto.drom.ru/")
        return Listing(
            source=self.name, source_id=oid, url=url, raw_url=url,
            title=str(row.get("title") or row.get("name") or "Drom объявление"),
            price_rub=self._int(row.get("price") or row.get("priceValue")),
            year=self._int(row.get("year")), mileage_km=self._int(row.get("mileageKm") or row.get("mileage")),
            brand=self._str(row.get("mark") or row.get("brand")), model=self._str(row.get("model")),
            generation=self._str(row.get("generation")), body_type=self._str(row.get("frameType") or row.get("bodyType")),
            fuel=self._fuel(row.get("fuelType") or row.get("fuel")),
            displacement_l=self._float(row.get("engineVolume") or row.get("engine_volume")),
            power_hp=self._int(row.get("enginePower") or row.get("power")),
            transmission=self._transmission(row.get("transmissionType") or row.get("transmission")),
            drivetrain=self._drive(row.get("driveType") or row.get("drive")),
            region=self._str(row.get("region") or row.get("city")),
            description=self._str(row.get("description") or row.get("info")),
            images=self._images(row),
        )

    @staticmethod
    def _str(v: Any) -> str | None: return str(v) if v not in (None, "") else None
    @staticmethod
    def _int(v: Any) -> int | None:
        try: return int(float(v)) if v not in (None, "") else None
        except (TypeError, ValueError): return None
    @staticmethod
    def _float(v: Any) -> float | None:
        try: return float(v) if v not in (None, "") else None
        except (TypeError, ValueError): return None
    @staticmethod
    def _images(row: dict[str, Any]) -> list[str]:
        photos = row.get("photos") or row.get("images") or []
        if isinstance(photos, dict): photos = list(photos.values())
        return [str(x.get("url") if isinstance(x, dict) else x) for x in photos if x]
    @staticmethod
    def _fuel(v: Any) -> FuelType | None:
        s=str(v).lower()
        if "diesel" in s or "диз" in s: return FuelType.diesel
        if "electric" in s or "элект" in s: return FuelType.electric
        if "hybrid" in s or "гибрид" in s: return FuelType.hybrid
        if "petrol" in s or "gasoline" in s or "бенз" in s: return FuelType.petrol
        return None
    @staticmethod
    def _transmission(v: Any) -> TransmissionType | None:
        s=str(v).lower()
        if "manual" in s or "механ" in s: return TransmissionType.manual
        if "robot" in s or "робот" in s: return TransmissionType.robot
        if "cvt" in s or "вариатор" in s: return TransmissionType.cvt
        if "auto" in s or "автомат" in s: return TransmissionType.automatic
        return None
    @staticmethod
    def _drive(v: Any) -> DrivetrainType | None:
        s=str(v).lower()
        if "front" in s or "перед" in s: return DrivetrainType.fwd
        if "rear" in s or "зад" in s: return DrivetrainType.rwd
        if "all" in s or "4wd" in s or "awd" in s or "пол" in s: return DrivetrainType.awd
        return None

adapter = DromAdapter()
