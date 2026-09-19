import os
from typing import Any
import httpx
from app.domain.catalog import CatalogNode, CatalogResponse, CatalogTechParams

API_URL = "https://apiauto.ru/1.0/search/cars/breadcrumbs"

class AutoRuCatalogClient:
    source = "autoru"

    def _headers(self) -> dict[str, str]:
        token = os.getenv("AUTORU_API_TOKEN")
        return {"x-authorization": token} if token else {}

    def fetch(self, bc_lookup: list[str] | None = None, state: str = "USED", rid: list[str] | None = None) -> CatalogResponse:
        token = os.getenv("AUTORU_API_TOKEN")
        if not token:
            raise RuntimeError("AUTORU_API_TOKEN is not configured")
        params: list[tuple[str, str]] = [("state", state)]
        lookup = "#".join(value for value in (bc_lookup or []) if value)
        if lookup:
            params.append(("bc_lookup", lookup))
        for value in rid or []:
            if value:
                params.append(("rid", value))
        response = httpx.get(API_URL, params=params, headers=self._headers(), timeout=15.0)
        response.raise_for_status()
        payload = response.json()
        nodes: list[CatalogNode] = []
        for breadcrumb in payload.get("breadcrumbs", []):
            level = str(breadcrumb.get("meta_level") or "").replace("_LEVEL", "").lower()
            mark = breadcrumb.get("mark") or {}
            model = breadcrumb.get("model") or {}
            generation = breadcrumb.get("super_generation") or {}
            config = breadcrumb.get("configuration") or {}
            gen_detail = generation.get("super_gen") or {}
            cfg_detail = config.get("configuration") or {}
            for entity in breadcrumb.get("entities", []):
                tech = entity.get("tech_params") or {}
                photo = ((entity.get("configuration") or {}).get("photo") or {}).get("sizes") or {}
                if not photo:
                    photo = (cfg_detail.get("photo") or {}).get("sizes") or {}
                node = CatalogNode(
                    id=str(entity.get("id") or ""),
                    name=str(entity.get("name") or tech.get("human_name") or cfg_detail.get("human_name") or "Без названия"),
                    level=level,
                    offers_count=int(entity.get("offers_count") or 0),
                    is_popular=entity.get("is_popular"),
                    mark_id=str(mark.get("id")) if mark.get("id") is not None else None,
                    mark_name=mark.get("name"),
                    model_id=str(model.get("id")) if model.get("id") is not None else None,
                    model_name=model.get("name"),
                    generation_id=str(generation.get("id")) if generation.get("id") is not None else None,
                    generation_name=generation.get("name"),
                    generation_year_from=gen_detail.get("year_from"),
                    generation_year_to=gen_detail.get("year_to"),
                    generation_restyle=gen_detail.get("is_restyle"),
                    configuration_id=str(config.get("id")) if config.get("id") is not None else None,
                    configuration_name=cfg_detail.get("configuration_name") or config.get("name"),
                    body_type=cfg_detail.get("body_type"),
                    doors_count=int(cfg_detail["doors_count"]) if str(cfg_detail.get("doors_count", "")).isdigit() else None,
                    photo_url=next(iter(photo.values()), None),
                    tech_params=CatalogTechParams.model_validate(tech) if tech else None,
                    raw=entity,
                )
                if node.id:
                    nodes.append(node)
        return CatalogResponse(source=self.source, state=state, nodes=nodes, total=len(nodes))

client = AutoRuCatalogClient()
