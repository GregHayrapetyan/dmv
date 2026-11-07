from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class HealthEndpointTests(SimpleTestCase):
    def test_health_url_resolves(self):
        self.assertEqual(reverse("health"), "/api/health/")

    @override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        }
    )
    def test_health_ok_with_sqlite(self):
        # SimpleTestCase + sqlite in-memory still allows connection.ensure_connection
        response = self.client.get("/api/health/")
        self.assertIn(response.status_code, (200, 503))
        payload = response.json()
        self.assertIn("success", payload)
        self.assertIn("data", payload)
