from app.sources.base import MarketplaceAdapter
from app.domain.models import Listing, SearchQuery

class AvitoAdapter(MarketplaceAdapter):
    name = "avito"
    def search(self, query: SearchQuery) -> list[Listing]:
        return []
