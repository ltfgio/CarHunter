from collections.abc import Iterable
from typing import Any
import re
from app.domain.models import AspirationType, EngineLayout, FilterCondition, FilterGroup, FilterOperator, Listing

_ENGINE_LAYOUT_PATTERNS = [
    (EngineLayout.v12, r"\bv[\s-]?12\\b"),
    (EngineLayout.v10, r"\bv[\s-]?10\\b"),
    (EngineLayout.v8, r"\bv[\s-]?8\\b"),
    (EngineLayout.v6, r"\bv[\s-]?6\\b"),
    (EngineLayout.v4, r"\bv[\s-]?4\\b"),
    (EngineLayout.w12, r"\bw[\s-]?12\\b"),
    (EngineLayout.w8, r"\bw[\s-]?8\\b"),
    (EngineLayout.inline_6, r"\b(?:i|l|r)[\s-]?6\\b|рядн(?:ая|ый)?\s*6"),
    (EngineLayout.inline_5, r"\b(?:i|l|r)[\s-]?5\\b|рядн(?:ая|ый)?\s*5"),
    (EngineLayout.inline_4, r"\b(?:i|l|r)[\s-]?4\\b|рядн(?:ая|ый)?\s*4"),
    (EngineLayout.inline_3, r"\b(?:i|l|r)[\s-]?3\\b|рядн(?:ая|ый)?\s*3"),
    (EngineLayout.flat_6, r"\\bboxer[\s-]?6\\b|оппозитн(?:ый|ая)?\s*6"),
    (EngineLayout.flat_4, r"\\bboxer[\s-]?4\\b|оппозитн(?:ый|ая)?\s*4"),
    (EngineLayout.vr6, r"\\bvr[\s-]?6\\b"),
    (EngineLayout.vr5, r"\\bvr[\s-]?5\\b"),
]

def _listing_text(listing: Listing) -> str:
    return " ".join(x for x in (listing.title, listing.description, listing.engine_code, listing.engine_family) if x).casefold()

def enrich_listing_specs(listing: Listing) -> Listing:
    text = _listing_text(listing)
    updates: dict[str, Any] = {}
    if listing.engine_layout is None:
        for layout, pattern in _ENGINE_LAYOUT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                updates["engine_layout"] = layout
                break
    if listing.cylinders is None and updates.get("engine_layout") is not None:
        layout = updates["engine_layout"]
        try:
            updates["cylinders"] = int(layout.value.split("_")[-1])
        except ValueError:
            pass
    if listing.aspiration is None:
        if re.search(r"\b(?:twin[\s-]?turbo|bi[\s-]?turbo|битурбо|двойной\s+турбо)\b", text):
            updates["aspiration"] = AspirationType.twin_turbo
        elif re.search(r"\b(?:turbo|turbocharged|турбо|наддув)\b", text):
            updates["aspiration"] = AspirationType.turbo
        elif re.search(r"\b(?:supercharged|компрессор|supercharger)\b", text):
            updates["aspiration"] = AspirationType.supercharger
        elif re.search(r"\b(?:naturally\s+aspirated|атмосферн(?:ый|ая)|na)\b", text):
            updates["aspiration"] = AspirationType.na
    return listing.model_copy(update=updates) if updates else listing


def _get_field(listing: Listing, field: str) -> Any:
    if field == "text": return " ".join(x for x in [listing.title, listing.description] if x)
    return getattr(listing, field, None)


def _contains(actual: Any, expected: Any) -> bool:
    if actual is None: return False
    if isinstance(actual, (list, tuple, set)): return expected in actual
    return str(expected).casefold() in str(actual).casefold()


def match_condition(listing: Listing, condition: FilterCondition) -> bool:
    actual, op, expected = _get_field(listing, condition.field), condition.operator, condition.value
    if op == FilterOperator.exists: return (actual is not None) is bool(expected if expected is not None else True)
    if op == FilterOperator.eq: return actual == expected
    if op == FilterOperator.ne: return actual != expected
    if op == FilterOperator.gt: return actual is not None and actual > expected
    if op == FilterOperator.gte: return actual is not None and actual >= expected
    if op == FilterOperator.lt: return actual is not None and actual < expected
    if op == FilterOperator.lte: return actual is not None and actual <= expected
    if op == FilterOperator.in_: return actual in (expected or [])
    if op == FilterOperator.not_in: return actual not in (expected or [])
    if op == FilterOperator.contains: return _contains(actual, expected)
    if op == FilterOperator.not_contains: return not _contains(actual, expected)
    if op == FilterOperator.starts_with: return actual is not None and str(actual).casefold().startswith(str(expected).casefold())
    if op == FilterOperator.ends_with: return actual is not None and str(actual).casefold().endswith(str(expected).casefold())
    if op == FilterOperator.between: return actual is not None and isinstance(expected, (list, tuple)) and len(expected) == 2 and expected[0] <= actual <= expected[1]
    return False


def match_group(listing: Listing, group: FilterGroup) -> bool:
    results = [match_group(listing, item) if isinstance(item, FilterGroup) else match_condition(listing, item) for item in group.conditions]
    if not results: return True
    return all(results) if group.logic == "and" else any(results)


def apply_legacy_filters(listings: Iterable[Listing], query) -> list[Listing]:
    result = [enrich_listing_specs(x) for x in listings]
    pairs = [("brand","eq",query.brand),("model","eq",query.model),("generation","eq",query.generation),("body_type","eq",query.body_type),("year","gte",query.year_min),("year","lte",query.year_max),("price_rub","gte",query.price_min),("price_rub","lte",query.price_max),("mileage_km","gte",query.mileage_min),("mileage_km","lte",query.mileage_max),("displacement_l","gte",query.displacement_min_l),("displacement_l","lte",query.displacement_max_l),("cylinders","gte",query.cylinders_min),("cylinders","lte",query.cylinders_max),("power_hp","gte",query.power_min_hp),("power_hp","lte",query.power_max_hp),("fuel","eq",query.fuel),("transmission","eq",query.transmission),("drivetrain","eq",query.drivetrain),("aspiration","eq",query.aspiration),("engine_layout","eq",query.engine_layout),("torque_nm","gte",query.torque_min_nm),("torque_nm","lte",query.torque_max_nm),("region","eq",query.region)]
    conditions = [FilterCondition(field=f, operator=FilterOperator(o), value=v) for f,o,v in pairs if v is not None]
    conditions += [FilterCondition(field="text", operator=FilterOperator.contains, value=x) for x in query.keywords]
    conditions += [FilterCondition(field="text", operator=FilterOperator.not_contains, value=x) for x in query.exclude_keywords]
    for condition in conditions: result = [x for x in result if match_condition(x, condition)]
    if query.filters: result = [x for x in result if match_group(x, query.filters)]
    return result


def sort_listings(listings: Iterable[Listing], sort: str) -> list[Listing]:
    items = list(listings)
    if sort == "price_asc": return sorted(items, key=lambda x: x.price_rub if x.price_rub is not None else 10**18)
    if sort == "price_desc": return sorted(items, key=lambda x: x.price_rub if x.price_rub is not None else -1, reverse=True)
    if sort == "year_desc": return sorted(items, key=lambda x: x.year if x.year is not None else 0, reverse=True)
    if sort == "mileage_asc": return sorted(items, key=lambda x: x.mileage_km if x.mileage_km is not None else 10**18)
    return items
