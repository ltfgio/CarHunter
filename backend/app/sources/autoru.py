import os
from urllib.parse import urlencode
import httpx
from app.sources.base import MarketplaceAdapter
from app.domain.models import Listing, SearchQuery, FuelType, TransmissionType, DrivetrainType

API_URL = "https://apiauto.ru/1.0/search/cars/breadcrumbs"

FUEL = {"DIESEL": FuelType.diesel, "GASOLINE": FuelType.petrol, "ELECTRO": FuelType.electric, "HYBRID": FuelType.hybrid}
GEAR = {"MECHANICAL": TransmissionType.manual, "AUTOMATIC": TransmissionType.automatic, "ROBOT": TransmissionType.robot, "VARIATOR": TransmissionType.cvt}
DRIVE = {"ALL_WHEEL_DRIVE": DrivetrainType.awd, "FORWARD_CONTROL": DrivetrainType.fwd, "REAR_DRIVE": DrivetrainType.rwd}

class AutoRuAdapter(MarketplaceAdapter):
    name = "autoru"

    def _headers(self) -> dict[str, str]:
        token = os.getenv("AUTORU_API_TOKEN")
        return {"x-authorization": token} if token else {}

    def search(self, query: SearchQuery) -> list[Listing]:
        token = os.getenv("AUTORU_API_TOKEN")
        if not token:
            return []

        lookup = "#".join(x for x in [query.brand, query.model, query.generation] if x)
        params: list[tuple[str, str]] = [("state", "USED")]
        if lookup:
            params.append(("bc_lookup", lookup))
        if query.region:
            # Region-name -> rid resolution is deliberately kept outside the adapter
            # until a local Auto.ru region catalog is added.
            pass

        response = httpx.get(API_URL, params=params, headers=self._headers(), timeout=15.0)
        response.raise_for_status()
        payload = response.json()

        listings: list[Listing] = []
        for breadcrumb in payload.get("breadcrumbs", []):
            for entity in breadcrumb.get("entities", []):
                tech = entity.get("tech_params") or {}
                config = entity.get("configuration") or {}
                fuel = FUEL.get(tech.get("engine_type"))
                transmission = GEAR.get(tech.get("transmission"))
                drivetrain = DRIVE.get(tech.get("gear_type"))
                title = entity.get("name") or tech.get("human_name") or config.get("configuration_name") or "Auto.ru"
                # Breadcrumbs describe catalog/configuration data, not individual ads.
                # Therefore source_id is catalog-level and url is a catalog placeholder.
                listings.append(Listing(
                    source=self.name,
                    source_id=str(entity.get("id") or title),
                    url="https://auto.ru/",
                    title=title,
                    brand=query.brand,
                    model=query.model,
                    generation=query.generation,
                    body_type=config.get("body_type"),
                    doors=config.get("doors_count"),
                    fuel=fuel,
                    displacement_l=(tech.get("displacement") / 1000) if isinstance(tech.get("displacement"), (int, float)) else None,
                    power_hp=tech.get("power"),
                    transmission=transmission,
                    drivetrain=drivetrain,
                ))
        return listings
