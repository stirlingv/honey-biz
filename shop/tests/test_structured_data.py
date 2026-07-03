"""Tests for Product JSON-LD (rich results) and the Google Merchant feed.

Both read the live catalog so search/Shopping listings stay in sync with the
site. Promo pricing is display-only but should still flow through to the
advertised price in both surfaces.
"""

import json
from datetime import date
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from shop.models import Product

# A promo window that is always "off" / always "on" regardless of the real date.
PROMO_OFF = dict(PROMO_BANNER_END=None)
PROMO_ON = dict(
    PROMO_BANNER_START=date(2000, 1, 1),
    PROMO_BANNER_END=date(2999, 1, 1),
    PROMO_DISCOUNT_PER_JAR=Decimal('2'),
)


class ProductJsonLdTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Wildflower Honey", description="Raw and local", price=Decimal("17.00"),
            size="Pint", category="honey",
        )

    def _jsonld(self, response):
        """Pull the Product JSON-LD block out of the rendered page."""
        marker = '<script type="application/ld+json">'
        html = response.content.decode()
        # The Product block is the one emitted by the structured_data template block.
        start = html.index(marker, html.index('"@type": "Product"') - 200)
        body = html[start + len(marker):]
        return json.loads(body[:body.index('</script>')])

    @override_settings(**PROMO_OFF)
    def test_detail_page_includes_product_jsonld(self):
        resp = self.client.get(reverse('product_detail', args=[self.product.pk]))
        data = self._jsonld(resp)
        self.assertEqual(data['@type'], 'Product')
        self.assertIn('Wildflower Honey', data['name'])
        self.assertEqual(data['offers']['price'], '17.00')
        self.assertEqual(data['offers']['priceCurrency'], 'USD')
        self.assertEqual(data['offers']['availability'], 'https://schema.org/InStock')

    @override_settings(**PROMO_ON)
    def test_jsonld_reflects_promo_price(self):
        resp = self.client.get(reverse('product_detail', args=[self.product.pk]))
        data = self._jsonld(resp)
        self.assertEqual(data['offers']['price'], '15.00')  # 17.00 - 2.00 promo

    @override_settings(**PROMO_OFF)
    def test_out_of_stock_marked_in_jsonld(self):
        self.product.in_stock = False
        self.product.save()
        resp = self.client.get(reverse('product_detail', args=[self.product.pk]))
        data = self._jsonld(resp)
        self.assertEqual(data['offers']['availability'], 'https://schema.org/OutOfStock')


class MerchantFeedTests(TestCase):
    def setUp(self):
        self.in_stock = Product.objects.create(
            name="Wildflower Honey", description="Raw and local", price=Decimal("17.00"),
            size="Pint", category="honey",
        )
        self.retired = Product.objects.create(
            name="Old Batch", description="gone", price=Decimal("9.00"),
            size="Half Pint", category="honey", in_stock=False,
        )

    @override_settings(**PROMO_OFF)
    def test_feed_lists_in_stock_products_only(self):
        resp = self.client.get(reverse('product_feed'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/xml')
        body = resp.content.decode()
        self.assertIn('Wildflower Honey', body)
        self.assertNotIn('Old Batch', body)

    @override_settings(**PROMO_OFF)
    def test_feed_item_has_required_merchant_fields(self):
        body = self.client.get(reverse('product_feed')).content.decode()
        self.assertIn(f'<g:id>{self.in_stock.pk}</g:id>', body)
        self.assertIn('<g:price>17.00 USD</g:price>', body)
        self.assertIn('<g:availability>in_stock</g:availability>', body)
        self.assertIn('<g:condition>new</g:condition>', body)

    @override_settings(**PROMO_ON)
    def test_feed_price_reflects_promo(self):
        body = self.client.get(reverse('product_feed')).content.decode()
        self.assertIn('<g:price>15.00 USD</g:price>', body)  # 17.00 - 2.00
