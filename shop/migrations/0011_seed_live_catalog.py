from decimal import Decimal

from django.db import migrations


WILDFLOWER = (
    "Raw, multifloral wildflower honey from Gadsden County in Florida's Panhandle, gathered by our "
    "mite-resistant bees from a wide variety of native blooms — clover, Spanish needle, holly, palmetto, "
    "gallberry, wild blackberry, and local trees and shrubs. Typically medium-to-dark amber, it has a rich, "
    "balanced sweetness with gentle floral notes and earthy undertones — full-bodied yet approachable, with a "
    "smooth finish and more complexity than lighter, single-flower honeys. A true \"taste of place,\" its "
    "flavor shifts with the season: lighter and more delicate in spring, darker and more robust later in the "
    "year. Raw and unfiltered, so it may naturally crystallize over time. Wonderful on biscuits, toast, "
    "oatmeal, or yogurt, stirred into tea, or paired with aged cheeses."
)

FAVOR = (
    "A petite jar of our raw wildflower honey — a sweet, all-natural favor for weddings, bridal and baby "
    "showers, birthdays, parties, and thank-you gifts. $10 each, with bulk discounts on larger orders."
)

HOLIDAY = (
    "A festive little jar of our raw wildflower honey — a charming holiday gift, stocking stuffer, hostess "
    "present, or party favor. $10 each, with bulk discounts on larger orders."
)

# The catalog we actually sell. Keyed on (name, size) so this is idempotent.
LIVE_PRODUCTS = [
    {"name": "Wildflower Honey", "size": "16 oz", "price": Decimal("17.00"), "category": "honey", "description": WILDFLOWER},
    {"name": "Wildflower Honey", "size": "32 oz", "price": Decimal("30.00"), "category": "honey", "description": WILDFLOWER},
    {"name": "Mini Favor Jar", "size": "Mini", "price": Decimal("10.00"), "category": "gift", "description": FAVOR},
    {"name": "Mini Holiday Jar", "size": "Mini", "price": Decimal("10.00"), "category": "gift", "description": HOLIDAY},
]

# Placeholder varietals that contradict the single-wildflower story. We hide rather
# than delete so existing orders (Order.product is PROTECT) stay intact.
RETIRE_NAMES = ["Clover Honey", "Spring Blossom Honey", "Autumn Harvest Honey", "Raw Honeycomb"]


def seed_live_catalog(apps, schema_editor):
    """Bring any environment's Product table in line with the catalog we sell.

    Product rows live in a gitignored SQLite DB, so this seeds them on deploy
    instead of requiring manual admin edits. Images are intentionally left blank;
    the storefront falls back to the committed static jar photos.
    """
    Product = apps.get_model("shop", "Product")

    for spec in LIVE_PRODUCTS:
        obj, _ = Product.objects.get_or_create(
            name=spec["name"],
            size=spec["size"],
            defaults={
                "price": spec["price"],
                "category": spec["category"],
                "description": spec["description"],
                "in_stock": True,
            },
        )
        obj.price = spec["price"]
        obj.category = spec["category"]
        obj.description = spec["description"]
        obj.in_stock = True
        obj.save()

    # Retire placeholder varietals and the legacy 12 oz wildflower size.
    Product.objects.filter(name__in=RETIRE_NAMES).update(in_stock=False)
    Product.objects.filter(name="Wildflower Honey", size="12 oz").update(in_stock=False)


def noop(apps, schema_editor):
    """No safe automatic reverse for seeded business data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0010_product_category_alter_order_status"),
    ]

    operations = [
        migrations.RunPython(seed_live_catalog, noop),
    ]
