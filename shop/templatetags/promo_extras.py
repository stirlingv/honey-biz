"""Template filters supporting the seasonal promo display."""

from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def sale_price(price, discount):
    """Return ``price`` reduced by ``discount``, floored at zero.

    Display-only: used to show the advertised promo price next to the struck-out
    list price. Returns the original price unchanged if the inputs aren't numbers.
    """
    try:
        result = Decimal(price) - Decimal(discount)
    except (InvalidOperation, TypeError, ValueError):
        return price
    return result if result > 0 else Decimal('0')
