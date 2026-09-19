import re
from collections.abc import Iterable
from app.domain.models import Listing

def _norm(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9а-яё]+", "", value.casefold())

def _url_key(url: str) -> str:
    return url.split("#",1)[0].rstrip("/").casefold()

def listing_key(listing: Listing) -> tuple:
    # Exact source URLs are safe; a high-confidence vehicle fingerprint clusters
    # cross-source copies without relying on seller PII.
    if listing.raw_url or listing.url:
        url = _url_key(listing.raw_url or listing.url)
        if url:
            return ("url", url)
    fingerprint = (
        _norm(listing.brand), _norm(listing.model), listing.year,
        listing.mileage_km, listing.price_rub,
    )
    if all(v not in (None, "") for v in fingerprint):
        return ("vehicle", *fingerprint)
    return ("source", listing.source, listing.source_id)

def deduplicate(listings: Iterable[Listing]) -> list[Listing]:
    result: list[Listing] = []
    seen: dict[tuple, Listing] = {}
    for listing in listings:
        key = listing_key(listing)
        if key not in seen:
            seen[key] = listing
            result.append(listing)
            continue
        # Prefer the copy with more structured data/images.
        current = seen[key]
        score = sum(v is not None for v in listing.model_dump().values()) + len(listing.images)
        old_score = sum(v is not None for v in current.model_dump().values()) + len(current.images)
        if score > old_score:
            idx = result.index(current)
            result[idx] = listing
            seen[key] = listing
    return result
