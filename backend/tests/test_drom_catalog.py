from app.sources.drom_catalog import DromCatalogResolver


def test_drom_catalog_extracts_native_ids():
    html = """
    <html><head><title>BMW 5-Series F10</title></head>
    <body>
      <script>
        window.__DATA__ = {"firmId": 25805, "modelId": 5123,
        "generationNumber": 5, "restylingNumber": 1};
      </script>
    </body></html>
    """
    resolver = DromCatalogResolver()
    resolver._fetch = lambda url: html

    result = resolver.resolve_url("https://auto.drom.ru/bmw/5-series/")
    node = result.nodes[0]

    assert node.raw["firmId"] == 25805
    assert node.raw["modelId"] == 5123
    assert node.raw["generationNumber"] == 5
    assert node.raw["restylingNumber"] == 1


def test_drom_catalog_rejects_non_drom_url():
    resolver = DromCatalogResolver()
    try:
        resolver.resolve_url("https://example.com/cars")
    except ValueError as exc:
        assert "Drom" in str(exc)
    else:
        raise AssertionError("expected ValueError")
