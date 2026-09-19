from app.sources.base import MarketplaceAdapter
from app.domain.models import Listing, SearchQuery

class AutoRuAdapter(MarketplaceAdapter):
    name = "autoru"
    def search(self, query: SearchQuery) -> list[Listing]:
        return []
