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

    async def test_search_filters_results_and_requests_each_time(self):
        meal = {"idMeal": "53065", "strMeal": "Sushi",
                "strMealThumb": "https://www.themealdb.com/images/media/meals/sushi.jpg"}
        service = self.make_service({"meals": [None, {}, meal,
            dict(meal, strMealThumb="https://example.org/other.jpg"),
            dict(meal, strMeal="Pizza"), dict(meal, idMeal="../bad"),
        ]})
        for _ in range(2):
            image = await service.random_image()
            self.assertEqual(image.url, meal["strMealThumb"])
            self.assertEqual(image.source, "https://www.themealdb.com/meal/53065")
        self.assertEqual(service.session.get.call_count, 2)
        call = service.session.get.call_args
        self.assertEqual(call.kwargs["params"], {"s": "sushi"})
        self.assertEqual(call.kwargs["timeout"].total, 10)
        self.assertNotIn("Authorization", call.kwargs["headers"])

    async def test_empty_and_invalid_payloads(self):
        for payload in ({}, [], {"meals": None}, {"meals": []}, {"meals": "invalid"}):
            with self.subTest(payload=payload):
                with self.assertRaises(ServiceError):
                    await self.make_service(payload).random_image()

    async def test_timeout_and_invalid_json(self):
        service = self.make_service({})
        service.session.get.side_effect = asyncio.TimeoutError
        with self.assertRaisesRegex(ServiceError, "trop lent"):
            await service.random_image()
        service = self.make_service({})
        service.session.get.return_value.__aenter__.return_value.json.side_effect = ValueError
        with self.assertRaisesRegex(ServiceError, "invalide"):
            await service.random_image()

    async def test_explicit_http_errors(self):
        for status in (403, 429, 503):
            with self.subTest(status=status):
                with self.assertRaisesRegex(ServiceError, f"HTTP {status}"):
                    await self.make_service({}, status=status).random_image()
