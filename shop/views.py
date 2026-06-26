import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    MAX_SELF_SERVE_QUANTITY,
    BeeRemovalRequestForm,
    CallbackRequestForm,
    NukeRequestForm,
    OrderForm,
    PollinationRequestForm,
)
from .models import (
    CallbackRequest,
    Order,
    Product,
)
from .services.notifications import (
    notify_new_bee_removal,
    notify_new_callback_request,
    notify_new_nuc_request,
    notify_new_order,
    notify_new_pollination_request,
)

logger = logging.getLogger(__name__)


def home(request):
    """Home page view.

    The home page presents three category tiles (honey, honeycomb, gift jars)
    that route to the shop, rather than listing individual products.
    """
    return render(request, 'shop/home.html')


def about(request):
    """About page view"""
    return render(request, 'shop/about.html')


def privacy_policy(request):
    """Privacy policy page"""
    return render(request, 'shop/privacy.html')


def terms_of_service(request):
    """Terms of service page"""
    return render(request, 'shop/terms.html')


def products(request):
    """Products listing page"""
    return render(request, 'shop/products.html', {
        'products': Product.objects.filter(in_stock=True, category='honey'),
        'gift_products': Product.objects.filter(in_stock=True, category='gift').order_by('name'),
        'gift_quantity_range': range(1, MAX_SELF_SERVE_QUANTITY + 1),
        'gift_max_quantity': MAX_SELF_SERVE_QUANTITY,
    })


def product_detail(request, pk):
    """Individual product detail page"""
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {
        'product': product
    })


def _lookup_product(product_id):
    """Return the in-stock Product for an id from the querystring/POST, or None."""
    if not product_id:
        return None
    try:
        return Product.objects.get(pk=product_id, in_stock=True)
    except (Product.DoesNotExist, ValueError, TypeError):
        return None


def order_honey(request):
    """Order form for honey.

    When the customer arrives from a product ("Order Now"), that product is
    shown as an order summary and submitted as a hidden field; otherwise they
    pick it from a dropdown.
    """
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Single step: the submitted form is the order. Save it, notify the
            # business (Slack -> manual QuickBooks invoice), and confirm.
            order = form.save()
            notify_new_order(order)
            request.session['completed_order_id'] = order.id
            return redirect('order_success')
        selected_product = _lookup_product(request.POST.get('product'))
    else:
        initial = {}
        selected_product = _lookup_product(request.GET.get('product'))
        if selected_product:
            initial['product'] = selected_product.pk
        qty = request.GET.get('quantity')
        if qty:
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = None
            if qty and 1 <= qty <= MAX_SELF_SERVE_QUANTITY:
                initial['quantity'] = qty
        form = OrderForm(initial=initial)

    return render(request, 'shop/order_honey.html', {
        'form': form,
        'selected_product': selected_product,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })


def order_success(request):
    """Order confirmation page showing what was just placed (no online payment)."""
    order_id = request.session.pop('completed_order_id', None)
    order = Order.objects.filter(pk=order_id).first() if order_id else None
    return render(request, 'shop/order_success.html', {'order': order})


def nuke_request(request):
    """Nuc request form"""
    if request.method == 'POST':
        form = NukeRequestForm(request.POST)
        if form.is_valid():
            nuke_req = form.save()
            notify_new_nuc_request(nuke_req)
            messages.success(
                request,
                f'Thank you for your interest! We will contact you at {nuke_req.email} to discuss your nuc purchase.'
            )
            return redirect('nuke_success')
    else:
        form = NukeRequestForm()

    return render(request, 'shop/nuke_request.html', {
        'form': form
    })


def nuke_success(request):
    """Nuc request success confirmation page"""
    return render(request, 'shop/nuke_success.html')


# =============================================================================
# Pollination Services Views
# =============================================================================

def pollination_services(request):
    """Pollination services information and request form"""
    if request.method == 'POST':
        form = PollinationRequestForm(request.POST)
        if form.is_valid():
            pollination_req = form.save()
            notify_new_pollination_request(pollination_req)
            messages.success(
                request,
                f'Thank you for your pollination inquiry! We will contact you at {pollination_req.email} to discuss your needs.'
            )
            return redirect('pollination_success')
    else:
        form = PollinationRequestForm()

    return render(request, 'shop/pollination_services.html', {
        'form': form
    })


def pollination_success(request):
    """Pollination request success confirmation page"""
    return render(request, 'shop/pollination_success.html')


# =============================================================================
# Bee Removal Services Views
# =============================================================================

def bee_removal(request):
    """Bee removal/relocation services information and request form"""
    if request.method == 'POST':
        form = BeeRemovalRequestForm(request.POST)
        if form.is_valid():
            removal_req = form.save()
            notify_new_bee_removal(removal_req)
            messages.success(
                request,
                f'Thank you for contacting us! We will reach out to {removal_req.email} as soon as possible.'
            )
            return redirect('bee_removal_success')
    else:
        form = BeeRemovalRequestForm()

    return render(request, 'shop/bee_removal.html', {
        'form': form
    })


def bee_removal_success(request):
    """Bee removal request success confirmation page"""
    return render(request, 'shop/bee_removal_success.html')


# =============================================================================
# Order status
# =============================================================================

def order_status(request, order_id):
    """View order status"""
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'shop/order_status.html', {'order': order})


# =============================================================================
# Callback Request
# =============================================================================

def callback_request(request):
    """Simple callback request form"""
    if request.method == 'POST':
        form = CallbackRequestForm(request.POST)
        if form.is_valid():
            callback = form.save()
            notify_new_callback_request(callback)
            messages.success(
                request,
                f'Thanks {callback.name}! We\'ll call you at {callback.phone} soon.'
            )
            return redirect('callback_success')
    else:
        initial = {}
        interest = request.GET.get('interest')
        valid_interests = {choice[0] for choice in CallbackRequest.INTEREST_CHOICES}
        if interest in valid_interests:
            initial['interest'] = interest
        message = request.GET.get('message')
        if message:
            initial['message'] = message
        form = CallbackRequestForm(initial=initial)

    return render(request, 'shop/callback_request.html', {'form': form})


def callback_success(request):
    """Callback request success page"""
    return render(request, 'shop/callback_success.html')


def robots_txt(request):
    """Serve robots.txt with sitemap location."""
    sitemap_url = request.build_absolute_uri(reverse('sitemap'))
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
