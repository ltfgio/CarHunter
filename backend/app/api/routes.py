from fastapi import APIRouter, HTTPException
from app.domain.models import SearchQuery, SearchResponse, EngineLayout
from app.sources.registry import adapters
from app.engine.dedup import deduplicate
from app.engine.filtering import apply_legacy_filters, sort_listings

router = APIRouter(prefix="/api")

def enum_options(values: list[str]) -> list[dict]:
    labels = {
        "petrol":"Бензин", "diesel":"Дизель", "hybrid":"Гибрид", "electric":"Электро", "other":"Другое",
        "manual":"Механика", "automatic":"Автомат", "robot":"Робот", "cvt":"Вариатор",
        "fwd":"Передний", "rwd":"Задний", "awd":"Полный",
        "na":"Атмосферный", "turbo":"Турбо", "twin_turbo":"Битурбо", "supercharger":"Компрессор",
    }
    return [{"value": x, "label": labels.get(x, x)} for x in values]

ENGINE_LAYOUT_LABELS = {
    "single":"1 цилиндр", "twin":"2 цилиндра", "inline_3":"Рядная 3",
    "inline_4":"Рядная 4", "inline_5":"Рядная 5", "inline_6":"Рядная 6", "inline_8":"Рядная 8",
    "v4":"V4", "v6":"V6", "v8":"V8", "v10":"V10", "v12":"V12", "v16":"V16",
    "flat_2":"Оппозитная 2", "flat_4":"Оппозитная 4", "flat_6":"Оппозитная 6", "flat_8":"Оппозитная 8",
    "vr5":"VR5", "vr6":"VR6", "vr8":"VR8", "w8":"W8", "w12":"W12", "w16":"W16",
    "rotary":"Роторный", "electric_motor":"Электромотор", "other":"Другое",
}

FILTER_FIELDS = [
    {"field":"brand","label":"Марка","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"model","label":"Модель","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"generation","label":"Поколение","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"body_type","label":"Кузов","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"trim","label":"Комплектация","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"engine_code","label":"Код двигателя","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"engine_family","label":"Семейство двигателя","type":"string","operators":["eq","ne","contains","in","not_in"]},
    {"field":"engine_layout","label":"Схема двигателя","type":"enum","operators":["eq","ne","in","not_in"],
     "options":[{"value":x.value,"label":ENGINE_LAYOUT_LABELS.get(x.value,x.value)} for x in EngineLayout]},
    {"field":"year","label":"Год","type":"number","unit":"год","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"price_rub","label":"Цена","type":"number","unit":"₽","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"mileage_km","label":"Пробег","type":"number","unit":"км","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"displacement_l","label":"Объём","type":"number","unit":"л","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"cylinders","label":"Цилиндры","type":"number","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"power_hp","label":"Мощность","type":"number","unit":"л.с.","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"torque_nm","label":"Крутящий момент","type":"number","unit":"Н·м","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"doors","label":"Двери","type":"number","unit":"шт.","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"seats","label":"Места","type":"number","unit":"шт.","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"owner_count","label":"Владельцы","type":"number","unit":"шт.","operators":["eq","ne","gt","gte","lt","lte","between"]},
    {"field":"fuel","label":"Топливо","type":"enum","operators":["eq","ne","in","not_in"],
     "options":enum_options(["petrol","diesel","hybrid","electric","other"])},
    {"field":"transmission","label":"Коробка","type":"enum","operators":["eq","ne","in","not_in"],
     "options":enum_options(["manual","automatic","robot","cvt","other"])},
    {"field":"drivetrain","label":"Привод","type":"enum","operators":["eq","ne","in","not_in"],
     "options":enum_options(["fwd","rwd","awd","other"])},
    {"field":"aspiration","label":"Наддув","type":"enum","operators":["eq","ne","in","not_in"],
     "options":enum_options(["na","turbo","twin_turbo","supercharger","other"])},
    {"field":"steering_side","label":"Руль","type":"enum","operators":["eq","ne","in","not_in"],
     "options":[{"value":"left","label":"Левый"},{"value":"right","label":"Правый"},{"value":"unknown","label":"Не указан"}]},
    {"field":"seller_type","label":"Продавец","type":"string","operators":["eq","ne","contains","in","not_in"]},
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
    unknown = sorted(set(query.sources) - set(adapters))
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown sources: {', '.join(unknown)}")
    selected = query.sources or sorted(adapters)
    listings = []
    for name in selected:
        listings.extend(adapters[name].search(query))

    listings = deduplicate(listings)
    listings = apply_legacy_filters(listings, query)
    listings = sort_listings(listings, query.sort)
    return SearchResponse(
        query=query,
        total=len(listings),
        listings=listings[:query.limit],
    )
