"""Smoke tests: every public page renders without error."""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from shop.models import Order, Product


class StaticPageSmokeTests(TestCase):
    def test_simple_get_pages_return_200(self):
        names = [
            "home", "about", "products", "order_honey", "order_success",
            "nuke_request", "nuke_success",
            "pollination_services", "pollination_success",
            "bee_removal", "bee_removal_success",
            "callback_request", "callback_success",
            "privacy_policy", "terms_of_service",
        ]
        for name in names:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_robots_txt(self):
        resp = self.client.get("/robots.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/plain")
        self.assertIn("Sitemap:", resp.content.decode())

    def test_sitemap_xml(self):
        resp = self.client.get(reverse("sitemap"))
        self.assertEqual(resp.status_code, 200)


class DynamicPageSmokeTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test Honey", description="d", price=Decimal("10.00"), size="16 oz",
        )
        self.order = Order.objects.create(
            first_name="A", last_name="B", email="a@b.com", phone="(850) 555-1234",
            address="1 St", city="Tallahassee", state="FL", zip_code="32301",
            product=self.product, quantity=1, total_price=Decimal("10.00"), status="draft",
        )

    def test_product_detail_renders(self):
        resp = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test Honey")

    def test_missing_product_returns_404(self):
        self.assertEqual(self.client.get(reverse("product_detail", args=[999999])).status_code, 404)

    def test_checkout_review_renders_for_draft_order(self):
        self.assertEqual(self.client.get(reverse("checkout_review", args=[self.order.pk])).status_code, 200)

    def test_order_status_renders(self):
        self.assertEqual(self.client.get(reverse("order_status", args=[self.order.pk])).status_code, 200)
