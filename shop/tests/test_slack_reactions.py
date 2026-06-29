"""Tests for the two-way Slack integration.

Covers:
  * post_message — chat.postMessage on the bot path (records the ts mapping)
    and webhook fallback when no bot token is configured.
  * get_message_reactions — parsing the live reaction set.
  * resolve_status — the derive-from-set status rule (progression, most-advanced
    wins, ❌ terminal override, empty → pending).
  * the inbound /slack/events/ endpoint — signature verification, the URL
    verification handshake, and reaction-driven status changes end to end.

All network calls are mocked; nothing leaves the test run.
"""

import hashlib
import hmac
import json
import time
from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from shop.models import CallbackRequest, NukeRequest, Order, PollinationRequest, Product, SlackMessage
from shop.services import notifications, slack_events

BOT_SETTINGS = dict(
    SLACK_BOT_TOKEN="xoxb-test",
    SLACK_CHANNEL="C123",
    SLACK_SIGNING_SECRET="shhh",
    SLACK_ALLOWED_REACTORS=[],
)


def _slack_ok(ts="1700000000.000100", channel="C123"):
    return MagicMock(raise_for_status=lambda: None,
                     json=lambda: {"ok": True, "ts": ts, "channel": channel})


class PostMessageTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Wildflower Honey", description="d", price=Decimal("17.00"), size="Pint",
        )

    def _order(self):
        return Order.objects.create(
            first_name="Jane", last_name="Doe", email="jane@example.com", phone="(850) 555-1234",
            address="1 Honey Ln", city="Tallahassee", state="FL", zip_code="32301",
            product=self.product, quantity=2,
        )

    @override_settings(**BOT_SETTINGS)
    def test_bot_path_posts_and_records_mapping(self):
        order = self._order()
        with patch("shop.services.notifications.requests.post", return_value=_slack_ok()) as post:
            ts = notifications.post_message("hi", link_to=order)

        self.assertEqual(ts, "1700000000.000100")
        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://slack.com/api/chat.postMessage")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer xoxb-test")
        self.assertEqual(kwargs["json"]["channel"], "C123")

        link = SlackMessage.objects.get(ts="1700000000.000100")
        self.assertEqual(link.target, order)

    @override_settings(SLACK_BOT_TOKEN="", SLACK_CHANNEL="", SLACK_WEBHOOK_URL="https://hooks.slack.test/x")
    def test_falls_back_to_webhook_without_bot_token(self):
        order = self._order()
        with patch("shop.services.notifications.requests.post",
                   return_value=MagicMock(raise_for_status=lambda: None)) as post:
            result = notifications.post_message("hi", link_to=order)

        self.assertTrue(result)
        self.assertEqual(post.call_args.kwargs["json"], {"text": "hi"})
        self.assertFalse(SlackMessage.objects.exists())

    @override_settings(**BOT_SETTINGS)
    def test_api_error_response_returns_none_and_records_nothing(self):
        order = self._order()
        bad = MagicMock(raise_for_status=lambda: None, json=lambda: {"ok": False, "error": "channel_not_found"})
        with patch("shop.services.notifications.requests.post", return_value=bad):
            self.assertIsNone(notifications.post_message("hi", link_to=order))
        self.assertFalse(SlackMessage.objects.exists())


@override_settings(**BOT_SETTINGS)
class GetMessageReactionsTests(TestCase):
    def test_parses_reaction_names(self):
        resp = MagicMock(raise_for_status=lambda: None, json=lambda: {
            "ok": True,
            "message": {"reactions": [
                {"name": "package", "count": 1},
                {"name": "white_check_mark", "count": 2},
            ]},
        })
        with patch("shop.services.notifications.requests.get", return_value=resp) as get:
            names = notifications.get_message_reactions("C123", "1.1")
        self.assertEqual(names, ["package", "white_check_mark"])
        self.assertEqual(get.call_args.kwargs["params"], {"channel": "C123", "timestamp": "1.1"})

    def test_no_reactions_key_returns_empty(self):
        resp = MagicMock(raise_for_status=lambda: None, json=lambda: {"ok": True, "message": {}})
        with patch("shop.services.notifications.requests.get", return_value=resp):
            self.assertEqual(notifications.get_message_reactions("C123", "1.1"), [])

    def test_api_error_returns_empty(self):
        resp = MagicMock(raise_for_status=lambda: None, json=lambda: {"ok": False, "error": "message_not_found"})
        with patch("shop.services.notifications.requests.get", return_value=resp):
            self.assertEqual(notifications.get_message_reactions("C123", "1.1"), [])


class ResolveStatusTests(TestCase):
    """Unit tests for the resolution rule, independent of Slack plumbing."""

    def setUp(self):
        self.order_flow = slack_events.STATUS_FLOW[Order]
        self.poll_flow = slack_events.STATUS_FLOW[PollinationRequest]

    def test_empty_set_is_default(self):
        self.assertEqual(slack_events.resolve_status(self.order_flow, []), "pending")

    def test_single_progression_reaction(self):
        self.assertEqual(slack_events.resolve_status(self.order_flow, ["package"]), "processing")

    def test_most_advanced_wins(self):
        self.assertEqual(
            slack_events.resolve_status(self.order_flow, ["package", "white_check_mark"]),
            "completed",
        )

    def test_terminal_overrides_progression(self):
        self.assertEqual(
            slack_events.resolve_status(self.order_flow, ["package", "white_check_mark", "x"]),
            "cancelled",
        )

    def test_unknown_emoji_ignored(self):
        self.assertEqual(slack_events.resolve_status(self.order_flow, ["eyes", "package"]), "processing")

    def test_multi_stage_progression_picks_highest(self):
        # contacted < scheduled < completed
        self.assertEqual(
            slack_events.resolve_status(self.poll_flow, ["telephone_receiver", "calendar"]),
            "scheduled",
        )


@override_settings(**BOT_SETTINGS)
class SlackEventsEndpointTests(TestCase):
    def setUp(self):
        self.url = reverse("slack_events")
        self.product = Product.objects.create(
            name="Wildflower Honey", description="d", price=Decimal("17.00"), size="Pint",
        )
        self.order = Order.objects.create(
            first_name="Jane", last_name="Doe", email="jane@example.com", phone="(850) 555-1234",
            address="1 Honey Ln", city="Tallahassee", state="FL", zip_code="32301",
            product=self.product, quantity=2,
        )

    def _signed_post(self, payload, secret="shhh", timestamp=None):
        body = json.dumps(payload)
        timestamp = timestamp or str(int(time.time()))
        basestring = f"v0:{timestamp}:{body}".encode()
        digest = hmac.new(secret.encode(), basestring, hashlib.sha256).hexdigest()
        return self.client.post(
            self.url,
            data=body,
            content_type="application/json",
            HTTP_X_SLACK_REQUEST_TIMESTAMP=timestamp,
            HTTP_X_SLACK_SIGNATURE=f"v0={digest}",
        )

    def _event(self, reaction, ts, kind="reaction_added", user="U1", channel="C123"):
        return {
            "type": "event_callback",
            "event": {
                "type": kind,
                "user": user,
                "reaction": reaction,
                "item": {"type": "message", "channel": channel, "ts": ts},
            },
        }

    def _map_order(self, ts="1700000000.000100"):
        return SlackMessage.record(channel="C123", ts=ts, obj=self.order)

    @contextmanager
    def _reactions(self, names):
        """Patch the live reaction set and the confirmation reply."""
        with patch("shop.services.slack_events.get_message_reactions", return_value=names) as fetch, \
             patch("shop.services.slack_events.post_thread_reply") as reply:
            yield fetch, reply

    # --- signature / handshake -------------------------------------------------

    def test_bad_signature_rejected(self):
        resp = self._signed_post({"type": "url_verification", "challenge": "c"}, secret="wrong")
        self.assertEqual(resp.status_code, 403)

    def test_missing_signature_rejected(self):
        resp = self.client.post(self.url, data="{}", content_type="application/json")
        self.assertEqual(resp.status_code, 403)

    def test_stale_timestamp_rejected(self):
        old = str(int(time.time()) - 60 * 10)
        resp = self._signed_post({"type": "url_verification", "challenge": "c"}, timestamp=old)
        self.assertEqual(resp.status_code, 403)

    def test_url_verification_echoes_challenge(self):
        resp = self._signed_post({"type": "url_verification", "challenge": "abc123"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["challenge"], "abc123")

    # --- reaction → status (derive from set) -----------------------------------

    def test_added_reaction_advances_status_and_replies(self):
        self._map_order()
        with self._reactions(["package"]) as (_fetch, reply):
            resp = self._signed_post(self._event("package", "1700000000.000100"))
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "processing")
        reply.assert_called_once()

    def test_most_advanced_of_multiple_emojis_wins(self):
        self._map_order()
        with self._reactions(["package", "white_check_mark"]):
            self._signed_post(self._event("white_check_mark", "1700000000.000100"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "completed")

    def test_cancel_emoji_overrides_progress(self):
        self._map_order()
        with self._reactions(["package", "white_check_mark", "x"]):
            self._signed_post(self._event("x", "1700000000.000100"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")

    def test_removing_top_reaction_steps_back(self):
        self.order.status = "completed"
        self.order.save()
        self._map_order()
        # ✅ removed; 📦 remains → back to processing.
        with self._reactions(["package"]) as (_fetch, reply):
            self._signed_post(self._event("white_check_mark", "1700000000.000100", kind="reaction_removed"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "processing")
        reply.assert_called_once()

    def test_removing_last_reaction_reverts_to_pending(self):
        self.order.status = "processing"
        self.order.save()
        self._map_order()
        with self._reactions([]):
            self._signed_post(self._event("package", "1700000000.000100", kind="reaction_removed"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_lower_emoji_on_advanced_message_is_noop(self):
        self.order.status = "completed"
        self.order.save()
        self._map_order()
        with self._reactions(["white_check_mark", "telephone_receiver"]) as (_fetch, reply):
            self._signed_post(self._event("telephone_receiver", "1700000000.000100"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "completed")
        reply.assert_not_called()  # no change → no confirmation

    def test_unknown_emoji_skips_api_call(self):
        self._map_order()
        with self._reactions(["package"]) as (fetch, reply):
            resp = self._signed_post(self._event("eyes", "1700000000.000100"))
        self.assertEqual(resp.status_code, 200)
        fetch.assert_not_called()  # not in vocabulary → no round-trip
        reply.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_unknown_ts_is_a_safe_noop(self):
        with self._reactions(["package"]) as (fetch, reply):
            resp = self._signed_post(self._event("package", "9999.0001"))
        self.assertEqual(resp.status_code, 200)
        fetch.assert_not_called()
        reply.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    @override_settings(SLACK_ALLOWED_REACTORS=["U_ADMIN"])
    def test_reaction_from_unlisted_user_is_ignored(self):
        self._map_order()
        with self._reactions(["package"]):
            self._signed_post(self._event("package", "1700000000.000100", user="U_STRANGER"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_idempotent_replay(self):
        self._map_order()
        with self._reactions(["white_check_mark"]):
            for _ in range(2):
                self._signed_post(self._event("white_check_mark", "1700000000.000100"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "completed")

    # --- per-model vocabularies ------------------------------------------------

    def test_nuc_decline(self):
        nuc = NukeRequest.objects.create(
            first_name="Sam", last_name="Bee", email="s@b.com", phone="(850) 555-0000",
            address="2 Hive Rd", city="Quincy", state="FL", zip_code="32351", quantity=1,
        )
        SlackMessage.record(channel="C123", ts="200.0001", obj=nuc)
        with self._reactions(["x"]):
            self._signed_post(self._event("x", "200.0001"))
        nuc.refresh_from_db()
        self.assertEqual(nuc.status, "declined")

    def test_callback_contacted(self):
        callback = CallbackRequest.objects.create(name="Pat", phone="(850) 555-2222")
        SlackMessage.record(channel="C123", ts="300.0001", obj=callback)
        with self._reactions(["telephone_receiver"]):
            self._signed_post(self._event("telephone_receiver", "300.0001"))
        callback.refresh_from_db()
        self.assertEqual(callback.status, "contacted")
