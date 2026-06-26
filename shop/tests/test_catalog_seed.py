from django.test import TestCase

from shop.models import Product


class SeedLiveCatalogTests(TestCase):
    """The 0011 data migration should seed the catalog we actually sell."""

    def test_storefront_honey_seeded(self):
        honey = Product.objects.filter(in_stock=True, category="honey")
        self.assertEqual(
            set(honey.values_list("name", "size")),
            {("Wildflower Honey", "16 oz"), ("Wildflower Honey", "32 oz")},
        )

    def test_storefront_gift_jars_seeded(self):
        gift = Product.objects.filter(in_stock=True, category="gift")
        self.assertEqual(
            set(gift.values_list("name", "size")),
            {("Mini Favor Jar", "Mini"), ("Mini Holiday Jar", "Mini")},
        )

    def test_gift_jars_priced_at_ten(self):
        for name in ("Mini Favor Jar", "Mini Holiday Jar"):
            self.assertEqual(str(Product.objects.get(name=name).price), "10.00")

    def test_placeholder_varietals_not_in_storefront(self):
        for name in ("Clover Honey", "Spring Blossom Honey", "Autumn Harvest Honey", "Raw Honeycomb"):
            self.assertFalse(
                Product.objects.filter(name=name, in_stock=True).exists(),
                f"{name} should not be sold in the storefront",
            )
