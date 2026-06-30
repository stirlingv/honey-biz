"""Hermetic tests for the `slack_smoke_test` management command.

The command's real job is to hit the live Slack workspace; here we mock all
Slack I/O and verify its orchestration: it posts + links a message, advances
status (driving the real post_save sync signal), checks the reactions read back,
reports pass/fail, and always cleans up its test rows.
"""

from contextlib import contextmanager
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from shop.models import Order, Product, SlackMessage

BOT_SETTINGS = {
    "SLACK_BOT_TOKEN": "xoxb-test",
    "SLACK_CHANNEL": "C1",
    "SLACK_BOT_USER_ID": "U_BOT",
}


def _fake_post(text, link_to=None):
    """Stand in for chat.postMessage: record the mapping, return a ts."""
    if link_to is not None:
        SlackMessage.record(channel="C1", ts="1.1", obj=link_to, text=text)
    return "1.1"


@contextmanager
def _mocked_slack(reaction_sequence):
    """Patch every outbound Slack call. ``reaction_sequence`` scripts what
    reactions.get returns after each status change."""
    with patch("shop.services.notifications.post_message", side_effect=_fake_post), \
         patch("shop.services.notifications.get_message_reactions",
               side_effect=list(reaction_sequence)), \
         patch("shop.services.slack_sync.update_message"), \
         patch("shop.services.slack_sync.add_reaction"), \
         patch("shop.services.slack_sync.remove_reaction"), \
         patch("shop.services.slack_sync.post_thread_reply"):
        yield


@override_settings(**BOT_SETTINGS)
class SlackSmokeTestCommandTests(TestCase):

    def _run(self, *extra):
        args = ["slack_smoke_test", "--yes", "--pause", "0", *extra]
        call_command(*args, stdout=StringIO(), stderr=StringIO())

    def test_happy_path_passes_and_cleans_up(self):
        # Cue appears (package), moves to white_check_mark, then clears.
        with _mocked_slack([["package"], ["white_check_mark"], []]):
            self._run()
        # No smoke-test rows left behind.
        self.assertEqual(Order.objects.count(), 0)
        self.assertFalse(Product.objects.filter(name="Smoke Test Honey").exists())
        self.assertEqual(SlackMessage.objects.count(), 0)

    def test_failed_check_raises_and_still_cleans_up(self):
        # Cue never appears → first check fails → command errors out.
        with _mocked_slack([[], [], []]):
            with self.assertRaises(CommandError):
                self._run()
        # Cleanup still runs in the finally block.
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(SlackMessage.objects.count(), 0)

    @override_settings(SLACK_BOT_TOKEN="", SLACK_CHANNEL="")
    def test_aborts_without_credentials(self):
        with self.assertRaises(CommandError):
            self._run()
        # Nothing was created.
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Product.objects.filter(name="Smoke Test Honey").count(), 0)
