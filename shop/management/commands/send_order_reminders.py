from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.utils import timezone

from shop.models import Order
from shop.services.notifications import notify_order_reminder


class Command(BaseCommand):
    help = "Send SMS reminders for orders still pending after 24 hours."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=24)
        overdue_orders = Order.objects.filter(
            status="pending",
            payment_status="unpaid",
            acknowledged_at__isnull=True,
            reminder_sent_at__isnull=True,
            created_at__lte=cutoff,
        )
        acknowledged_overdue_orders = Order.objects.filter(
            status="pending",
            payment_status="unpaid",
            acknowledged_at__isnull=False,
            acknowledged_at__lte=cutoff,
        ).filter(
            Q(reminder_sent_at__isnull=True) | Q(reminder_sent_at__lt=F("acknowledged_at"))
        )

        sent_count = 0
        for order in list(overdue_orders) + list(acknowledged_overdue_orders):
            notify_order_reminder(order)
            order.reminder_sent_at = timezone.now()
            order.save(update_fields=["reminder_sent_at"])
            sent_count += 1

        self.stdout.write(self.style.SUCCESS(f"Sent {sent_count} reminder(s)."))
