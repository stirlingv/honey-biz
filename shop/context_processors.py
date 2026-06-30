"""Template context processors shared across all pages."""

from decimal import Decimal

from django.conf import settings
from django.utils import timezone


def promo_is_active():
    """Return True while today falls inside the configured promo window.

    The window (``PROMO_BANNER_START`` / ``PROMO_BANNER_END`` in settings) is
    date-gated so the promotion appears and disappears on its own — once it ends
    there is nothing to tear down by hand.
    """
    start = getattr(settings, 'PROMO_BANNER_START', None)
    end = getattr(settings, 'PROMO_BANNER_END', None)
    today = timezone.localdate()
    return end is not None and today <= end and (start is None or today >= start)


def promo_discount_per_jar():
    """The advertised per-jar discount, or 0 when the promo is not running."""
    if not promo_is_active():
        return Decimal('0')
    return getattr(settings, 'PROMO_DISCOUNT_PER_JAR', Decimal('0'))


def promo_banner(request):
    """Expose the promo state to every template."""
    return {
        'promo_active': promo_is_active(),
        'promo_discount': promo_discount_per_jar(),
    }
