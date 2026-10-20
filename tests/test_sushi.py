import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

from sataniawabot.services.errors import ServiceError
from sataniawabot.services.sushi import SushiService


class SushiTests(unittest.IsolatedAsyncioTestCase):
    def make_service(self, result, status=200):
        response = SimpleNamespace(status=status, json=AsyncMock(return_value=result))
        session = Mock()
        session.get.return_value = Mock(
            __aenter__=AsyncMock(return_value=response), __aexit__=AsyncMock(return_value=False),
        )
        return SushiService(session)

    async def test_online_search_filters_images_and_repeats_request(self):
        service = self.make_service({"query": {"pages": [
            {"imageinfo": [{"mime": "application/pdf", "url": "https://upload.wikimedia.org/file.pdf"}]},
            {"imageinfo": [{"mime": "image/jpeg", "url": "https://upload.wikimedia.org/sushi.jpg",
                            "descriptionurl": "https://commons.wikimedia.org/wiki/File:Sushi.jpg"}]},
        ]}})
        for _ in range(2):
            image = await service.random_image()
            self.assertEqual(image.url, "https://upload.wikimedia.org/sushi.jpg")
        self.assertEqual(service.session.get.call_count, 2)
        self.assertIn("sushi", service.session.get.call_args.kwargs["params"]["gsrsearch"])

    async def test_empty_malformed_api_error_and_http_failure(self):
        for payload, status in (({}, 200), ({"query": {"pages": None}}, 200),
                                ({"error": {"code": "badrequest"}}, 200), ({}, 503)):
            with self.subTest(payload=payload, status=status):
                with self.assertRaises(ServiceError):
                    await self.make_service(payload, status).random_image()

    async def test_timeout(self):
        service = self.make_service({})
        service.session.get.side_effect = asyncio.TimeoutError
        with self.assertRaisesRegex(ServiceError, "trop lente"):
            await service.random_image()
