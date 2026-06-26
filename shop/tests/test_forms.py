"""Unit tests for shared form validation (phone, email, quantity cap)."""

from decimal import Decimal

from django.test import TestCase

from shop.forms import MAX_SELF_SERVE_QUANTITY, CallbackRequestForm, OrderForm
from shop.models import Product


class PhoneEmailNormalizationTests(TestCase):
    def _form(self, **o):
        data = dict(name="X Y", phone="850-555-1234", email="Foo@Bar.com",
                    interest="general", best_time="", message="")
        data.update(o)
        return CallbackRequestForm(data)

    def test_accepts_common_phone_formats(self):
        for raw in ["8505551234", "850-555-1234", "(850) 555-1234", "+1 850 555 1234", "1-850-555-1234"]:
            with self.subTest(raw=raw):
                form = self._form(phone=raw)
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["phone"], "(850) 555-1234")

    def test_rejects_bad_phone(self):
        form = self._form(phone="12345")
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_email_is_lowercased_and_stripped(self):
        form = self._form(email="  Mixed@Case.COM  ")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "mixed@case.com")


class OrderQuantityCapTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Wildflower Honey", description="d", price=Decimal("17.00"), size="16 oz",
        )

    def _form(self, quantity):
        return OrderForm(dict(
            first_name="J", last_name="D", email="j@d.com", phone="8505551234",
            address="1 St", city="Tally", state="FL", zip_code="32301",
            product=self.product.pk, quantity=quantity, notes="",
        ))

    def test_max_self_serve_quantity_is_allowed(self):
        self.assertTrue(self._form(MAX_SELF_SERVE_QUANTITY).is_valid())

    def test_over_cap_is_rejected(self):
        form = self._form(MAX_SELF_SERVE_QUANTITY + 1)
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_zero_quantity_is_rejected(self):
        self.assertFalse(self._form(0).is_valid())
