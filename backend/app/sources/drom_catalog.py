import re
from urllib.parse import urlparse

import httpx

from app.domain.catalog import CatalogNode, CatalogResponse

DROM_HOSTS = {"auto.drom.ru", "www.drom.ru", "drom.ru"}


class DromCatalogResolver:
    source = "drom"

    def _fetch(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in DROM_HOSTS:
            raise ValueError("Only public Drom URLs are supported")
        response = httpx.get(
            url,
            timeout=15.0,
            headers={"User-Agent": "CarHunter/0.1"},
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.text

    @staticmethod
    def _first_int(html: str, names: tuple[str, ...]) -> int | None:
        for name in names:
            pattern = rf'["\\']{re.escape(name)}["\\']\\s*[:=]\\s*["\\']?(\\d+)'
            match = re.search(pattern, html)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _title(html: str) -> str | None:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
        if not match:
            return None
        return re.sub(r"\\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip() or None

    def resolve_url(self, url: str) -> CatalogResponse:
        html = self._fetch(url)
        firm_id = self._first_int(html, ("firmId", "firm_id"))
        model_id = self._first_int(html, ("modelId", "model_id"))
        generation_number = self._first_int(html, ("generationNumber", "generation_number"))
        restyling_number = self._first_int(html, ("restylingNumber", "restyling_number"))

        parsed = urlparse(url)
        node_id = ":".join(
            str(x) for x in (firm_id, model_id, generation_number, restyling_number) if x is not None
        )
        if not node_id:
            node_id = parsed.path.strip("/") or "drom"

        node = CatalogNode(
            id=node_id,
            name=self._title(html) or parsed.path.strip("/") or "Drom",
            level="resolved",
            offers_count=0,
            raw={
                "url": url,
                "firmId": firm_id,
                "modelId": model_id,
                "generationNumber": generation_number,
                "restylingNumber": restyling_number,
            },
        )
        return CatalogResponse(source=self.source, state="USED", nodes=[node], total=1)


resolver = DromCatalogResolver()
