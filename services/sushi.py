"""Images de sushi via TheMealDB, sans stockage local ni identifiants personnels."""
import asyncio
import logging
import random
from dataclasses import dataclass
from urllib.parse import urlsplit

import aiohttp

from .errors import ServiceError

logger = logging.getLogger(__name__)


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
                "https://www.themealdb.com/api/json/v1/1/search.php",
                params={"s": "sushi"},
                headers={"User-Agent": "SataniawaBot/1.0"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    logger.warning("Recherche sushi : TheMealDB HTTP %s", response.status)
                    if response.status == 429:
                        raise ServiceError("TheMealDB limite les requêtes (HTTP 429). Réessaie plus tard.")
                    raise ServiceError(f"TheMealDB est indisponible (HTTP {response.status}). Réessaie plus tard.")
                result = await response.json()
            meals = result["meals"]
            if meals is None:
                meals = []
            if not isinstance(meals, list):
                raise ValueError("Liste de recettes invalide")
            images = []
            for meal in meals:
                if not isinstance(meal, dict):
                    continue
                url = meal.get("strMealThumb")
                meal_id = meal.get("idMeal")
                name = meal.get("strMeal")
                if not isinstance(url, str):
                    continue
                parsed = urlsplit(url)
                if (
                    parsed.scheme == "https"
                    and parsed.netloc in {"www.themealdb.com", "themealdb.com"}
                    and parsed.path.startswith("/images/media/meals/")
                    and isinstance(meal_id, str) and meal_id.isascii() and meal_id.isdigit()
                    and isinstance(name, str) and "sushi" in name.casefold()
                ):
                    images.append(SushiImage(url, f"https://www.themealdb.com/meal/{meal_id}"))
            if not images:
                raise ServiceError("Aucune image de sushi trouvée sur TheMealDB. Réessaie plus tard.")
            return random.choice(images)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise ServiceError("TheMealDB est indisponible ou trop lent. Réessaie plus tard.") from None
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ServiceError("TheMealDB a renvoyé une réponse invalide.") from None
