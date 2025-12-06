from django.contrib import admin
from .models import Product, Order, NukeRequest


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'size', 'price', 'in_stock', 'created_at']
    list_filter = ['in_stock', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'in_stock']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'product', 'quantity', 'total_price', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'qb_invoice_id']
    list_editable = ['status']
    readonly_fields = ['total_price', 'created_at', 'updated_at', 'qb_invoice_id', 'qb_payment_id', 'payment_url', 'paid_at']
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'city', 'state', 'zip_code')
        }),
        ('Order Details', {
            'fields': ('product', 'quantity', 'total_price', 'status', 'notes')
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'qb_invoice_id', 'qb_payment_id', 'payment_url', 'paid_at'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(NukeRequest)
class NukeRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'quantity', 'experience_level', 'status', 'created_at']
    list_filter = ['status', 'experience_level', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'city', 'state', 'zip_code')
        }),
        ('Request Details', {
            'fields': ('quantity', 'experience_level', 'preferred_pickup_date', 'notes')
        }),
        ('Status', {
            'fields': ('status', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
