from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Order, NukeRequest
from .forms import OrderForm, NukeRequestForm


def home(request):
    """Home page view"""
    featured_products = Product.objects.filter(in_stock=True)[:3]
    return render(request, 'shop/home.html', {
        'featured_products': featured_products
    })


def about(request):
    """About page view"""
    return render(request, 'shop/about.html')


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
    """Order form for honey"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(
                request,
                f'Thank you for your order! We will contact you at {order.email} to confirm your order.'
            )
            return redirect('order_success')
    else:
        form = OrderForm()
    
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
