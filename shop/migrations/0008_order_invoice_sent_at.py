from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_rename_qb_fields_to_square'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='invoice_sent_at',
            field=models.DateTimeField(blank=True, help_text='When the QuickBooks invoice was sent to the customer', null=True),
        ),
    ]
