"""
Square Payment Integration Service

Creates hosted payment links for orders. When a customer clicks "Proceed to Payment",
we create a Square Payment Link and redirect them to Square's secure checkout page.
Square deposits the funds to the bank account directly — no extra accounting setup needed.

QB Desktop workflow for mom:
  Square deposits appear in her bank account → she reconciles in QB Desktop as normal.
  For detail, Square's monthly CSV can be imported via QB Desktop's bank feed import.
"""

import hashlib
import hmac
import base64
import logging
import uuid

from django.conf import settings

logger = logging.getLogger(__name__)


def _get_client():
    from square.client import Client
    return Client(
        access_token=settings.SQUARE_ACCESS_TOKEN,
        environment=settings.SQUARE_ENVIRONMENT,
    )


def create_payment_link(order, redirect_url: str) -> dict:
    """
    Create a Square Payment Link for an order.

    Args:
        order: Order model instance
        redirect_url: URL Square redirects the customer to after payment

    Returns:
        dict with 'url' (Square checkout URL) and 'square_order_id'

    Raises:
        Exception if the Square API call fails
    """
    client = _get_client()

    body = {
        'idempotency_key': str(uuid.uuid4()),
        'order': {
            'location_id': settings.SQUARE_LOCATION_ID,
            'reference_id': str(order.id),  # used to match webhook back to our order
            'line_items': [
                {
                    'name': f'{order.product.name} ({order.product.size})',
                    'quantity': str(order.quantity),
                    'base_price_money': {
                        'amount': int(order.product.price * 100),  # Square uses cents
                        'currency': 'USD',
                    },
                }
            ],
        },
        'checkout_options': {
            'redirect_url': redirect_url,
            'ask_for_shipping_address': False,
        },
        'pre_populated_data': {
            'buyer_email': order.email,
        },
    }

    result = client.checkout.create_payment_link(body)

    if result.is_success():
        link = result.body['payment_link']
        logger.info(f'Created Square payment link for order {order.id}: {link["id"]}')
        return {
            'url': link['url'],
            'square_order_id': link['order_id'],
        }
    else:
        errors = result.errors
        logger.error(f'Square API error creating payment link for order {order.id}: {errors}')
        raise Exception(f'Square payment link creation failed: {errors}')


def verify_webhook_signature(body: bytes, signature: str, url: str) -> bool:
    """
    Verify a Square webhook event signature.

    Square signs each webhook using HMAC-SHA256 over (url + body) with the
    webhook signature key from the Square Developer Dashboard.

    Args:
        body: Raw request body bytes
        signature: Value of the x-square-hmacsha256-signature header
        url: Full URL of the webhook endpoint (must match exactly)

    Returns:
        True if signature is valid, False otherwise
    """
    key = settings.SQUARE_WEBHOOK_SIGNATURE_KEY
    if not key:
        logger.warning('SQUARE_WEBHOOK_SIGNATURE_KEY not set — skipping signature verification')
        return False

    payload = url + body.decode('utf-8')
    expected = base64.b64encode(
        hmac.new(
            key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256,
        ).digest()
    ).decode('utf-8')

    return hmac.compare_digest(expected, signature)
