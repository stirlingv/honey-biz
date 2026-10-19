"""Gift jar pricing: the small (mini) favor and holiday jars are $8 each; the
larger 4 oz gift jar is $10. Prices live on the seeded Product rows (data
migrations), and every surface reads them from there — no hardcoded prices.
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

    def test_seeded_gift_jars_cost_eight_dollars(self):
        for name in GIFT_JAR_NAMES:
            with self.subTest(name=name):
                self.assertEqual(Product.objects.get(name=name).price, Decimal("8.00"))

    def test_gift_jar_descriptions_carry_no_stale_price(self):
        for name in GIFT_JAR_NAMES:
            with self.subTest(name=name):
                self.assertNotIn("$10", Product.objects.get(name=name).description)

    def test_order_total_uses_eight_dollar_price(self):
        self.assertEqual(self._order(quantity=24).total_price, Decimal("192.00"))

    def test_slack_alert_shows_eight_dollar_total(self):
        with patch.object(notifications, "post_message") as post, \
                patch.object(notifications, "send_admin_email"):
            notifications.notify_new_order(self._order(quantity=24))
        self.assertIn("$192.00", post.call_args.args[0])

    def test_storefront_copy_says_from_eight_dollars(self):
        # Not every gift jar is $8 any more, so the summary copy says "from".
        for name in ("home", "products"):
            with self.subTest(page=name):
                resp = self.client.get(reverse(name))
                self.assertContains(resp, "from $8 each")
                self.assertNotContains(resp, "$10 each")

    def test_product_page_and_feed_advertise_eight_dollars(self):
        detail = self.client.get(reverse("product_detail", args=[self.favor.pk]))
        self.assertContains(detail, "$8.00")
        self.assertContains(detail, '"price": "8.00"')
        self.assertContains(self.client.get(reverse("product_feed")), "8.00 USD")


class FourOunceGiftJarTests(TestCase):
    """The larger 4 oz jar (gold lid, custom lid label, ribbon) is its own
    product at $10, so its price is shown and invoiced separately."""

    def setUp(self):
        self.jar = Product.objects.get(name="4 oz Gift Jar")

    def test_seeded_at_ten_dollars_four_ounces_in_gift_section(self):
        self.assertEqual(self.jar.price, Decimal("10.00"))
        self.assertEqual(self.jar.size, "4 oz")
        self.assertEqual(self.jar.category, "gift")
        self.assertTrue(self.jar.in_stock)
        self.assertNotIn("$", self.jar.description)

    def test_order_total_and_free_shipping(self):
        order = Order.objects.create(
            first_name="Jane", last_name="Doe", email="jane@example.com", phone="(850) 555-1234",
            address="1 Honey Ln", city="Tallahassee", state="FL", zip_code="32301",
            product=self.jar, quantity=24, total_price=Decimal("0"),
        )
        self.assertEqual(order.total_price, Decimal("240.00"))
        self.assertTrue(order.ships_free)

    def test_gift_section_lists_each_jar_with_its_size_and_price(self):
        html = self.client.get(reverse("products")).content.decode()
        cards = html[html.index('<div class="proof-grid">'):]
        cards = cards[:cards.index("</section>")]
        for name, size, price in (
            ("Mini Favor Jar", "Mini", "$8.00 each"),
            ("Mini Holiday Jar", "Mini", "$8.00 each"),
            ("4 oz Gift Jar", "4 oz", "$10.00 each"),
        ):
            with self.subTest(name=name):
                card = cards[cards.index(f"<h3>{name}</h3>"):]
                card = card[:card.index("</form>")]
                self.assertIn(f'<p class="size">{size}</p>', card)
                self.assertIn(price, card)
        # Small $8 jars first, the $10 jar last.
        self.assertLess(cards.index("Mini Holiday Jar"), cards.index("4 oz Gift Jar"))

    def test_product_page_uses_its_own_photo_and_price(self):
        resp = self.client.get(reverse("product_detail", args=[self.jar.pk]))
        self.assertContains(resp, "images/live_photos/mini-jar-blue-ribbon.jpg")
        self.assertContains(resp, '"price": "10.00"')

    def test_gallery_captions_tell_mini_from_four_ounce(self):
        from shop.views import GIFT_JAR_GALLERY
        captions = {p["image"]: p["caption"] for p in GIFT_JAR_GALLERY}
        self.assertTrue(captions["images/live_photos/mini-jar-blue-ribbon.jpg"].startswith("4 oz jar"))
        for image, caption in captions.items():
            if image != "images/live_photos/mini-jar-blue-ribbon.jpg":
                with self.subTest(image=image):
                    self.assertTrue(caption.startswith("Mini"), caption)


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
