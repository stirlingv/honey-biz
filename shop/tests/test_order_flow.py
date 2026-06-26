"""Integration tests for the honey ordering + checkout workflow.

The flow is: submit form -> draft order (no notification) -> review ->
confirm (POST) -> pending order + business notified -> success.
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

    def _order(self, **overrides):
        defaults = dict(
            first_name="A", last_name="B", email="a@b.com", phone="(850) 555-1234",
            address="1 St", city="Tallahassee", state="FL", zip_code="32301",
            product=self.product, quantity=1, total_price=Decimal("17.00"), status="draft",
        )
        defaults.update(overrides)
        return Order.objects.create(**defaults)


class OrderSubmissionTests(OrderBase):
    @patch("shop.views.notify_new_order")
    def test_valid_submission_creates_draft_without_notifying(self, notify):
        resp = self.client.post(reverse("order_honey"), self._payload())

        order = Order.objects.get()
        self.assertEqual(order.status, "draft")
        self.assertRedirects(resp, reverse("checkout_review", args=[order.id]))
        self.assertEqual(order.total_price, Decimal("34.00"))   # 17.00 x 2
        self.assertEqual(order.email, "jane@example.com")       # lowercased by form mixin
        self.assertEqual(order.phone, "(850) 555-1234")         # normalized by form mixin
        self.assertEqual(self.client.session["pending_order_id"], order.id)
        notify.assert_not_called()                              # not until the customer confirms

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


class CheckoutConfirmationTests(OrderBase):
    def test_review_renders_for_draft_order(self):
        order = self._order()
        self.assertEqual(self.client.get(reverse("checkout_review", args=[order.id])).status_code, 200)

    def test_review_redirects_when_order_already_submitted(self):
        order = self._order(status="pending")
        resp = self.client.get(reverse("checkout_review", args=[order.id]))
        self.assertRedirects(resp, reverse("order_status", args=[order.id]))

    @patch("shop.views.notify_new_order")
    def test_confirm_marks_pending_notifies_and_redirects_to_success(self, notify):
        order = self._order()
        resp = self.client.post(reverse("checkout_process", args=[order.id]))

        order.refresh_from_db()
        self.assertEqual(order.status, "pending")
        self.assertRedirects(resp, reverse("order_success"))
        notify.assert_called_once_with(order)

    @patch("shop.views.notify_new_order")
    def test_get_to_process_does_not_submit_or_notify(self, notify):
        order = self._order()
        resp = self.client.get(reverse("checkout_process", args=[order.id]))

        order.refresh_from_db()
        self.assertEqual(order.status, "draft")                 # unchanged — GET never mutates
        self.assertRedirects(resp, reverse("checkout_review", args=[order.id]))
        notify.assert_not_called()

    @patch("shop.views.notify_new_order")
    def test_confirming_an_already_submitted_order_is_idempotent(self, notify):
        order = self._order(status="pending")
        resp = self.client.post(reverse("checkout_process", args=[order.id]))

        self.assertRedirects(resp, reverse("order_status", args=[order.id]))
        notify.assert_not_called()                              # no duplicate notification
