"""Template context processors shared across all pages."""

from django.conf import settings
from django.utils import timezone


def promo_banner(request):
    """Expose whether the seasonal promo banner should be shown.

    The banner is date-gated (see ``PROMO_BANNER_START`` / ``PROMO_BANNER_END``
    in settings) so it appears and disappears on its own — once the promotion
    ends there is nothing to tear down by hand.
    """
    start = getattr(settings, 'PROMO_BANNER_START', None)
    end = getattr(settings, 'PROMO_BANNER_END', None)
    today = timezone.localdate()
    active = end is not None and today <= end and (start is None or today >= start)
    return {'promo_active': active}
