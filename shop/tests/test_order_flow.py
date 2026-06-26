"""Integration tests for the single-step honey ordering workflow.

Flow: submit the order form -> the order is saved + the business is notified
(Slack) -> a confirmation page shows the order summary. No separate review step.
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from shop.models import Order, Product


class OrderBase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Wildflower Honey", description="raw", price=Decimal("17.00"),
            size="Pint", category="honey",
        )

    def _payload(self, **overrides):
        data = dict(
            first_name="Jane", last_name="Doe", email="Jane@Example.COM",
            phone="850-555-1234", address="1 Honey Ln", city="Tallahassee",
            state="FL", zip_code="32301", product=self.product.pk, quantity=2, notes="",
        )
        data.update(overrides)
        return data


class OrderSubmissionTests(OrderBase):
    @patch("shop.views.notify_new_order")
    def test_valid_submission_creates_order_and_notifies(self, notify):
        resp = self.client.post(reverse("order_honey"), self._payload())

        order = Order.objects.get()
        self.assertRedirects(resp, reverse("order_success"))
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.total_price, Decimal("34.00"))    # 17.00 x 2
        self.assertEqual(order.email, "jane@example.com")        # lowercased by form mixin
        self.assertEqual(order.phone, "(850) 555-1234")          # normalized by form mixin
        notify.assert_called_once_with(order)

    @patch("shop.views.notify_new_order")
    def test_invalid_submission_creates_nothing(self, notify):
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

    def test_order_page_shows_summary_for_selected_product(self):
        resp = self.client.get(reverse("order_honey"), {"product": self.product.pk})
        self.assertEqual(resp.context["selected_product"], self.product)
        self.assertContains(resp, "You're ordering")
        self.assertContains(resp, self.product.name)
        self.assertNotContains(resp, "Select Product")   # dropdown replaced by summary

    def test_order_page_without_product_shows_picker(self):
        resp = self.client.get(reverse("order_honey"))
        self.assertIsNone(resp.context["selected_product"])
        self.assertContains(resp, "Select Product")


class OrderConfirmationTests(OrderBase):
    @patch("shop.views.notify_new_order")
    def test_success_page_shows_the_placed_order(self, notify):
        resp = self.client.post(reverse("order_honey"), self._payload(), follow=True)
        order = Order.objects.get()
        self.assertContains(resp, f"Order #{order.id}")
        self.assertContains(resp, "Wildflower Honey")

    def test_success_page_without_a_recent_order_is_generic(self):
        resp = self.client.get(reverse("order_success"))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Order #")
