"""
Notification Service

Sends Slack messages when orders and service requests come in.
Admin email is kept as an optional silent fallback.
"""

import logging

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_slack(message):
    """
    Post a message to the configured Slack incoming webhook.
    Requires SLACK_WEBHOOK_URL in settings.
    """
    webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not configured — skipping Slack notification")
        return False

    try:
        response = requests.post(webhook_url, json={"text": message}, timeout=5)
        response.raise_for_status()
        logger.info("Slack notification sent")
        return True
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False


def post_message(text, link_to=None):
    """
    Post a notification to Slack.

    When a bot token + channel are configured, uses ``chat.postMessage`` so we
    capture the message ``ts`` and link it to ``link_to`` — this is what makes
    reaction-driven status updates possible. Without a bot token it falls back
    to the outbound-only incoming webhook (no reaction tracking).

    Returns the message ``ts`` on the bot path, otherwise the webhook bool.
    """
    token = getattr(settings, 'SLACK_BOT_TOKEN', '')
    channel = getattr(settings, 'SLACK_CHANNEL', '')
    if not (token and channel):
        return send_slack(text)

    try:
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "text": text},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Failed to post Slack message: {e}")
        return None

    if not data.get("ok"):
        logger.error("Slack chat.postMessage error: %s", data.get("error"))
        return None

    if link_to is not None:
        try:
            from shop.models import SlackMessage
            SlackMessage.record(
                channel=data.get("channel", channel), ts=data["ts"], obj=link_to,
                text=text,
            )
        except Exception:
            logger.exception("Failed to record Slack message mapping")
    return data.get("ts")


def update_message(channel, ts, text):
    """Edit a previously-posted notification (chat.update). Used to stamp the
    authoritative status onto the message when it changes outside Slack. No-op
    without a bot token."""
    token = getattr(settings, 'SLACK_BOT_TOKEN', '')
    if not (token and channel and ts):
        return False
    try:
        response = requests.post(
            "https://slack.com/api/chat.update",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "ts": ts, "text": text},
            timeout=5,
        )
        response.raise_for_status()
        return response.json().get("ok", False)
    except Exception as e:
        logger.error(f"Failed to update Slack message: {e}")
        return False


def add_reaction(channel, ts, name):
    """Add the bot's own reaction to a message (status cue). No-op without a
    bot token; treats already_reacted as success."""
    return _reaction_op("reactions.add", channel, ts, name, ok_errors={"already_reacted"})


def remove_reaction(channel, ts, name):
    """Remove the bot's own reaction from a message. No-op without a bot token;
    treats no_reaction as success (nothing to remove)."""
    return _reaction_op("reactions.remove", channel, ts, name, ok_errors={"no_reaction"})


def _reaction_op(method, channel, ts, name, ok_errors=frozenset()):
    token = getattr(settings, 'SLACK_BOT_TOKEN', '')
    if not (token and channel and ts and name):
        return False
    try:
        response = requests.post(
            f"https://slack.com/api/{method}",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "timestamp": ts, "name": name},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Failed Slack {method}: {e}")
        return False
    if data.get("ok") or data.get("error") in ok_errors:
        return True
    logger.error("Slack %s error: %s", method, data.get("error"))
    return False


def get_message_reactions(channel, ts):
    """Return the list of reaction names currently on a message via
    ``reactions.get``. Reading live state (rather than tracking add/remove
    deltas) keeps status resolution self-healing if an event is missed or
    retried out of order. Empty list if unconfigured or on error."""
    token = getattr(settings, 'SLACK_BOT_TOKEN', '')
    if not (token and channel and ts):
        return []
    try:
        response = requests.get(
            "https://slack.com/api/reactions.get",
            headers={"Authorization": f"Bearer {token}"},
            params={"channel": channel, "timestamp": ts},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Failed to fetch Slack reactions: {e}")
        return []
    if not data.get("ok"):
        logger.error("Slack reactions.get error: %s", data.get("error"))
        return []
    message = data.get("message") or {}
    return [r.get("name") for r in message.get("reactions", []) if r.get("name")]


def post_thread_reply(channel, thread_ts, text):
    """Reply in-thread to a posted notification (visible confirmation of a
    reaction-driven status change). No-op without a bot token."""
    token = getattr(settings, 'SLACK_BOT_TOKEN', '')
    if not (token and channel):
        return False
    try:
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "thread_ts": thread_ts, "text": text},
            timeout=5,
        )
        response.raise_for_status()
        return response.json().get("ok", False)
    except Exception as e:
        logger.error(f"Failed to post Slack thread reply: {e}")
        return False


def send_admin_email(subject, message):
    """
    Send email notification to admin. Silent fallback — won't raise if unconfigured.
    """
    admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', None)
    if not admin_email:
        return False
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send admin email: {e}")
        return False


# =============================================================================
# Per-event notification functions
# =============================================================================

def notify_new_order(order):
    callback_flag = "📞 *CALL BACK REQUESTED*\n" if order.prefer_callback else ""
    post_message(
        f"🍯 *New Honey Order #{order.id}*\n"
        f"{callback_flag}"
        f"*Customer:* {order.first_name} {order.last_name}\n"
        f"*Phone:* {order.phone}   *Email:* {order.email}\n"
        f"*Product:* {order.product.name} ({order.product.size}) × {order.quantity} = *${order.total_price}*\n"
        f"*Ship to:* {order.full_address}\n"
        f"➡️ Send QuickBooks invoice to {order.email}",
        link_to=order,
    )
    send_admin_email(f"New Honey Order #{order.id}", _order_email_body(order))


def notify_order_reminder(order):
    post_message(
        f"⏰ *Reminder — Order #{order.id} still pending*\n"
        f"{order.first_name} {order.last_name} — "
        f"{order.quantity}× {order.product.name} (${order.total_price})\n"
        f"Invoice not yet marked as sent.",
        link_to=order,
    )


def notify_new_nuc_request(nuc_request):
    callback_flag = "📞 *CALL BACK REQUESTED*\n" if nuc_request.prefer_callback else ""
    post_message(
        f"🐝 *New Nuc Request #{nuc_request.id}*\n"
        f"{callback_flag}"
        f"*Customer:* {nuc_request.first_name} {nuc_request.last_name}\n"
        f"*Phone:* {nuc_request.phone}   *Email:* {nuc_request.email}\n"
        f"*Nucs:* {nuc_request.quantity}   *Experience:* {nuc_request.experience_level}\n"
        f"*Preferred pickup:* {nuc_request.preferred_pickup_date or 'Not specified'}\n"
        f"*Location:* {nuc_request.city}, {nuc_request.state}",
        link_to=nuc_request,
    )
    send_admin_email(
        f"New Nuc Request #{nuc_request.id}",
        f"Customer: {nuc_request.first_name} {nuc_request.last_name}\n"
        f"Email: {nuc_request.email}  Phone: {nuc_request.phone}\n"
        f"Nucs: {nuc_request.quantity}, Experience: {nuc_request.experience_level}\n"
        f"Pickup: {nuc_request.preferred_pickup_date or 'Not specified'}\n"
        f"Notes: {nuc_request.notes or 'None'}"
    )


def notify_new_pollination_request(pollination_request):
    callback_flag = "📞 *CALL BACK REQUESTED*\n" if pollination_request.prefer_callback else ""
    post_message(
        f"🌸 *New Pollination Request #{pollination_request.id}*\n"
        f"{callback_flag}"
        f"*Customer:* {pollination_request.first_name} {pollination_request.last_name}\n"
        f"*Phone:* {pollination_request.phone}   *Email:* {pollination_request.email}\n"
        f"*Crop:* {pollination_request.crop_type}   *Acreage:* {pollination_request.acreage} acres\n"
        f"*Start:* {pollination_request.preferred_start_date}   *Duration:* {pollination_request.duration_weeks} weeks\n"
        f"*Location:* {pollination_request.city}, {pollination_request.state}",
        link_to=pollination_request,
    )
    send_admin_email(
        f"New Pollination Request #{pollination_request.id}",
        f"Customer: {pollination_request.first_name} {pollination_request.last_name}\n"
        f"Email: {pollination_request.email}  Phone: {pollination_request.phone}\n"
        f"Crop: {pollination_request.crop_type}, Acreage: {pollination_request.acreage}\n"
        f"Start: {pollination_request.preferred_start_date}, Duration: {pollination_request.duration_weeks} weeks\n"
        f"Notes: {pollination_request.notes or 'None'}"
    )


def notify_new_bee_removal(removal_request):
    urgency_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'emergency': '🔴'}
    emoji = urgency_emoji.get(removal_request.urgency, '⚪')
    callback_flag = "📞 *CALL BACK REQUESTED*\n" if removal_request.prefer_callback else ""
    post_message(
        f"{emoji} *Bee Removal Request #{removal_request.id} — {removal_request.urgency.upper()}*\n"
        f"{callback_flag}"
        f"*Customer:* {removal_request.first_name} {removal_request.last_name}\n"
        f"*Phone:* {removal_request.phone}   *Email:* {removal_request.email}\n"
        f"*Bee location:* {removal_request.bee_location} in {removal_request.city}, {removal_request.state}\n"
        f"*How long:* {removal_request.how_long_present}\n"
        f"*Sprayed:* {'Yes ⚠️' if removal_request.has_been_sprayed else 'No'}",
        link_to=removal_request,
    )
    send_admin_email(
        f"{'🚨 URGENT: ' if removal_request.urgency in ['high', 'emergency'] else ''}Bee Removal #{removal_request.id}",
        f"URGENCY: {removal_request.urgency.upper()}\n"
        f"Customer: {removal_request.first_name} {removal_request.last_name}\n"
        f"Email: {removal_request.email}  Phone: {removal_request.phone}\n"
        f"Location: {removal_request.bee_location} — {removal_request.city}, {removal_request.state}\n"
        f"Sprayed: {'Yes' if removal_request.has_been_sprayed else 'No'}\n"
        f"Notes: {removal_request.notes or 'None'}"
    )


def notify_new_callback_request(callback):
    post_message(
        f"📞 *Callback Request #{callback.id}*\n"
        f"*Name:* {callback.name}   *Phone:* {callback.phone}\n"
        f"*About:* {callback.get_interest_display()}\n"
        f"*Best time:* {callback.best_time or 'Not specified'}\n"
        f"*Message:* {callback.message or 'None'}",
        link_to=callback,
    )
    send_admin_email(
        f"Callback Request #{callback.id} — {callback.get_interest_display()}",
        f"Name: {callback.name}\nPhone: {callback.phone}\nEmail: {callback.email or 'Not provided'}\n"
        f"About: {callback.get_interest_display()}\nBest time: {callback.best_time or 'Not specified'}\n"
        f"Message: {callback.message or 'None'}"
    )


# =============================================================================
# Internal helpers
# =============================================================================

def _order_email_body(order):
    return (
        f"New honey order received!\n\n"
        f"Order #{order.id}\n"
        f"Customer: {order.first_name} {order.last_name}\n"
        f"Email: {order.email}\nPhone: {order.phone}\n"
        f"Prefers Callback: {'YES' if order.prefer_callback else 'No'}\n\n"
        f"Product: {order.product.name} ({order.product.size})\n"
        f"Quantity: {order.quantity}\nTotal: ${order.total_price}\n\n"
        f"Ship to:\n{order.full_address}\n\n"
        f"Notes: {order.notes or 'None'}"
    )
