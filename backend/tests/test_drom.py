from app.domain.models import SearchQuery
from app.sources.drom import DromAdapter


def test_drom_params_use_native_ids():
    query = SearchQuery(
        brand="BMW",
        model="5 серия",
        year_min=2010,
        price_max=2_000_000,
        source_params={"drom": {"firmId": 9, "modelId": 7, "generationNumber": 5}},
    )
    params = DromAdapter()._params(query)

    assert params["firmId"] == 9
    assert params["modelId"] == 7
    assert params["generationNumber"] == 5
    assert params["minYear"] == 2010
    assert params["maxPrice"] == 2_000_000
    assert params["page"] == 1


def test_drom_params_do_not_send_display_names_as_ids():
    query = SearchQuery(brand="BMW", model="5 серия")
    params = DromAdapter()._params(query)

    assert "firmId" not in params
    assert "modelId" not in params


def test_drom_rows_accept_common_response_shapes():
    adapter = DromAdapter()
    row = {"id": 123, "title": "BMW 530d", "price": 1500000, "year": 2012}

    assert adapter._rows({"offers": [row]}) == [row]
    assert adapter._rows({"items": {"results": [row]}}) == [row]
    assert adapter._rows([row]) == [row]


def test_drom_listing_normalization():
    listing = DromAdapter()._listing({
        "id": 123,
        "title": "BMW 530d xDrive",
        "price": 1500000,
        "year": 2012,
        "mileageKm": 180000,
        "engineVolume": 3.0,
        "enginePower": 258,
        "fuel": "diesel",
        "transmission": "automatic",
        "drive": "4WD",
        "url": "https://auto.drom.ru/bmw/5-series/123/",
    })

    assert listing.source == "drom"
    assert listing.source_id == "123"
    assert listing.price_rub == 1500000
    assert listing.year == 2012
    assert listing.mileage_km == 180000
    assert listing.displacement_l == 3.0
    assert listing.power_hp == 258
