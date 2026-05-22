from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_order_invoice_sent_at'),
    ]

    operations = [
        migrations.RemoveField(model_name='order', name='payment_status'),
        migrations.RemoveField(model_name='order', name='square_order_id'),
        migrations.RemoveField(model_name='order', name='square_payment_id'),
        migrations.RemoveField(model_name='order', name='payment_url'),
        migrations.RemoveField(model_name='order', name='paid_at'),
    ]
