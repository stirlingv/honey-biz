from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0006_order_acknowledged_at_order_reminder_sent_at'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='qb_invoice_id',
            new_name='square_order_id',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='qb_payment_id',
            new_name='square_payment_id',
        ),
    ]
