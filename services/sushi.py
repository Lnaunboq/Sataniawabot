"""Recherche d’images de sushi sur Wikimedia Commons, sans stockage local."""
import asyncio
import random
from dataclasses import dataclass

import aiohttp

from .errors import ServiceError


@dataclass(frozen=True)
class SushiImage:
    url: str
    source: str


class SushiService:
    def __init__(self, session):
        self.session = session

    async def random_image(self):
        try:
            async with self.session.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query", "format": "json", "formatversion": "2",
                    "generator": "search", "gsrsearch": "sushi filetype:bitmap",
                    "gsrnamespace": "6", "gsrlimit": "30",
                    "prop": "imageinfo", "iiprop": "url|mime",
                },
                headers={"User-Agent": "SataniawaBot/1.0 (Discord sushi command)"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise ServiceError("La recherche d’images de sushi est indisponible. Réessaie plus tard.")
                result = await response.json()
            if "error" in result:
                raise ServiceError("La recherche d’images de sushi est indisponible. Réessaie plus tard.")
            images = []
            for page in result.get("query", {}).get("pages", []):
                for info in page.get("imageinfo", []):
                    url = info.get("url", "")
                    source = info.get("descriptionurl", "")
                    if (
                        info.get("mime") in {"image/jpeg", "image/png", "image/webp", "image/gif"}
                        and isinstance(url, str) and url.startswith("https://upload.wikimedia.org/")
                        and isinstance(source, str) and source.startswith("https://commons.wikimedia.org/")
                    ):
                        images.append(SushiImage(url, source))
            if not images:
                raise ServiceError("Aucune image de sushi trouvée. Réessaie plus tard.")
            return random.choice(images)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise ServiceError("La recherche d’images de sushi est indisponible ou trop lente. Réessaie plus tard.") from None
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ServiceError("La recherche d’images de sushi a renvoyé une réponse invalide.") from None
