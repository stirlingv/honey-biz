from django.urls import path
from . import views

urlpatterns = [
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('products/', views.products, name='products'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('order/', views.order_honey, name='order_honey'),
    path('order/success/', views.order_success, name='order_success'),
    path('nucs/', views.nuke_request, name='nuke_request'),
    path('nucs/success/', views.nuke_success, name='nuke_success'),
    
    # Services
    path('services/pollination/', views.pollination_services, name='pollination_services'),
    path('services/pollination/success/', views.pollination_success, name='pollination_success'),
    path('services/bee-removal/', views.bee_removal, name='bee_removal'),
    path('services/bee-removal/success/', views.bee_removal_success, name='bee_removal_success'),
    
    # Callback request
    path('callback/', views.callback_request, name='callback_request'),
    path('callback/success/', views.callback_success, name='callback_success'),
    
    # Checkout flow
    path('checkout/<int:order_id>/review/', views.checkout_review, name='checkout_review'),
    path('checkout/<int:order_id>/process/', views.checkout_process, name='checkout_process'),
    path('order/<int:order_id>/status/', views.order_status, name='order_status'),
    
    # QuickBooks OAuth (admin only)
    path('quickbooks/connect/', views.quickbooks_connect, name='quickbooks_connect'),
    path('quickbooks/callback/', views.quickbooks_callback, name='quickbooks_callback'),
    path('quickbooks/disconnect/', views.quickbooks_disconnect, name='quickbooks_disconnect'),
    
    # Legal pages
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
]
