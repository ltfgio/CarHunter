from fastapi import APIRouter
from app.domain.models import SearchQuery, SearchResponse, EngineLayout
from app.sources.registry import adapters

router = APIRouter(prefix="/api")

FILTER_FIELDS = [
    {"field":"brand","label":"Марка","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"model","label":"Модель","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"generation","label":"Поколение","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"body_type","label":"Кузов","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"engine_code","label":"Код двигателя","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"engine_family","label":"Семейство двигателя","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"engine_layout","label":"Схема двигателя","type":"enum","operators":["eq","ne","in","not_in"],"options":[{"value":x.value,"label":x.value.upper().replace("_"," ")} for x in EngineLayout]},
    {"field":"year","label":"Год","type":"number","unit":"год","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"price_rub","label":"Цена","type":"number","unit":"₽","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"mileage_km","label":"Пробег","type":"number","unit":"км","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"displacement_l","label":"Объём","type":"number","unit":"л","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"cylinders","label":"Цилиндры","type":"number","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"power_hp","label":"Мощность","type":"number","unit":"л.с.","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"torque_nm","label":"Крутящий момент","type":"number","unit":"Н·м","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"fuel","label":"Топливо","type":"enum","operators":["eq","ne","in","not_in"],"options":[{"value":x,"label":x} for x in ["petrol","diesel","hybrid","electric","other"]]},
    {"field":"transmission","label":"Коробка","type":"enum","operators":["eq","ne","in","not_in"],"options":[{"value":x,"label":x} for x in ["manual","automatic","robot","cvt","other"]]},
    {"field":"drivetrain","label":"Привод","type":"enum","operators":["eq","ne","in","not_in"],"options":[{"value":x,"label":x} for x in ["fwd","rwd","awd","other"]]},
    {"field":"aspiration","label":"Наддув","type":"enum","operators":["eq","ne","in","not_in"],"options":[{"value":x,"label":x} for x in ["na","turbo","twin_turbo","supercharger","other"]]},
    {"field":"region","label":"Регион","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"text","label":"Текст объявления","type":"text","operators":["contains","not_contains"]},
]

@router.get("/sources")
def sources() -> list[str]:
    return sorted(adapters)

@router.get("/filter-fields")
def filter_fields() -> list[dict]:
    return FILTER_FIELDS

@router.post("/search", response_model=SearchResponse)
def search(query: SearchQuery) -> SearchResponse:
    return SearchResponse(query=query, total=0, listings=[])
