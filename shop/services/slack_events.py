"""
Inbound Slack Events handling.

Turns the one-way #new-orders feed into a two-way control surface: the emoji
reactions on a notification message *as a set* determine that order/request's
status. We don't treat each add/remove as an imperative command — instead, on
any reaction event we read the message's full reaction set and resolve a single
status from it. That makes the behaviour deterministic regardless of how many
emojis are present or what order they arrived in, and makes ``reaction_removed``
trivial: recompute and the status naturally steps back to the most-advanced
emoji that remains.

Resolution rule (per model), given the reactions currently on the message:
  1. If a terminal off-ramp reaction (❌) is present → that status wins outright.
  2. Else → the most-advanced progression stage whose emoji is present.
  3. Else (no known emoji) → the default (pending).

Slack's reaction events only carry the channel + message ts, so we resolve the
target through the ``SlackMessage`` mapping written when the notification was
posted (see ``notifications.post_message``).
"""

import hashlib
import hmac
import logging
import time

from django.conf import settings

from shop.models import (
    BeeRemovalRequest,
    CallbackRequest,
    NukeRequest,
    Order,
    PollinationRequest,
    SlackMessage,
)
from shop.services.notifications import get_message_reactions, post_thread_reply

logger = logging.getLogger(__name__)

# Per model: an ordered progression of (reaction name, status) from least to
# most advanced, plus terminal off-ramp reactions that override the progression
# whenever present. Reaction names are Slack's, without the surrounding colons.
STATUS_FLOW = {
    Order: {
        'progression': [
            ('package', 'processing'),
            ('white_check_mark', 'completed'),
        ],
        'terminal': {'x': 'cancelled'},
        'default': 'pending',
    },
    NukeRequest: {
        'progression': [
            ('telephone_receiver', 'contacted'),
            ('white_check_mark', 'completed'),
        ],
        'terminal': {'x': 'declined'},
        'default': 'pending',
    },
    PollinationRequest: {
        'progression': [
            ('telephone_receiver', 'contacted'),
            ('calendar', 'scheduled'),
            ('white_check_mark', 'completed'),
        ],
        'terminal': {'x': 'declined'},
        'default': 'pending',
    },
    BeeRemovalRequest: {
        'progression': [
            ('telephone_receiver', 'contacted'),
            ('calendar', 'scheduled'),
            ('white_check_mark', 'completed'),
        ],
        'terminal': {'x': 'declined'},
        'default': 'pending',
    },
    CallbackRequest: {
        'progression': [
            ('telephone_receiver', 'contacted'),
            ('white_check_mark', 'completed'),
        ],
        'terminal': {},
        'default': 'pending',
    },
}


def known_reactions(flow):
    """The set of reaction names that mean something for this model."""
    return {name for name, _ in flow['progression']} | set(flow['terminal'])


def resolve_status(flow, present_reactions):
    """Resolve a single status from the set of reactions on a message."""
    present = set(present_reactions)
    # 1. Terminal off-ramp (❌) overrides everything while present.
    for name, status in flow['terminal'].items():
        if name in present:
            return status
    # 2. Most-advanced progression stage present (progression is ascending).
    for name, status in reversed(flow['progression']):
        if name in present:
            return status
    # 3. Nothing known reacted → back to default.
    return flow['default']


def verify_signature(request):
    """Validate Slack's v0 request signature. Returns False unless the signing
    secret is configured and the HMAC + timestamp check out."""
    secret = getattr(settings, 'SLACK_SIGNING_SECRET', '')
    if not secret:
        return False

    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')
    if not timestamp or not signature:
        return False

    # Reject stale requests (replay protection): Slack recommends a 5 min window.
    try:
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False
    except (TypeError, ValueError):
        return False

    basestring = b'v0:' + timestamp.encode() + b':' + request.body
    digest = hmac.new(secret.encode(), basestring, hashlib.sha256).hexdigest()
    expected = 'v0=' + digest
    return hmac.compare_digest(expected, signature)


def handle_event(payload):
    """Process an ``event_callback`` payload. Returns the target object when a
    reaction event was for one of our messages, else None. Never raises — the
    event endpoint must always return 200 so Slack stops retrying."""
    try:
        event = payload.get('event') or {}
        if event.get('type') not in ('reaction_added', 'reaction_removed'):
            return None

        allowed = getattr(settings, 'SLACK_ALLOWED_REACTORS', [])
        if allowed and event.get('user') not in allowed:
            logger.info("Ignoring Slack reaction from unlisted user %s", event.get('user'))
            return None

        item = event.get('item') or {}
        if item.get('type') != 'message':
            return None
        ts = item.get('ts')
        channel = item.get('channel')
        if not ts:
            return None

        # The mapping only exists for messages we posted, which inherently
        # scopes this to our own notification channel.
        link = SlackMessage.objects.filter(ts=ts).select_related('content_type').first()
        if link is None:
            return None
        target = link.target
        if target is None:
            return None
        flow = STATUS_FLOW.get(type(target))
        if not flow:
            return None

        # Skip the API round-trip for emojis outside this model's vocabulary —
        # they can't change the resolved status.
        if event.get('reaction') not in known_reactions(flow):
            return target

        channel = channel or link.channel
        present = get_message_reactions(channel, ts)
        new_status = resolve_status(flow, present)

        # Idempotent: only persist + confirm when the resolved status changed.
        if target.status != new_status:
            target.status = new_status
            target.save(update_fields=['status', 'updated_at'])
            post_thread_reply(
                channel, ts, f"{target} → *{target.get_status_display()}*"
            )
        return target
    except Exception:
        logger.exception("Failed to handle Slack event")
        return None
