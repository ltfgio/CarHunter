from app.sources.base import MarketplaceAdapter
from app.domain.models import Listing, SearchQuery


class AvitoAdapter(MarketplaceAdapter):
    name = "avito"
    capabilities = {"listing_search": False, "catalog": False}

    def search(self, query: SearchQuery) -> list[Listing]:
        return []
