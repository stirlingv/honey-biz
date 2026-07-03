"""Structured data helpers: Product JSON-LD and the Google Merchant feed.

Both read the same live catalog (``Product``) so search engines and Google
Merchant Center stay in sync with the site automatically — there is nothing to
regenerate by hand when the catalog changes.
"""

from decimal import Decimal


def _absolute(base_url, path):
    return f"{base_url.rstrip('/')}{path}"


def product_offer_price(product, promo_discount=Decimal('0')):
    """The advertised price for a product, promo discount applied and floored at 0."""
    price = product.price - promo_discount
    return price if price > 0 else Decimal('0')


def product_jsonld(product, base_url, promo_discount=Decimal('0')):
    """Return a schema.org ``Product`` dict for a product detail page.

    Emitting price + availability makes each jar eligible for Google's free
    product rich results. Returned as a plain dict so the view can ``json.dumps``
    it (which handles all the escaping); callers should render it with ``|safe``.
    """
    price = product_offer_price(product, promo_discount)
    availability = 'https://schema.org/InStock' if product.in_stock else 'https://schema.org/OutOfStock'
    data = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'name': f'{product.name} — {product.size}',
        'description': product.description,
        'category': product.get_category_display(),
        'brand': {
            '@type': 'Brand',
            'name': 'Bear Creek Apiaries & Honey LLC',
        },
        'url': _absolute(base_url, product.get_absolute_url()),
        'offers': {
            '@type': 'Offer',
            'price': f'{price:.2f}',
            'priceCurrency': 'USD',
            'availability': availability,
            'url': _absolute(base_url, product.get_absolute_url()),
            'seller': {
                '@id': f'{base_url.rstrip("/")}/#business',
            },
        },
    }
    if product.image:
        data['image'] = _absolute(base_url, product.image.url)
    return data


def merchant_feed_items(products, base_url, promo_discount=Decimal('0')):
    """Build the row data for the Google Merchant product feed.

    Returns a list of dicts consumed by ``product_feed.xml``. Only in-stock
    products should be passed in; Google rejects items without a resolvable
    price and availability.
    """
    items = []
    for product in products:
        price = product_offer_price(product, promo_discount)
        items.append({
            'id': product.pk,
            'title': f'{product.name} — {product.size}',
            'description': product.description,
            'link': _absolute(base_url, product.get_absolute_url()),
            'image_link': _absolute(base_url, product.image.url) if product.image else '',
            'availability': 'in_stock' if product.in_stock else 'out_of_stock',
            'price': f'{price:.2f} USD',
            'brand': 'Bear Creek Apiaries & Honey LLC',
            'condition': 'new',
        })
    return items
