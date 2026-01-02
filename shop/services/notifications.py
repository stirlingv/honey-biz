"""
Notification Service

Handles SMS and email notifications for orders and service requests.
"""

import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_sms_notification(message):
    """
    Send SMS notification via email-to-SMS gateway.
    
    Uses carrier email gateways to send text messages for free.
    Verizon: number@vtext.com
    AT&T: number@txt.att.net
    T-Mobile: number@tmomail.net
    
    Args:
        message: Short message to send (SMS has 160 char limit)
    """
    sms_email = getattr(settings, 'SMS_NOTIFICATION_EMAIL', None)
    
    if not sms_email:
        logger.warning("SMS_NOTIFICATION_EMAIL not configured, skipping SMS notification")
        return False
    
    try:
        # SMS messages should be short - carriers may split long messages
        truncated_message = message[:155] + "..." if len(message) > 160 else message
        
        send_mail(
            subject='',  # SMS doesn't show subject, keep empty
            message=truncated_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[sms_email],
            fail_silently=False,
        )
        logger.info(f"SMS notification sent to {sms_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS notification: {e}")
        return False


def send_admin_email(subject, message):
    """
    Send email notification to admin.
    
    Args:
        subject: Email subject line
        message: Email body content
    """
    admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', None)
    
    if not admin_email:
        logger.warning("ADMIN_NOTIFICATION_EMAIL not configured, skipping email notification")
        return False
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        logger.info(f"Admin email sent to {admin_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send admin email: {e}")
        return False


def notify_new_order(order):
    """
    Send notifications for a new honey order.
    
    Args:
        order: Order model instance
    """
    # SMS notification (short)
    callback_flag = "📞CALLBACK " if order.prefer_callback else ""
    sms_message = f"{callback_flag}New Order! {order.first_name} {order.last_name} - {order.quantity}x {order.product.name} (${order.total_price})"
    send_sms_notification(sms_message)
    
    # Email notification (detailed)
    email_subject = f"New Honey Order #{order.id}"
    email_message = f"""
New honey order received!

Order #{order.id}
Customer: {order.first_name} {order.last_name}
Email: {order.email}
Phone: {order.phone}
📞 Prefers Callback: {'YES - Please call!' if order.prefer_callback else 'No'}

Product: {order.product.name} ({order.product.size})
Quantity: {order.quantity}
Total: ${order.total_price}

Shipping Address:
{order.address}
{order.city}, {order.state} {order.zip_code}

Notes: {order.notes or 'None'}

View in admin: /admin/shop/order/{order.id}/change/
"""
    send_admin_email(email_subject, email_message)


def notify_new_nuc_request(nuc_request):
    """
    Send notifications for a new nuc (bee starter kit) request.
    
    Args:
        nuc_request: NukeRequest model instance
    """
    callback_flag = "📞CALLBACK " if nuc_request.prefer_callback else ""
    sms_message = f"{callback_flag}New Nuc Request! {nuc_request.first_name} {nuc_request.last_name} wants {nuc_request.quantity} nucs"
    send_sms_notification(sms_message)
    
    email_subject = f"New Nuc Request #{nuc_request.id}"
    email_message = f"""
New bee nuc request received!

Request #{nuc_request.id}
Customer: {nuc_request.first_name} {nuc_request.last_name}
Email: {nuc_request.email}
Phone: {nuc_request.phone}
📞 Prefers Callback: {'YES - Please call!' if nuc_request.prefer_callback else 'No'}

Quantity: {nuc_request.quantity} nucs
Experience Level: {nuc_request.experience_level}
Preferred Pickup: {nuc_request.preferred_pickup_date or 'Not specified'}

Location:
{nuc_request.address}
{nuc_request.city}, {nuc_request.state} {nuc_request.zip_code}

Notes: {nuc_request.notes or 'None'}

View in admin: /admin/shop/nukerequest/{nuc_request.id}/change/
"""
    send_admin_email(email_subject, email_message)


def notify_new_pollination_request(pollination_request):
    """
    Send notifications for a new pollination service request.
    
    Args:
        pollination_request: PollinationRequest model instance
    """
    callback_flag = "📞CALLBACK " if pollination_request.prefer_callback else ""
    sms_message = f"{callback_flag}Pollination Request! {pollination_request.first_name} - {pollination_request.acreage} acres of {pollination_request.crop_type}"
    send_sms_notification(sms_message)
    
    email_subject = f"New Pollination Request #{pollination_request.id}"
    email_message = f"""
New pollination service request!

Request #{pollination_request.id}
Customer: {pollination_request.first_name} {pollination_request.last_name}
Email: {pollination_request.email}
Phone: {pollination_request.phone}
📞 Prefers Callback: {'YES - Please call!' if pollination_request.prefer_callback else 'No'}

Crop Type: {pollination_request.crop_type}
Acreage: {pollination_request.acreage} acres
Hives Requested: {pollination_request.num_hives_requested or 'Not specified'}
Start Date: {pollination_request.preferred_start_date}
Duration: {pollination_request.duration_weeks} weeks

Property Location:
{pollination_request.property_address}
{pollination_request.city}, {pollination_request.state} {pollination_request.zip_code}

Notes: {pollination_request.notes or 'None'}

View in admin: /admin/shop/pollinationrequest/{pollination_request.id}/change/
"""
    send_admin_email(email_subject, email_message)


def notify_new_bee_removal(removal_request):
    """
    Send notifications for a new bee removal request.
    
    Args:
        removal_request: BeeRemovalRequest model instance
    """
    urgency_emoji = {
        'low': '🟢',
        'medium': '🟡', 
        'high': '🟠',
        'emergency': '🔴'
    }
    emoji = urgency_emoji.get(removal_request.urgency, '⚪')
    
    callback_flag = "📞CALLBACK " if removal_request.prefer_callback else ""
    sms_message = f"{emoji} {callback_flag}Bee Removal! {removal_request.urgency.upper()} - {removal_request.first_name} in {removal_request.city} ({removal_request.bee_location})"
    send_sms_notification(sms_message)
    
    email_subject = f"{'🚨 URGENT: ' if removal_request.urgency in ['high', 'emergency'] else ''}Bee Removal Request #{removal_request.id}"
    email_message = f"""
New bee removal request!

Request #{removal_request.id}
URGENCY: {removal_request.urgency.upper()}

Customer: {removal_request.first_name} {removal_request.last_name}
Email: {removal_request.email}
Phone: {removal_request.phone}
📞 Prefers Callback: {'YES - Please call!' if removal_request.prefer_callback else 'No'}

Property Type: {removal_request.property_type}
Bee Location: {removal_request.bee_location}
How Long Present: {removal_request.how_long_present}
Estimated Size: {removal_request.estimated_size or 'Not specified'}
Height from Ground: {removal_request.height_from_ground or 'Not specified'}

Been Sprayed: {'Yes ⚠️' if removal_request.has_been_sprayed else 'No'}
Can Send Photo: {'Yes' if removal_request.can_send_photo else 'No'}

Property Location:
{removal_request.property_address}
{removal_request.city}, {removal_request.state} {removal_request.zip_code}

Notes: {removal_request.notes or 'None'}

View in admin: /admin/shop/beeremovalrequest/{removal_request.id}/change/
"""
    send_admin_email(email_subject, email_message)


def notify_new_callback_request(callback):
    """
    Send notifications for a new callback request.
    
    Args:
        callback: CallbackRequest model instance
    """
    interest_display = callback.get_interest_display()
    
    sms_message = f"📞 Callback Request! {callback.name} wants to discuss: {interest_display}. Call: {callback.phone}"
    send_sms_notification(sms_message)
    
    email_subject = f"📞 Callback Request #{callback.id} - {interest_display}"
    email_message = f"""
New callback request received!

Request #{callback.id}
Name: {callback.name}
Phone: {callback.phone}
Email: {callback.email or 'Not provided'}

Interested In: {interest_display}
Best Time to Call: {callback.best_time or 'Not specified'}

Message: {callback.message or 'None'}

View in admin: /admin/shop/callbackrequest/{callback.id}/change/
"""
    send_admin_email(email_subject, email_message)
