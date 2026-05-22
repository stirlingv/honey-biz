"""
Notification Service

Sends WhatsApp messages via Twilio when orders and service requests come in.
Admin email is kept as an optional fallback but WhatsApp is the primary channel.
"""

import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_whatsapp(message):
    """
    Send a WhatsApp message to mom via Twilio.

    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM,
    and WHATSAPP_NOTIFY_NUMBER to be set in settings.
    """
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
    to_number = getattr(settings, 'WHATSAPP_NOTIFY_NUMBER', None)

    if not all([account_sid, auth_token, from_number, to_number]):
        logger.warning("Twilio WhatsApp not configured — skipping WhatsApp notification")
        return False

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        client.messages.create(
            from_=f"whatsapp:{from_number}",
            to=f"whatsapp:{to_number}",
            body=message,
        )
        logger.info(f"WhatsApp notification sent to {to_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp notification: {e}")
        return False


def send_admin_email(subject, message):
    """
    Send email notification to admin. Optional fallback — may be unreliable
    if email credentials are not configured.
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
        logger.info(f"Admin email sent to {admin_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send admin email: {e}")
        return False


# =============================================================================
# Per-event notification functions
# =============================================================================

def notify_new_order(order):
    callback_flag = "📞 CALL BACK  " if order.prefer_callback else ""
    msg = (
        f"🍯 *New Honey Order!*\n"
        f"{callback_flag}\n"
        f"*Customer:* {order.first_name} {order.last_name}\n"
        f"*Phone:* {order.phone}\n"
        f"*Email:* {order.email}\n\n"
        f"*Product:* {order.product.name} ({order.product.size})\n"
        f"*Qty:* {order.quantity}  •  *Total:* ${order.total_price}\n\n"
        f"*Ship to:* {order.full_address}\n\n"
        f"Send QuickBooks invoice to: {order.email}"
    )
    send_whatsapp(msg)
    send_admin_email(f"New Honey Order #{order.id}", _order_email_body(order))


def notify_order_reminder(order):
    msg = (
        f"⏰ *Reminder — Order #{order.id} still pending!*\n"
        f"{order.first_name} {order.last_name} — "
        f"{order.quantity}x {order.product.name} (${order.total_price})\n"
        f"Invoice not yet marked as sent."
    )
    send_whatsapp(msg)


def notify_new_nuc_request(nuc_request):
    callback_flag = "📞 CALL BACK  " if nuc_request.prefer_callback else ""
    msg = (
        f"🐝 *New Nuc Request!*\n"
        f"{callback_flag}\n"
        f"*Customer:* {nuc_request.first_name} {nuc_request.last_name}\n"
        f"*Phone:* {nuc_request.phone}\n"
        f"*Email:* {nuc_request.email}\n\n"
        f"*Nucs:* {nuc_request.quantity}  •  *Experience:* {nuc_request.experience_level}\n"
        f"*Pickup:* {nuc_request.preferred_pickup_date or 'Not specified'}\n\n"
        f"*Location:* {nuc_request.city}, {nuc_request.state}"
    )
    send_whatsapp(msg)
    send_admin_email(
        f"New Nuc Request #{nuc_request.id}",
        f"Customer: {nuc_request.first_name} {nuc_request.last_name}\n"
        f"Email: {nuc_request.email}\nPhone: {nuc_request.phone}\n"
        f"Nucs: {nuc_request.quantity}, Experience: {nuc_request.experience_level}\n"
        f"Pickup: {nuc_request.preferred_pickup_date or 'Not specified'}\n"
        f"Notes: {nuc_request.notes or 'None'}"
    )


def notify_new_pollination_request(pollination_request):
    callback_flag = "📞 CALL BACK  " if pollination_request.prefer_callback else ""
    msg = (
        f"🌸 *New Pollination Request!*\n"
        f"{callback_flag}\n"
        f"*Customer:* {pollination_request.first_name} {pollination_request.last_name}\n"
        f"*Phone:* {pollination_request.phone}\n"
        f"*Email:* {pollination_request.email}\n\n"
        f"*Crop:* {pollination_request.crop_type}  •  *Acreage:* {pollination_request.acreage} acres\n"
        f"*Start:* {pollination_request.preferred_start_date}  •  *Duration:* {pollination_request.duration_weeks} weeks\n\n"
        f"*Location:* {pollination_request.city}, {pollination_request.state}"
    )
    send_whatsapp(msg)
    send_admin_email(
        f"New Pollination Request #{pollination_request.id}",
        f"Customer: {pollination_request.first_name} {pollination_request.last_name}\n"
        f"Email: {pollination_request.email}\nPhone: {pollination_request.phone}\n"
        f"Crop: {pollination_request.crop_type}, Acreage: {pollination_request.acreage}\n"
        f"Start: {pollination_request.preferred_start_date}, Duration: {pollination_request.duration_weeks} weeks\n"
        f"Notes: {pollination_request.notes or 'None'}"
    )


def notify_new_bee_removal(removal_request):
    urgency_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'emergency': '🔴'}
    emoji = urgency_emoji.get(removal_request.urgency, '⚪')
    callback_flag = "📞 CALL BACK  " if removal_request.prefer_callback else ""
    msg = (
        f"{emoji} *Bee Removal Request — {removal_request.urgency.upper()}*\n"
        f"{callback_flag}\n"
        f"*Customer:* {removal_request.first_name} {removal_request.last_name}\n"
        f"*Phone:* {removal_request.phone}\n"
        f"*Email:* {removal_request.email}\n\n"
        f"*Location:* {removal_request.bee_location} in {removal_request.city}, {removal_request.state}\n"
        f"*How long:* {removal_request.how_long_present}\n"
        f"*Sprayed:* {'Yes ⚠️' if removal_request.has_been_sprayed else 'No'}"
    )
    send_whatsapp(msg)
    send_admin_email(
        f"{'🚨 URGENT: ' if removal_request.urgency in ['high', 'emergency'] else ''}Bee Removal #{removal_request.id}",
        f"URGENCY: {removal_request.urgency.upper()}\n"
        f"Customer: {removal_request.first_name} {removal_request.last_name}\n"
        f"Email: {removal_request.email}\nPhone: {removal_request.phone}\n"
        f"Location: {removal_request.bee_location} — {removal_request.city}, {removal_request.state}\n"
        f"Sprayed: {'Yes' if removal_request.has_been_sprayed else 'No'}\n"
        f"Notes: {removal_request.notes or 'None'}"
    )


def notify_new_callback_request(callback):
    msg = (
        f"📞 *Callback Request!*\n"
        f"*Name:* {callback.name}\n"
        f"*Phone:* {callback.phone}\n"
        f"*About:* {callback.get_interest_display()}\n"
        f"*Best time:* {callback.best_time or 'Not specified'}\n"
        f"*Message:* {callback.message or 'None'}"
    )
    send_whatsapp(msg)
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
        f"Email: {order.email}\n"
        f"Phone: {order.phone}\n"
        f"Prefers Callback: {'YES' if order.prefer_callback else 'No'}\n\n"
        f"Product: {order.product.name} ({order.product.size})\n"
        f"Quantity: {order.quantity}\n"
        f"Total: ${order.total_price}\n\n"
        f"Ship to:\n{order.full_address}\n\n"
        f"Notes: {order.notes or 'None'}"
    )
