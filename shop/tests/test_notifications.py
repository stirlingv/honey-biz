"""Tests for the Slack/email notification service.

Network calls are mocked; no real requests leave the test run.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from shop.models import Order, Product
from shop.services import notifications


class SendSlackTests(TestCase):
    @override_settings(SLACK_WEBHOOK_URL="")
    def test_no_webhook_configured_is_a_safe_noop(self):
        with patch("shop.services.notifications.requests.post") as post:
            self.assertFalse(notifications.send_slack("hi"))
            post.assert_not_called()

    @override_settings(SLACK_WEBHOOK_URL="https://hooks.slack.test/abc")
    def test_posts_message_to_webhook(self):
        with patch("shop.services.notifications.requests.post") as post:
            post.return_value = MagicMock(raise_for_status=lambda: None)
            self.assertTrue(notifications.send_slack("hello"))
            post.assert_called_once()
            _, kwargs = post.call_args
            self.assertEqual(kwargs["json"], {"text": "hello"})

    @override_settings(SLACK_WEBHOOK_URL="https://hooks.slack.test/abc")
    def test_network_error_is_swallowed(self):
        with patch("shop.services.notifications.requests.post", side_effect=Exception("boom")):
            self.assertFalse(notifications.send_slack("hello"))


class OrderNotificationTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Wildflower Honey", description="d", price=Decimal("17.00"), size="Pint",
        )

    def _order(self, **o):
        defaults = dict(
            first_name="Jane", last_name="Doe", email="jane@example.com", phone="(850) 555-1234",
            address="1 Honey Ln", city="Tallahassee", state="FL", zip_code="32301",
            product=self.product, quantity=2, total_price=Decimal("34.00"),
        )
        defaults.update(o)
        return Order.objects.create(**defaults)

    def test_order_message_includes_key_details(self):
        order = self._order()
        with patch("shop.services.notifications.send_slack") as slack:
            notifications.notify_new_order(order)
        slack.assert_called_once()
        msg = slack.call_args.args[0]
        self.assertIn(f"#{order.id}", msg)
        self.assertIn("Wildflower Honey", msg)
        self.assertNotIn("CALL BACK REQUESTED", msg)

    def test_callback_flag_appears_when_requested(self):
        order = self._order(prefer_callback=True)
        with patch("shop.services.notifications.send_slack") as slack:
            notifications.notify_new_order(order)
        self.assertIn("CALL BACK REQUESTED", slack.call_args.args[0])
