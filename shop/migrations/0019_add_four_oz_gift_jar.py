from decimal import Decimal

from django.db import migrations

# The mini favor/holiday jars stay at $8. The larger 4 oz jar (gold lid, lid
# label, satin ribbon, honey dipper) is a separate product at $10, so its
# price shows, orders, and invoices on its own.
NAME = "4 oz Gift Jar"
SIZE = "4 oz"
DESCRIPTION = (
    "A larger jar of our raw wildflower honey with a gold lid, decorative lid label, satin ribbon bow, "
    "and wooden honey dipper — a lovely keepsake favor or gift for weddings, showers, and special "
    "occasions. Bulk discounts available on larger orders."
)


def add_four_oz_gift_jar(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    Product.objects.update_or_create(
        name=NAME,
        size=SIZE,
        defaults={
            "price": Decimal("10.00"),
            "category": "gift",
            "description": DESCRIPTION,
            "in_stock": True,
        },
    )


def noop(apps, schema_editor):
    """No safe automatic reverse for seeded business data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0018_gift_jars_eight_dollars"),
    ]

    operations = [
        migrations.RunPython(add_four_oz_gift_jar, noop),
    ]
