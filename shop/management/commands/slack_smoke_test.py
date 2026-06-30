"""Live end-to-end smoke test for two-way Slack status sync.

Posts a throwaway order notification to the *real* Slack channel, drives the
order through its status flow, and reads the message's reactions back from Slack
to confirm the bot's status cue actually moves. This is the one check that
mocked unit tests can't give you: that the configured token, scopes, channel
membership, and event wiring all work against the live workspace.

Run it once after deploy, with SLACK_BOT_TOKEN + SLACK_CHANNEL configured:

    python manage.py slack_smoke_test

Database rows it creates are always cleaned up. The Slack message is left for
you to eyeball (re-run with --delete-slack to remove it, best-effort).
"""

import time
from decimal import Decimal

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from shop.models import Order, Product, SlackMessage
from shop.services import notifications


class Command(BaseCommand):
    help = (
        "Live end-to-end smoke test of outbound Slack status sync: posts a test "
        "order to the real channel, advances its status, and verifies the bot's "
        "status reaction moves. Cleans up the test data afterward."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes", action="store_true",
            help="Skip the confirmation prompt (for non-interactive runs).",
        )
        parser.add_argument(
            "--delete-slack", action="store_true",
            help="Best-effort delete of the test Slack message when done "
                 "(DB rows are always cleaned up regardless).",
        )
        parser.add_argument(
            "--pause", type=float, default=2.0,
            help="Seconds to wait after each change before reading reactions "
                 "back (Slack is eventually consistent). Default: 2.",
        )

    def handle(self, *args, **options):
        token = getattr(settings, "SLACK_BOT_TOKEN", "")
        channel = getattr(settings, "SLACK_CHANNEL", "")
        if not (token and channel):
            raise CommandError(
                "SLACK_BOT_TOKEN and SLACK_CHANNEL must be set — this test posts "
                "to the live workspace."
            )
        if not getattr(settings, "SLACK_BOT_USER_ID", ""):
            self.stdout.write(self.style.WARNING(
                "Heads up: SLACK_BOT_USER_ID is unset, so the bot's own reactions "
                "won't be filtered from inbound events. Outbound sync is still tested."
            ))

        if not options["yes"]:
            self.stdout.write(self.style.WARNING(
                f"This posts a TEST order to Slack channel {channel} and drives "
                "live status updates."
            ))
            if input("Continue? [y/N] ").strip().lower() not in ("y", "yes"):
                self.stdout.write("Aborted.")
                return

        pause = options["pause"]
        checks = []
        product = order = None
        ts = msg_channel = None

        try:
            product = Product.objects.create(
                name="Smoke Test Honey",
                description="Temporary smoke-test product — safe to delete.",
                price=Decimal("1.00"), size="Pint", in_stock=False,
            )
            order = Order.objects.create(
                first_name="Slack", last_name="Smoke Test",
                email="smoke-test@bcapiaries.com", phone="(850) 555-0000",
                address="1 Test Ln", city="Tallahassee", state="FL",
                zip_code="32301", product=product, quantity=1,
            )

            # 1. Post a linked notification (records the SlackMessage mapping).
            self.stdout.write("→ Posting test order notification…")
            notifications.post_message(
                f"🧪 *Slack sync smoke test* — order #{order.id} "
                "(test data, will self-clean)",
                link_to=order,
            )
            link = SlackMessage.objects.filter(
                content_type__model="order", object_id=order.pk
            ).first()
            if not link:
                raise CommandError(
                    "No SlackMessage was recorded — chat.postMessage likely failed. "
                    "Check the bot token, the channel id, and that the bot is a "
                    "member of the channel."
                )
            ts, msg_channel = link.ts, link.channel
            self.stdout.write(self.style.SUCCESS(f"  posted (ts={ts}) and linked."))

            # 2. pending → processing: the 📦 cue should appear.
            self._advance(order, "processing")
            time.sleep(pause)
            reactions = notifications.get_message_reactions(msg_channel, ts)
            self._record(checks, "pending → processing adds the 📦 cue",
                         "package" in reactions)

            # 3. processing → completed: the cue should move to ✅.
            self._advance(order, "completed")
            time.sleep(pause)
            reactions = notifications.get_message_reactions(msg_channel, ts)
            self._record(checks, "processing → completed moves the cue to ✅",
                         "white_check_mark" in reactions and "package" not in reactions)

            # 4. completed → pending: the bot cue should be cleared.
            self._advance(order, "pending")
            time.sleep(pause)
            reactions = notifications.get_message_reactions(msg_channel, ts)
            self._record(checks, "completed → pending clears the bot cue",
                         "white_check_mark" not in reactions and "package" not in reactions)

        finally:
            if ts and options["delete_slack"]:
                self._delete_message(token, msg_channel, ts)
            elif ts:
                self.stdout.write(self.style.WARNING(
                    f"\nLeaving the test message in Slack (ts={ts}). Delete the "
                    "thread when done, or re-run with --delete-slack."
                ))
            # Never leave smoke-test rows in the business database.
            if order is not None:
                SlackMessage.objects.filter(
                    content_type__model="order", object_id=order.pk
                ).delete()
                order.delete()
            if product is not None:
                product.delete()
            self.stdout.write("Cleaned up smoke-test database rows.")

        self.stdout.write("\n" + "=" * 52)
        for label, ok in checks:
            tag = self.style.SUCCESS("PASS") if ok else self.style.ERROR("FAIL")
            self.stdout.write(f"  [{tag}] {label}")
        self.stdout.write("=" * 52)
        passed = sum(1 for _, ok in checks if ok)
        if checks and passed == len(checks):
            self.stdout.write(self.style.SUCCESS(
                f"All {passed} checks passed — outbound Slack sync is live. 🎉"
            ))
        else:
            raise CommandError(
                f"{len(checks) - passed} of {len(checks)} checks FAILED — see above."
            )

    def _advance(self, order, status):
        self.stdout.write(f"→ Setting status = {status}…")
        order.status = status
        order.save()

    def _record(self, checks, label, ok):
        checks.append((label, ok))
        tag = self.style.SUCCESS("ok") if ok else self.style.ERROR("MISMATCH")
        self.stdout.write(f"  {label}: {tag}")

    def _delete_message(self, token, channel, ts):
        try:
            requests.post(
                "https://slack.com/api/chat.delete",
                headers={"Authorization": f"Bearer {token}"},
                json={"channel": channel, "ts": ts}, timeout=5,
            )
            self.stdout.write("Deleted the test Slack message (thread replies may linger).")
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"Could not delete test Slack message: {e}"
            ))
