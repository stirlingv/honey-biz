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

    # Order status
    path('order/<int:order_id>/status/', views.order_status, name='order_status'),

    # Slack inbound events (reaction-driven status updates)
    path('slack/events/', views.slack_events_endpoint, name='slack_events'),

    # Legal pages
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
]
