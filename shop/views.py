import logging
import uuid
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import Product, Order, NukeRequest, PollinationRequest, BeeRemovalRequest, CallbackRequest
from .forms import OrderForm, NukeRequestForm, PollinationRequestForm, BeeRemovalRequestForm, CallbackRequestForm
from .services.notifications import (
    notify_new_order, 
    notify_new_nuc_request,
    notify_new_pollination_request,
    notify_new_bee_removal,
    notify_new_callback_request
)

logger = logging.getLogger(__name__)


def home(request):
    """Home page view"""
    featured_products = Product.objects.filter(in_stock=True)[:3]
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


def products(request):
    """Products listing page"""
    products = Product.objects.filter(in_stock=True)
    return render(request, 'shop/products.html', {
        'products': products
    })


def product_detail(request, pk):
    """Individual product detail page"""
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {
        'product': product
    })


def order_honey(request):
    """Order form for honey - now redirects to checkout for payment"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            # Send SMS/email notification
            notify_new_order(order)
            # Store order ID in session for checkout
            request.session['pending_order_id'] = order.id
            return redirect('checkout_review', order_id=order.id)
    else:
        # Pre-select product if passed in URL
        initial = {}
        product_id = request.GET.get('product')
        if product_id:
            initial['product'] = product_id
        form = OrderForm(initial=initial)
    
    return render(request, 'shop/order_honey.html', {
        'form': form
    })


def order_success(request):
    """Order success confirmation page"""
    return render(request, 'shop/order_success.html')


def nuke_request(request):
    """Nuc request form"""
    if request.method == 'POST':
        form = NukeRequestForm(request.POST)
        if form.is_valid():
            nuke_req = form.save()
            # Send SMS/email notification
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
            # Send SMS/email notification
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
            # Send SMS/email notification
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
    """Review order before payment"""
    order = get_object_or_404(Order, pk=order_id)
    
    # Security check - only allow access to recent pending orders
    if order.payment_status not in ['unpaid', 'pending']:
        messages.info(request, 'This order has already been processed.')
        return redirect('order_status', order_id=order.id)
    
    return render(request, 'shop/checkout_review.html', {
        'order': order,
        'quickbooks_configured': bool(settings.QUICKBOOKS_CLIENT_ID),
    })


def checkout_process(request, order_id):
    """Process the checkout - create invoice and redirect to payment"""
    order = get_object_or_404(Order, pk=order_id)
    
    if order.payment_status not in ['unpaid', 'pending']:
        messages.info(request, 'This order has already been processed.')
        return redirect('order_status', order_id=order.id)
    
    # Check if QuickBooks is configured
    if not settings.QUICKBOOKS_CLIENT_ID:
        # QuickBooks not configured - fall back to manual processing
        order.status = 'pending'
        order.save()
        messages.success(
            request,
            'Your order has been submitted! We will contact you at '
            f'{order.email} with payment instructions.'
        )
        return redirect('order_success')
    
    # Check if we have QB tokens in session (admin has connected QB)
    qb_tokens = request.session.get('qb_tokens')
    
    if not qb_tokens:
        # Need to connect QuickBooks first
        # For now, fall back to manual processing
        order.status = 'pending'
        order.save()
        messages.success(
            request,
            'Your order has been submitted! We will contact you at '
            f'{order.email} with payment instructions and an invoice.'
        )
        return redirect('order_success')
    
    # Create invoice in QuickBooks
    try:
        from .services.quickbooks import quickbooks_service
        
        result = quickbooks_service.create_invoice(
            order=order,
            access_token=qb_tokens['access_token'],
            realm_id=qb_tokens['realm_id'],
        )
        
        # Update order with QuickBooks info
        order.qb_invoice_id = result['invoice_id']
        order.status = 'awaiting_payment'
        order.payment_status = 'pending'
        order.save()
        
        # Get payment link
        payment_url = quickbooks_service.get_payment_link(
            invoice_id=result['invoice_id'],
            access_token=qb_tokens['access_token'],
            realm_id=qb_tokens['realm_id'],
        )
        
        if payment_url:
            order.payment_url = payment_url
            order.save()
            return redirect(payment_url)
        
        # No payment link available - invoice will be emailed
        messages.success(
            request,
            'Your order has been submitted! An invoice has been sent to '
            f'{order.email}. Please check your email to complete payment.'
        )
        return redirect('order_success')
        
    except Exception as e:
        logger.error(f"Error creating QuickBooks invoice: {e}")
        # Fall back to manual processing
        order.status = 'pending'
        order.save()
        messages.warning(
            request,
            'Your order has been submitted, but we encountered an issue '
            'with payment processing. We will contact you at '
            f'{order.email} with payment instructions.'
        )
        return redirect('order_success')


def order_status(request, order_id):
    """View order status and payment status"""
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'shop/order_status.html', {
        'order': order,
    })


# =============================================================================
# QuickBooks OAuth Views (Admin only)
# =============================================================================

def quickbooks_connect(request):
    """Initiate QuickBooks OAuth flow (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('home')
    
    if not settings.QUICKBOOKS_CLIENT_ID:
        messages.error(request, 'QuickBooks is not configured. Please add your API credentials.')
        return redirect('home')
    
    from .services.quickbooks import quickbooks_service
    
    # Generate state for CSRF protection
    state = str(uuid.uuid4())
    request.session['qb_oauth_state'] = state
    
    auth_url = quickbooks_service.get_authorization_url(state=state)
    return redirect(auth_url)


def quickbooks_callback(request):
    """Handle QuickBooks OAuth callback"""
    # Verify state
    state = request.GET.get('state')
    stored_state = request.session.get('qb_oauth_state')
    
    if state != stored_state:
        messages.error(request, 'Invalid OAuth state. Please try again.')
        return redirect('home')
    
    # Get authorization code and realm ID
    auth_code = request.GET.get('code')
    realm_id = request.GET.get('realmId')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f'QuickBooks authorization failed: {error}')
        return redirect('home')
    
    if not auth_code or not realm_id:
        messages.error(request, 'Missing authorization code or company ID.')
        return redirect('home')
    
    try:
        from .services.quickbooks import quickbooks_service
        
        tokens = quickbooks_service.handle_callback(auth_code, realm_id)
        
        # Store tokens in session (in production, store in database)
        request.session['qb_tokens'] = {
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'realm_id': realm_id,
        }
        
        messages.success(request, 'Successfully connected to QuickBooks!')
        return redirect('home')
        
    except Exception as e:
        logger.error(f"QuickBooks OAuth error: {e}")
        messages.error(request, 'Failed to connect to QuickBooks. Please try again.')
        return redirect('home')


def quickbooks_disconnect(request):
    """Disconnect QuickBooks (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('home')
    
    if 'qb_tokens' in request.session:
        del request.session['qb_tokens']
    
    messages.success(request, 'Disconnected from QuickBooks.')
    return redirect('home')


def callback_request(request):
    """Simple callback request form"""
    if request.method == 'POST':
        form = CallbackRequestForm(request.POST)
        if form.is_valid():
            callback = form.save()
            
            # Send notifications
            notify_new_callback_request(callback)
            
            messages.success(
                request,
                f'Thanks {callback.name}! We\'ll call you at {callback.phone} soon.'
            )
            return redirect('callback_success')
    else:
        form = CallbackRequestForm()
    
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
