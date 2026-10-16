from decimal import Decimal

from django.db import migrations

# Gift/mini jars drop to $8. The price is no longer repeated inside the
# description text (the cards and product page show product.price), so a future
# price change only needs to touch `price`.
FAVOR = (
    "A petite jar of our raw wildflower honey — a sweet, all-natural favor for weddings, bridal and baby "
    "showers, birthdays, parties, and thank-you gifts. Bulk discounts available on larger orders."
)

HOLIDAY = (
    "A festive little jar of our raw wildflower honey — a charming holiday gift, stocking stuffer, hostess "
    "present, or party favor. Bulk discounts available on larger orders."
)

GIFT_JARS = {
    "Mini Favor Jar": FAVOR,
    "Mini Holiday Jar": HOLIDAY,
}


def price_gift_jars_at_eight(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    for name, description in GIFT_JARS.items():
        Product.objects.filter(name=name, size="Mini").update(
            price=Decimal("8.00"), description=description,
        )


def noop(apps, schema_editor):
    """No safe automatic reverse for seeded business data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0017_order_fulfillment_alter_order_address_and_more"),
    ]

    operations = [
        migrations.RunPython(price_gift_jars_at_eight, noop),
    ]
