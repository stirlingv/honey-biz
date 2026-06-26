"""Integration tests for the honey ordering + checkout workflow."""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from shop.models import Order, Product


class OrderFlowTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Wildflower Honey", description="raw", price=Decimal("17.00"),
            size="16 oz", category="honey",
        )

    def _payload(self, **overrides):
        data = dict(
            first_name="Jane", last_name="Doe", email="Jane@Example.COM",
            phone="850-555-1234", address="1 Honey Ln", city="Tallahassee",
            state="FL", zip_code="32301", product=self.product.pk, quantity=2, notes="",
        )
        data.update(overrides)
        return data

    def _make_order(self, **overrides):
        defaults = dict(
            first_name="A", last_name="B", email="a@b.com", phone="(850) 555-1234",
            address="1 St", city="Tallahassee", state="FL", zip_code="32301",
            product=self.product, quantity=1, total_price=Decimal("17.00"),
        )
        defaults.update(overrides)
        return Order.objects.create(**defaults)

    @patch("shop.views.notify_new_order")
    def test_valid_order_creates_record_normalizes_and_notifies(self, notify):
        resp = self.client.post(reverse("order_honey"), self._payload())

        order = Order.objects.get()
        self.assertRedirects(resp, reverse("checkout_review", args=[order.id]))
        self.assertEqual(order.total_price, Decimal("34.00"))   # 17.00 x 2, computed in Model.save
        self.assertEqual(order.email, "jane@example.com")       # lowercased by form mixin
        self.assertEqual(order.phone, "(850) 555-1234")         # normalized by form mixin
        self.assertEqual(order.status, "pending")
        self.assertEqual(self.client.session["pending_order_id"], order.id)
        notify.assert_called_once_with(order)

    @patch("shop.views.notify_new_order")
    def test_invalid_order_creates_nothing(self, notify):
        resp = self.client.post(reverse("order_honey"), self._payload(email="not-an-email", phone="123"))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        notify.assert_not_called()

    @patch("shop.views.notify_new_order")
    def test_quantity_over_cap_is_rejected_and_points_to_callback(self, notify):
        resp = self.client.post(reverse("order_honey"), self._payload(quantity=25))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(resp, "callback")
        notify.assert_not_called()

    def test_get_prefills_product_and_quantity_from_querystring(self):
        resp = self.client.get(reverse("order_honey"), {"product": self.product.pk, "quantity": 5})
        form = resp.context["form"]
        self.assertEqual(str(form["product"].value()), str(self.product.pk))
        self.assertEqual(form["quantity"].value(), 5)

    def test_get_ignores_out_of_range_quantity_prefill(self):
        resp = self.client.get(reverse("order_honey"), {"product": self.product.pk, "quantity": 999})
        self.assertIsNone(resp.context["form"]["quantity"].value())

    def test_checkout_review_redirects_when_order_not_pending(self):
        order = self._make_order(status="completed")
        resp = self.client.get(reverse("checkout_review", args=[order.id]))
        self.assertRedirects(resp, reverse("order_status", args=[order.id]))

    def test_checkout_process_sends_pending_order_to_success(self):
        order = self._make_order()
        resp = self.client.get(reverse("checkout_process", args=[order.id]))
        self.assertRedirects(resp, reverse("order_success"))
