from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from shop.models import Order, Product


class OrderReminderCommandTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Wildflower Honey",
            description="Local raw honey",
            price="12.00",
            size="16 oz",
            in_stock=True,
        )

    def _create_order(self, **overrides):
        order = Order.objects.create(
            first_name="Jamie",
            last_name="Bee",
            email="jamie@example.com",
            phone="8505551111",
            address="123 Honey Ln",
            city="Tallahassee",
            state="FL",
            zip_code="32301",
            product=self.product,
            quantity=1,
            total_price="12.00",
            status=overrides.pop("status", "pending"),
            **overrides,
        )
        return order

    @patch("shop.management.commands.send_order_reminders.notify_order_reminder")
    def test_sends_reminder_for_stale_pending_order(self, notify_mock):
        order = self._create_order()
        cutoff = timezone.now() - timedelta(hours=25)
        Order.objects.filter(pk=order.pk).update(
            created_at=cutoff,
            updated_at=cutoff,
        )

        call_command("send_order_reminders")

        notify_mock.assert_called_once()
        order.refresh_from_db()
        self.assertIsNotNone(order.reminder_sent_at)

    @patch("shop.management.commands.send_order_reminders.notify_order_reminder")
    def test_skips_recent_order(self, notify_mock):
        order = self._create_order()
        recent_time = timezone.now() - timedelta(hours=2)
        Order.objects.filter(pk=order.pk).update(
            created_at=recent_time,
            updated_at=recent_time,
        )

        call_command("send_order_reminders")

        notify_mock.assert_not_called()
        order.refresh_from_db()
        self.assertIsNone(order.reminder_sent_at)

    @patch("shop.management.commands.send_order_reminders.notify_order_reminder")
    def test_skips_acknowledged_order_before_24_hours(self, notify_mock):
        order = self._create_order(acknowledged_at=timezone.now() - timedelta(hours=2))
        stale_time = timezone.now() - timedelta(hours=30)
        Order.objects.filter(pk=order.pk).update(
            created_at=stale_time,
            updated_at=stale_time,
        )

        call_command("send_order_reminders")

        notify_mock.assert_not_called()
        order.refresh_from_db()
        self.assertIsNone(order.reminder_sent_at)

    @patch("shop.management.commands.send_order_reminders.notify_order_reminder")
    def test_skips_already_reminded_order(self, notify_mock):
        order = self._create_order(reminder_sent_at=timezone.now())
        stale_time = timezone.now() - timedelta(hours=30)
        Order.objects.filter(pk=order.pk).update(
            created_at=stale_time,
            updated_at=stale_time,
        )

        call_command("send_order_reminders")

        notify_mock.assert_not_called()
        order.refresh_from_db()
        self.assertIsNotNone(order.reminder_sent_at)

    @patch("shop.management.commands.send_order_reminders.notify_order_reminder")
    def test_sends_second_reminder_after_acknowledged(self, notify_mock):
        order = self._create_order(acknowledged_at=timezone.now() - timedelta(hours=26))
        stale_time = timezone.now() - timedelta(hours=30)
        Order.objects.filter(pk=order.pk).update(
            created_at=stale_time,
            updated_at=stale_time,
        )

        call_command("send_order_reminders")

        notify_mock.assert_called_once()
        order.refresh_from_db()
        self.assertIsNotNone(order.reminder_sent_at)

    @patch("shop.management.commands.send_order_reminders.notify_order_reminder")
    def test_skips_acknowledged_order_with_action(self, notify_mock):
        order = self._create_order(
            acknowledged_at=timezone.now() - timedelta(hours=26),
            status="processing",
        )
        stale_time = timezone.now() - timedelta(hours=30)
        Order.objects.filter(pk=order.pk).update(
            created_at=stale_time,
            updated_at=stale_time,
        )

        call_command("send_order_reminders")

        notify_mock.assert_not_called()
        order.refresh_from_db()
        self.assertIsNone(order.reminder_sent_at)

    @patch("shop.management.commands.send_order_reminders.notify_order_reminder")
    def test_sends_post_ack_reminder_even_if_reminded_before(self, notify_mock):
        reminder_time = timezone.now() - timedelta(hours=50)
        order = self._create_order(
            acknowledged_at=timezone.now() - timedelta(hours=26),
            reminder_sent_at=reminder_time,
        )
        stale_time = timezone.now() - timedelta(hours=30)
        Order.objects.filter(pk=order.pk).update(
            created_at=stale_time,
            updated_at=stale_time,
        )

        call_command("send_order_reminders")

        notify_mock.assert_called_once()
        order.refresh_from_db()
        self.assertIsNotNone(order.reminder_sent_at)
