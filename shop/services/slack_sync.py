"""
Outbound status sync: Django -> Slack.

When an order/request's status changes anywhere that isn't a Slack reaction
(admin list edit, change form, an action, the status view…), reflect it back
into the Slack notification so the channel stays the single source of truth:

  * Stamp the message (chat.update) with an authoritative status line. The bot
    fully owns the message text, so this always converges — no dependence on
    being able to remove a human's reaction.
  * Move the bot's own status-cue reaction to match (best-effort visual). The
    bot can only manage its *own* reactions, so a human's lingering reaction
    may stay visible; the stamp is the truth.

Driven by a post_save signal (see ``shop.signals``). Slack-originated changes
pass ``source='slack'`` so we stamp but skip re-driving the cue the human
already created.
"""

import logging

from shop.models import SlackMessage
from shop.services.notifications import (
    add_reaction,
    post_thread_reply,
    remove_reaction,
    update_message,
)
from shop.services.slack_events import status_to_reaction

logger = logging.getLogger(__name__)


def _status_line(instance):
    name = status_to_reaction(type(instance)).get(instance.status)
    emoji = f":{name}: " if name else ""
    return f"\n\n*Status:* {emoji}{instance.get_status_display()}"


def sync_status_to_slack(instance, source=None):
    """Reflect ``instance``'s current status onto its Slack notification(s)."""
    links = list(
        SlackMessage.objects.filter(
            content_type__model=instance._meta.model_name,
            object_id=instance.pk,
        )
    )
    if not links:
        return

    status_line = _status_line(instance)
    target_reaction = status_to_reaction(type(instance)).get(instance.status)

    for link in links:
        update_message(link.channel, link.ts, f"{link.text}{status_line}")

        # Cue is only driven for out-of-band changes; a Slack reaction already
        # placed the human's emoji.
        if source != 'slack' and link.bot_reaction != target_reaction:
            if link.bot_reaction:
                remove_reaction(link.channel, link.ts, link.bot_reaction)
            if target_reaction:
                add_reaction(link.channel, link.ts, target_reaction)
            link.bot_reaction = target_reaction or ''
            link.save(update_fields=['bot_reaction'])

    # A quiet heads-up in-thread when the change came from outside Slack.
    if source != 'slack':
        primary = links[0]
        post_thread_reply(
            primary.channel,
            primary.ts,
            f"{instance} → *{instance.get_status_display()}* (updated outside Slack)",
        )
