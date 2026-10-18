"""Gift jars are 4 oz and sell for $10 each. The price lives on the seeded Product rows
(data migrations), and every surface reads it from there — no hardcoded price
copy left behind.
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from shop.models import Order, Product
from shop.services import notifications

GIFT_JAR_NAMES = ("Mini Favor Jar", "Mini Holiday Jar")


class GiftJarPriceTests(TestCase):
    def setUp(self):
        self.favor = Product.objects.get(name="Mini Favor Jar")

    def _order(self, quantity=24):
        return Order.objects.create(
            first_name="Jane", last_name="Doe", email="jane@example.com", phone="(850) 555-1234",
            address="1 Honey Ln", city="Tallahassee", state="FL", zip_code="32301",
            product=self.favor, quantity=quantity, total_price=Decimal("0"),
        )

    def test_seeded_gift_jars_cost_ten_dollars(self):
        for name in GIFT_JAR_NAMES:
            with self.subTest(name=name):
                self.assertEqual(Product.objects.get(name=name).price, Decimal("10.00"))

    def test_gift_jar_descriptions_carry_no_stale_price(self):
        for name in GIFT_JAR_NAMES:
            with self.subTest(name=name):
                description = Product.objects.get(name=name).description
                self.assertNotIn("$10", description)
                self.assertNotIn("$8", description)

    def test_order_total_uses_ten_dollar_price(self):
        self.assertEqual(self._order(quantity=24).total_price, Decimal("240.00"))

    def test_slack_alert_shows_ten_dollar_total(self):
        with patch.object(notifications, "post_message") as post, \
                patch.object(notifications, "send_admin_email"):
            notifications.notify_new_order(self._order(quantity=24))
        self.assertIn("$240.00", post.call_args.args[0])

    def test_storefront_copy_shows_ten_dollars(self):
        for name in ("home", "products"):
            with self.subTest(page=name):
                resp = self.client.get(reverse(name))
                self.assertContains(resp, "$10 each")
                self.assertNotContains(resp, "$8 each")

    def test_product_page_and_feed_advertise_ten_dollars(self):
        detail = self.client.get(reverse("product_detail", args=[self.favor.pk]))
        self.assertContains(detail, "$10.00")
        self.assertContains(detail, '"price": "10.00"')
        self.assertContains(self.client.get(reverse("product_feed")), "10.00 USD")


class GiftJarSizeTests(TestCase):
    """Gift jars are 4 oz; the size shows everywhere product.size is shown,
    including on the gift section order cards."""

    def test_seeded_gift_jars_are_four_ounces(self):
        for name in GIFT_JAR_NAMES:
            with self.subTest(name=name):
                self.assertEqual(Product.objects.get(name=name).size, "4 oz")

    def test_gift_cards_show_size(self):
        resp = self.client.get(reverse("products"))
        html = resp.content.decode()
        cards = html[html.index('<div class="proof-grid">'):]
        cards = cards[:cards.index("</section>")]
        self.assertEqual(cards.count('<p class="size">4 oz</p>'), len(GIFT_JAR_NAMES))

    def test_product_page_shows_size(self):
        favor = Product.objects.get(name="Mini Favor Jar")
        resp = self.client.get(reverse("product_detail", args=[favor.pk]))
        self.assertContains(resp, '<p class="product-detail-size">4 oz</p>', html=True)


class OrderRepricingTests(TestCase):
    """A price change must not silently rewrite orders already placed: the
    admin invoice details (copied into QuickBooks) read total_price."""

    def setUp(self):
        self.product = Product.objects.create(
            name="Test Jar", description="d", price=Decimal("10.00"), size="Mini", category="gift",
        )
        self.order = Order.objects.create(
            first_name="Jane", last_name="Doe", email="jane@example.com", phone="(850) 555-1234",
            address="1 Honey Ln", city="Tallahassee", state="FL", zip_code="32301",
            product=self.product, quantity=3, total_price=Decimal("0"),
        )
        self.product.price = Decimal("8.00")
        self.product.save()
        self.order.refresh_from_db()

    def test_resaving_existing_order_keeps_price_it_was_placed_at(self):
        # e.g. changing status from the admin order list (a full save)
        self.order.status = "completed"
        self.order.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_price, Decimal("30.00"))

    def test_changing_quantity_reprices_at_current_price(self):
        self.order.quantity = 5
        self.order.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_price, Decimal("40.00"))

    def test_changing_product_reprices(self):
        other = Product.objects.create(
            name="Other Jar", description="d", price=Decimal("12.00"), size="Mini", category="gift",
        )
        self.order.product = other
        self.order.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_price, Decimal("36.00"))
