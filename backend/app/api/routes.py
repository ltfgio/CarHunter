from fastapi import APIRouter
from app.domain.models import SearchQuery, SearchResponse
from app.sources.registry import adapters

router = APIRouter(prefix="/api")

@router.get("/sources")
def sources() -> list[str]:
    return sorted(adapters)

@router.get("/search", response_model=SearchResponse)
def search(query: SearchQuery) -> SearchResponse:
    # Source adapters will be wired here as integrations are implemented.
    return SearchResponse(query=query, total=0, listings=[])
