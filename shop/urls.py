from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('products/', views.products, name='products'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('order/', views.order_honey, name='order_honey'),
    path('order/success/', views.order_success, name='order_success'),
    path('nucs/', views.nuke_request, name='nuke_request'),
    path('nucs/success/', views.nuke_success, name='nuke_success'),
]
