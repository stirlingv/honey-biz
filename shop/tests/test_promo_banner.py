"""Tests for the date-gated seasonal promo banner and discount display."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from shop.models import Product
from shop.templatetags.promo_extras import sale_price


class PromoBannerTests(TestCase):
    """The promo only appears while today is inside the configured window."""

    def setUp(self):
        self.today = timezone.localdate()

    def _window(self, start_offset, end_offset):
        return override_settings(
            PROMO_BANNER_START=self.today + timedelta(days=start_offset),
            PROMO_BANNER_END=self.today + timedelta(days=end_offset),
        )

    def test_bar_and_graphic_show_during_window(self):
        with self._window(-1, 1):
            response = self.client.get(reverse('home'))
        self.assertContains(response, 'promo-bar')
        self.assertContains(response, '4th-of-july')
        # The $2/jar discount offer must be advertised while the promo runs.
        self.assertContains(response, '$2')
        self.assertContains(response, 'July 5')

    def test_bar_shows_site_wide_during_window(self):
        with self._window(-1, 1):
            response = self.client.get(reverse('products'))
        self.assertContains(response, 'promo-bar')

    def test_hidden_after_window(self):
        with self._window(-10, -1):
            response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'promo-bar')
        self.assertNotContains(response, '4th-of-july')

    def test_hidden_before_window(self):
        with self._window(1, 10):
            response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'promo-bar')

    def test_inclusive_on_final_day(self):
        with self._window(-5, 0):
            response = self.client.get(reverse('home'))
        self.assertContains(response, 'promo-bar')

    @override_settings(PROMO_BANNER_START=None, PROMO_BANNER_END=None)
    def test_disabled_when_no_end_date(self):
        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'promo-bar')


class SalePriceFilterTests(TestCase):
    def test_subtracts_discount(self):
        self.assertEqual(sale_price(Decimal('17.00'), Decimal('2')), Decimal('15.00'))

    def test_floors_at_zero(self):
        self.assertEqual(sale_price(Decimal('1.00'), Decimal('2')), Decimal('0'))

    def test_passes_through_non_numeric(self):
        self.assertEqual(sale_price('n/a', Decimal('2')), 'n/a')


class DiscountDisplayTests(TestCase):
    """The $2/jar discount is shown on pricing surfaces only while promo is live."""

    def setUp(self):
        self.today = timezone.localdate()
        self.product = Product.objects.create(
            name='Wildflower Honey', size='Pint', price=Decimal('17.00'),
            category='honey', in_stock=True,
        )

    def _live(self):
        return override_settings(
            PROMO_BANNER_START=self.today - timedelta(days=1),
            PROMO_BANNER_END=self.today + timedelta(days=1),
            PROMO_DISCOUNT_PER_JAR=Decimal('2'),
        )

    def _ended(self):
        return override_settings(
            PROMO_BANNER_START=self.today - timedelta(days=10),
            PROMO_BANNER_END=self.today - timedelta(days=1),
            PROMO_DISCOUNT_PER_JAR=Decimal('2'),
        )

    def test_product_list_shows_sale_price_when_live(self):
        with self._live():
            response = self.client.get(reverse('products'))
        self.assertContains(response, 'price-sale')
        self.assertContains(response, 'price-original')
        self.assertContains(response, '$15')  # 17 - 2

    def test_product_list_full_price_after_promo(self):
        with self._ended():
            response = self.client.get(reverse('products'))
        self.assertNotContains(response, 'price-sale')
        self.assertContains(response, '$17')

    @patch("shop.views.notify_new_order")
    def test_confirmation_shows_discount_for_order(self, _mock_notify):
        order_url = reverse('order_honey')
        payload = {
            'product': self.product.pk, 'quantity': 3,
            'first_name': 'Pat', 'last_name': 'Bee',
            'email': 'pat@example.com', 'phone': '8505551234',
            'address': '1 Hive Rd', 'city': 'Tallahassee',
            'state': 'FL', 'zip_code': '32301',
        }
        with self._live():
            self.client.post(order_url, payload)
            response = self.client.get(reverse('order_success'))
        # 3 jars x $2 = $6 off, shown as a discount line.
        self.assertContains(response, '4th of July discount')
        self.assertContains(response, '6')

    @patch("shop.views.notify_new_order")
    def test_confirmation_no_discount_after_promo(self, _mock_notify):
        order_url = reverse('order_honey')
        payload = {
            'product': self.product.pk, 'quantity': 3,
            'first_name': 'Pat', 'last_name': 'Bee',
            'email': 'pat@example.com', 'phone': '8505551234',
            'address': '1 Hive Rd', 'city': 'Tallahassee',
            'state': 'FL', 'zip_code': '32301',
        }
        with self._ended():
            self.client.post(order_url, payload)
            response = self.client.get(reverse('order_success'))
        self.assertNotContains(response, '4th of July discount')
