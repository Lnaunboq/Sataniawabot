"""Traduction DeepL avec une session HTTP asynchrone réutilisée."""
import asyncio
import aiohttp
from .errors import NotConfigured, ServiceError


class DeepLService:
    def __init__(self, api_key, session):
        self.api_key = api_key
        self.session = session
        host = (
            "https://api-free.deepl.com"
            if api_key.endswith(":fx") else "https://api.deepl.com"
        )
        self.url = host + "/v2/translate"

    async def translate(self, text, target_lang):
        if not self.api_key:
            raise NotConfigured("DeepL n’est pas configuré.")
        try:
            async with self.session.post(
                self.url,
                headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"},
                data={"text": text, "target_lang": target_lang.upper()},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise ServiceError(f"Erreur DeepL : HTTP {response.status}.")
                result = await response.json()
                translation = result["translations"][0]["text"]
                if not isinstance(translation, str) or not translation:
                    raise ValueError("Traduction vide")
                return translation
        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise ServiceError("DeepL est indisponible ou le délai d’attente est dépassé.") from None
        except (KeyError, IndexError, TypeError, ValueError):
            raise ServiceError("DeepL a renvoyé une réponse invalide.") from None
