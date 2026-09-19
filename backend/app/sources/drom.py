from app.sources.base import MarketplaceAdapter
from app.domain.models import Listing, SearchQuery

class DromAdapter(MarketplaceAdapter):
    name = "drom"
    def search(self, query: SearchQuery) -> list[Listing]:
        return []
