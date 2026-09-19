from abc import ABC, abstractmethod
from app.domain.models import Listing, SearchQuery

class MarketplaceAdapter(ABC):
    name: str
    @abstractmethod
    def search(self, query: SearchQuery) -> list[Listing]:
        raise NotImplementedError
