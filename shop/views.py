import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import HttpResponse

from .forms import (
    BeeRemovalRequestForm,
    CallbackRequestForm,
    NukeRequestForm,
    OrderForm,
    PollinationRequestForm,
)
from .models import (
    BeeRemovalRequest,
    CallbackRequest,
    NukeRequest,
    Order,
    PollinationRequest,
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
    """Home page view"""
    # Lead with flagship honey ('honey' sorts after 'gift', so -category puts it first),
    # then gift jars, so the showcase stays representative as the catalog grows.
    featured_products = Product.objects.filter(in_stock=True).order_by('-category', 'name', 'size')[:4]
    return render(request, 'shop/home.html', {
        'featured_products': featured_products
    })


def about(request):
    """About page view"""
    return render(request, 'shop/about.html')


def privacy_policy(request):
    """Privacy policy page"""
    return render(request, 'shop/privacy.html')


def terms_of_service(request):
    """Terms of service page"""
    return render(request, 'shop/terms.html')


MAX_SELF_SERVE_QUANTITY = 24


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


def order_honey(request):
    """Order form for honey"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            notify_new_order(order)
            request.session['pending_order_id'] = order.id
            return redirect('checkout_review', order_id=order.id)
    else:
        initial = {}
        product_id = request.GET.get('product')
        if product_id:
            initial['product'] = product_id
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
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })


def order_success(request):
    """Generic order success confirmation page (no payment — manual follow-up)"""
    return render(request, 'shop/order_success.html')


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
# Checkout and Payment Views
# =============================================================================

def checkout_review(request, order_id):
    """Review order before submitting"""
    order = get_object_or_404(Order, pk=order_id)

    if order.status != 'pending':
        messages.info(request, 'This order has already been submitted.')
        return redirect('order_status', order_id=order.id)

    return render(request, 'shop/checkout_review.html', {'order': order})


def checkout_process(request, order_id):
    """Submit the order and confirm to customer we'll follow up with an invoice."""
    order = get_object_or_404(Order, pk=order_id)

    if order.status not in ['pending']:
        messages.info(request, 'This order has already been submitted.')
        return redirect('order_status', order_id=order.id)

    order.status = 'pending'
    order.save()
    return redirect('order_success')


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
