import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from app.config import Settings
from app.main import app, settings
from app.services.api_client import create_api_client


class ApplicationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_homepage_renders_configured_app_name(self):
        response = await self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.app_name, response.text)

    async def test_each_feature_has_a_rendered_starter_page(self):
        feature_pages = (
            ("/auth/login", "Area fitur: Auth"),
            ("/customer/", "Area fitur: Customer"),
            ("/driver/", "Area fitur: Driver"),
            ("/chat/", "Area fitur: Chat"),
            ("/admin/", "Area fitur: Admin"),
        )

        for path, heading in feature_pages:
            with self.subTest(path=path):
                response = await self.client.get(path)

                self.assertEqual(response.status_code, 200)
                self.assertIn(heading, response.text)

    async def test_static_stylesheet_is_served(self):
        response = await self.client.get("/static/css/style.css")

        self.assertEqual(response.status_code, 200)
        self.assertIn(".feature-list", response.text)

    async def test_driver_dashboard_renders_empty_open_orders_state(self):
        configured_settings = Settings(
            _env_file=None,
            backend_api_base_url="https://backend.example.test",
        )

        def mock_api_client(_settings):
            def handler(request):
                if request.url.path == "/api/v1/driver/availability":
                    return httpx.Response(200, json={"availability": "ACTIVE"})
                if request.url.path == "/api/v1/orders/available":
                    return httpx.Response(200, json={"orders": []})
                return httpx.Response(404, json={"detail": "Tidak ditemukan"})

            return httpx.AsyncClient(
                transport=httpx.MockTransport(handler),
                base_url="https://backend.example.test",
            )

        with (
            patch("app.router.driver.get_settings", return_value=configured_settings),
            patch("app.router.driver.create_api_client", side_effect=mock_api_client),
        ):
            response = await self.client.get(
                "/driver/dashboard",
                cookies={"access_token": "test-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Belum ada pesanan tersedia", response.text)
        self.assertIn("ACTIVE", response.text)

    async def test_driver_accept_order_uses_contract_endpoint(self):
        configured_settings = Settings(
            _env_file=None,
            backend_api_base_url="https://backend.example.test",
        )

        def mock_api_client(_settings):
            def handler(request):
                self.assertEqual(request.url.path, "/api/v1/orders/101/accept")
                self.assertEqual(
                    request.headers["authorization"],
                    "Bearer test-token",
                )
                return httpx.Response(
                    200,
                    json={"message": "Order berhasil diterima", "order": {"id": 101, "status": "ACCEPTED"}},
                )

            return httpx.AsyncClient(
                transport=httpx.MockTransport(handler),
                base_url="https://backend.example.test",
            )

        with (
            patch("app.router.driver.get_settings", return_value=configured_settings),
            patch("app.router.driver.create_api_client", side_effect=mock_api_client),
        ):
            response = await self.client.post(
                "/driver/orders/101/accept",
                cookies={"access_token": "test-token"},
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 303)
        self.assertIn("success=Order+berhasil+diterima", response.headers["location"])

    def test_api_client_requires_a_configured_backend_url(self):
        settings_without_api = Settings(
            _env_file=None,
            backend_api_base_url=None,
        )

        with self.assertRaisesRegex(RuntimeError, "APP_BACKEND_API_BASE_URL"):
            create_api_client(settings_without_api)

    async def test_api_client_uses_the_configured_backend_url(self):
        configured_settings = Settings(
            _env_file=None,
            backend_api_base_url="https://backend.example.test/api/",
        )
        api_client = create_api_client(configured_settings)

        try:
            self.assertEqual(str(api_client.base_url), "https://backend.example.test/api/")
        finally:
            await api_client.aclose()

    def test_settings_read_the_documented_environment_variables(self):
        with patch.dict(
            "os.environ",
            {
                "APP_NAME": "Test App",
                "APP_ENV": "test",
                "APP_DEBUG": "false",
            },
        ):
            configured_settings = Settings(_env_file=None)

        self.assertEqual(configured_settings.app_name, "Test App")
        self.assertEqual(configured_settings.environment, "test")
        self.assertFalse(configured_settings.debug)

    def test_example_environment_file_can_be_copied_as_is(self):
        example_settings = Settings(
            _env_file=Path(__file__).resolve().parents[1] / ".env.example",
        )

        self.assertEqual(example_settings.app_name, "AnterinDong")
        self.assertTrue(example_settings.debug)
        self.assertIsNone(example_settings.backend_api_base_url)


if __name__ == "__main__":
    unittest.main()
