from app.domain.models import FuelType, SearchQuery, TransmissionType, DrivetrainType
from app.sources.autoru import AutoRuAdapter


def test_autoru_url_maps_unified_filters():
    q = SearchQuery(
        brand="BMW",
        model="5 серия",
        year_min=2010,
        price_max=2_000_000,
        displacement_min_l=3.0,
        power_min_hp=250,
        mileage_max=250_000,
        fuel=FuelType.diesel,
        transmission=TransmissionType.automatic,
        drivetrain=DrivetrainType.awd,
        region="213",
    )
    url = AutoRuAdapter()._url(q)
    assert "mark_model=BMW%235" in url
    assert "year_from=2010" in url
    assert "price_to=2000000" in url
    assert "engine_volume_from=3000" in url
    assert "engine_power_from=250" in url
    assert "km_age_to=250000" in url
    assert "engine_type=DIESEL" in url
    assert "transmission=AUTOMATIC" in url
    assert "drive=ALL_WHEEL_DRIVE" in url
    assert "rid=213" in url


def test_autoru_html_parser_handles_json_ld():
    html = """
    <script type="application/ld+json">
    {"@type":"Car","name":"BMW 530d xDrive","url":"https://auto.ru/cars/used/sale/bmw/5-series/123/","offers":{"price":1500000},"productionDate":"2012","mileageFromOdometer":{"value":180000}}
    </script>
    """
    rows = AutoRuAdapter._html_rows(html)
    assert rows[0]["name"] == "BMW 530d xDrive"
    assert rows[0]["offers"]["price"] == 1500000


def test_autoru_parser_fallback_finds_offer_url():
    html = r'''<script>{"url":"https://auto.ru/cars/used/sale/bmw/5-series/123/","name":"BMW 530d","price":1500000,"year":2012,"km_age":180000}</script>'''
    rows = AutoRuAdapter._html_rows(html)
    assert rows[0]["url"].startswith("https://auto.ru/")
    assert rows[0]["price"] == "1500000"


def test_autoru_native_url_override():
    q = SearchQuery(source_params={"autoru": {"url": "https://auto.ru/cars/used/"}})
    assert AutoRuAdapter()._url(q) == "https://auto.ru/cars/used/"
