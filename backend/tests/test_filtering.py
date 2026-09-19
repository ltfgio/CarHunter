from app.domain.models import FilterCondition, FilterGroup, FilterOperator, Listing, SearchQuery
from app.engine.filtering import apply_legacy_filters, match_group, sort_listings


def car(**kwargs):
    base = dict(source="test", source_id="1", url="https://example.test/1", title="BMW 550i F10 V8 twin turbo", price_rub=1800000, year=2012, mileage_km=140000, brand="BMW", model="550i", displacement_l=4.4, cylinders=8, power_hp=407, drivetrain="awd", aspiration="twin_turbo", description="M-package, xDrive")
    base.update(kwargs)
    return Listing(**base)


def test_nested_or_and_not_contains():
    q = FilterGroup(logic="and", conditions=[FilterGroup(logic="or", conditions=[FilterCondition(field="model", operator=FilterOperator.eq, value="550i"), FilterCondition(field="model", operator=FilterOperator.eq, value="M5")]), FilterCondition(field="power_hp", operator=FilterOperator.gte, value=400), FilterCondition(field="text", operator=FilterOperator.not_contains, value="битый")])
    assert match_group(car(), q)
    assert not match_group(car(model="M3", power_hp=450), q)


def test_range_and_keywords():
    result = apply_legacy_filters([car(), car(price_rub=3200000, year=2008)], SearchQuery(price_max=2500000, year_min=2010, keywords=["V8"]))
    assert len(result) == 1


def test_sort():
    items = [car(price_rub=2_000_000), car(price_rub=1_000_000)]
    assert sort_listings(items, "price_asc")[0].price_rub == 1_000_000
