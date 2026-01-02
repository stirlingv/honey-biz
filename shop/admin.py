from django.contrib import admin
from .models import Product, Order, NukeRequest, PollinationRequest, BeeRemovalRequest, CallbackRequest


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


@admin.register(PollinationRequest)
class PollinationRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'crop_type', 'acreage', 'preferred_start_date', 'status', 'created_at']
    list_filter = ['status', 'crop_type', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'city']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Property Information', {
            'fields': ('property_address', 'city', 'state', 'zip_code')
        }),
        ('Service Details', {
            'fields': ('crop_type', 'crop_type_other', 'acreage', 'num_hives_requested', 'preferred_start_date', 'duration_weeks', 'notes')
        }),
        ('Status & Pricing', {
            'fields': ('status', 'quoted_price', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(BeeRemovalRequest)
class BeeRemovalRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'city', 'bee_location', 'urgency', 'status', 'created_at']
    list_filter = ['status', 'urgency', 'bee_location', 'property_type', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'city', 'property_address']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Property Information', {
            'fields': ('property_address', 'city', 'state', 'zip_code', 'property_type')
        }),
        ('Bee Information', {
            'fields': ('bee_location', 'bee_location_other', 'how_long_present', 'estimated_size', 'height_from_ground', 'urgency')
        }),
        ('Additional Info', {
            'fields': ('has_been_sprayed', 'can_send_photo', 'notes')
        }),
        ('Status & Scheduling', {
            'fields': ('status', 'scheduled_date', 'quoted_price', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CallbackRequest)
class CallbackRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'interest', 'best_time', 'status', 'created_at']
    list_filter = ['status', 'interest', 'created_at']
    search_fields = ['name', 'phone', 'email', 'message']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Request Details', {
            'fields': ('interest', 'best_time', 'message')
        }),
        ('Status', {
            'fields': ('status', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
