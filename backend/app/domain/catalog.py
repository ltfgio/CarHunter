from typing import Any
from pydantic import BaseModel, Field

class CatalogTechParams(BaseModel):
    nameplate_engine: str | None = None
    engine_type: str | None = None
    displacement: int | None = None
    gear_type: str | None = None
    transmission: str | None = None
    power: int | None = None
    power_kvt: str | None = None
    year_start: int | None = None
    year_stop: int | None = None
    human_name: str | None = None

class CatalogNode(BaseModel):
    id: str
    name: str
    level: str
    offers_count: int = 0
    is_popular: bool | None = None
    mark_id: str | None = None
    mark_name: str | None = None
    model_id: str | None = None
    model_name: str | None = None
    generation_id: str | None = None
    generation_name: str | None = None
    generation_year_from: int | None = None
    generation_year_to: int | None = None
    generation_restyle: bool | None = None
    configuration_id: str | None = None
    configuration_name: str | None = None
    body_type: str | None = None
    doors_count: int | None = None
    photo_url: str | None = None
    tech_params: CatalogTechParams | None = None
    raw: dict[str, Any] = Field(default_factory=dict)

class CatalogResponse(BaseModel):
    source: str
    state: str
    nodes: list[CatalogNode]
    total: int
