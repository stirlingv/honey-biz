from decimal import Decimal

from django.db import migrations

# Gift jars go back to $10 and are labeled with their real size, 4 oz
# (previously the generic "Mini"). Descriptions don't mention price or size,
# so only these two fields change.
GIFT_JAR_NAMES = ["Mini Favor Jar", "Mini Holiday Jar"]


def price_gift_jars_at_ten_four_oz(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    Product.objects.filter(name__in=GIFT_JAR_NAMES, category="gift").update(
        price=Decimal("10.00"), size="4 oz",
    )


def noop(apps, schema_editor):
    """No safe automatic reverse for seeded business data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0018_gift_jars_eight_dollars"),
    ]

    operations = [
        migrations.RunPython(price_gift_jars_at_ten_four_oz, noop),
    ]
