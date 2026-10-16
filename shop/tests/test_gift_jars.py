"""Tests for the gift jar section: the example-photo gallery and free shipping
on large gift/mini jar orders (FREE_SHIPPING_MIN_QUANTITY+ jars, delivered).
"""

import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from shop.models import FREE_SHIPPING_MIN_QUANTITY, Order, Product
from shop.services import notifications
from shop.views import GIFT_JAR_GALLERY


class GiftJarBase(TestCase):
    def setUp(self):
        self.gift = Product.objects.create(
            name="Test Favor Jar", description="mini", price=Decimal("10.00"),
            size="Mini", category="gift",
        )
        self.honey = Product.objects.create(
            name="Test Honey", description="raw", price=Decimal("17.00"),
            size="16 oz", category="honey",
        )

    def _order(self, product=None, quantity=FREE_SHIPPING_MIN_QUANTITY, **o):
        defaults = dict(
            first_name="Jane", last_name="Doe", email="jane@example.com", phone="(850) 555-1234",
            address="1 Honey Ln", city="Tallahassee", state="FL", zip_code="32301",
            product=product or self.gift, quantity=quantity, total_price=Decimal("0"),
        )
        defaults.update(o)
        return Order.objects.create(**defaults)

    def _payload(self, **overrides):
        data = dict(
            first_name="Jane", last_name="Doe", email="jane@example.com",
            phone="850-555-1234", address="1 Honey Ln", city="Tallahassee",
            state="FL", zip_code="32301", product=self.gift.pk,
            quantity=FREE_SHIPPING_MIN_QUANTITY, notes="",
        )
        data.update(overrides)
        return data


class FreeShippingRuleTests(GiftJarBase):
    def test_threshold_is_24_jars(self):
        self.assertEqual(FREE_SHIPPING_MIN_QUANTITY, 24)

    def test_delivered_gift_order_at_threshold_ships_free(self):
        self.assertTrue(self._order(quantity=FREE_SHIPPING_MIN_QUANTITY).ships_free)

    def test_gift_order_below_threshold_pays_postage(self):
        self.assertFalse(self._order(quantity=FREE_SHIPPING_MIN_QUANTITY - 1).ships_free)

    def test_full_size_honey_never_ships_free(self):
        self.assertFalse(self.honey.offers_free_shipping)
        self.assertFalse(self._order(product=self.honey).ships_free)

    def test_pickup_order_is_not_flagged_as_free_shipping(self):
        # Pickup has no postage at all; the "free shipping" flag would be noise.
        order = self._order(fulfillment="pickup", address="", city="", state="", zip_code="")
        self.assertFalse(order.ships_free)


class FreeShippingNotificationTests(GiftJarBase):
    # Patch post_message — the real outbound Slack seam (see CLAUDE.md).
    def _slack_and_email(self, order):
        with patch.object(notifications, "post_message") as post, \
                patch.object(notifications, "send_admin_email") as email:
            notifications.notify_new_order(order)
        return post.call_args.args[0], email.call_args.args[1]

    def test_qualifying_order_tells_family_not_to_charge_postage(self):
        slack, email = self._slack_and_email(self._order())
        self.assertIn("FREE SHIPPING", slack)
        self.assertIn("FREE SHIPPING", email)

    def test_non_qualifying_orders_have_no_free_shipping_flag(self):
        for order in (
            self._order(quantity=FREE_SHIPPING_MIN_QUANTITY - 1),
            self._order(product=self.honey),
        ):
            with self.subTest(product=order.product.name, qty=order.quantity):
                slack, email = self._slack_and_email(order)
                self.assertNotIn("FREE SHIPPING", slack)
                self.assertNotIn("FREE SHIPPING", email)


class FreeShippingOrderPageTests(GiftJarBase):
    @patch("shop.views.notify_new_order")
    def test_qualifying_order_confirmation_says_it_ships_free(self, notify):
        resp = self.client.post(reverse("order_honey"), self._payload(), follow=True)
        self.assertContains(resp, "ships free")
        self.assertNotContains(resp, "before postage")

    @patch("shop.views.notify_new_order")
    def test_small_gift_order_confirmation_still_mentions_postage(self, notify):
        resp = self.client.post(
            reverse("order_honey"), self._payload(quantity=FREE_SHIPPING_MIN_QUANTITY - 1), follow=True,
        )
        self.assertContains(resp, "before postage")
        self.assertNotContains(resp, "ships free")

    def test_gift_order_summary_advertises_free_shipping(self):
        resp = self.client.get(reverse("order_honey"), {"product": self.gift.pk})
        self.assertContains(resp, f"Free shipping on {FREE_SHIPPING_MIN_QUANTITY}+ jars")

    def test_honey_order_summary_does_not_advertise_free_shipping(self):
        resp = self.client.get(reverse("order_honey"), {"product": self.honey.pk})
        self.assertNotContains(resp, "Free shipping on")

    def test_live_total_knows_which_products_ship_free(self):
        resp = self.client.get(reverse("order_honey"))
        eligible = json.loads(resp.context["free_shipping_products"])
        self.assertIn(str(self.gift.pk), eligible)
        self.assertNotIn(str(self.honey.pk), eligible)
        self.assertEqual(resp.context["free_shipping_min"], FREE_SHIPPING_MIN_QUANTITY)


class GiftSectionTests(GiftJarBase):
    def setUp(self):
        super().setUp()
        self.resp = self.client.get(reverse("products"))

    def test_section_advertises_free_shipping(self):
        self.assertContains(self.resp, f"Free shipping on orders of {FREE_SHIPPING_MIN_QUANTITY}+ jars")

    def test_quantity_picker_labels_the_free_shipping_quantity(self):
        self.assertContains(self.resp, f"{FREE_SHIPPING_MIN_QUANTITY} — free shipping")
        self.assertNotContains(self.resp, f">{FREE_SHIPPING_MIN_QUANTITY - 1} — free shipping")

    def test_gallery_shows_every_example_photo_with_controls(self):
        self.assertContains(self.resp, "data-gallery")
        self.assertContains(self.resp, 'class="gift-gallery-slide"', count=len(GIFT_JAR_GALLERY))
        for photo in GIFT_JAR_GALLERY:
            self.assertContains(self.resp, photo["image"])
            self.assertContains(self.resp, escape(photo["caption"]))
        self.assertContains(self.resp, 'aria-label="Next photo"')
        self.assertContains(self.resp, 'aria-label="Previous photo"')

    def test_gallery_has_multiple_photos_and_includes_the_new_jar(self):
        self.assertGreater(len(GIFT_JAR_GALLERY), 1)
        self.assertIn(
            "images/live_photos/mini-jar-blue-ribbon.jpg", [p["image"] for p in GIFT_JAR_GALLERY],
        )

    def test_gallery_photos_exist_and_have_alt_text(self):
        for photo in GIFT_JAR_GALLERY:
            with self.subTest(image=photo["image"]):
                self.assertIsNotNone(finders.find(photo["image"]), "missing static file")
                self.assertTrue(photo["alt"].strip())

    def test_order_cards_have_no_photo_all_photos_live_in_gallery(self):
        # Card photos duplicated gallery slides and cost ~a screen of scrolling
        # each on phones; the cards are just name, price, quantity, Order Now.
        html = self.resp.content.decode()
        cards = html[html.index('<div class="proof-grid">'):]
        cards = cards[:cards.index("</section>")]
        self.assertIn("Order Now", cards)
        self.assertNotIn("<img", cards)
        gallery_images = [p["image"] for p in GIFT_JAR_GALLERY]
        for image in ("images/live_photos/mini-jar-wedding.jpeg", "images/live_photos/mini-jar-holidays.jpeg"):
            self.assertIn(image, gallery_images)
