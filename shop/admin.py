from datetime import timedelta

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from .models import Product, Order, NukeRequest, PollinationRequest, BeeRemovalRequest, CallbackRequest


class OrderArchiveFilter(admin.SimpleListFilter):
    title = "Order age"
    parameter_name = "archive"

    def lookups(self, request, model_admin):
        return [
            ("active", "Active (last 30 days or not completed)"),
            ("archived", "Archived (completed 30+ days ago)"),
        ]

    def queryset(self, request, queryset):
        cutoff = timezone.now() - timedelta(days=30)
        archived = queryset.filter(status="completed", updated_at__lte=cutoff)
        value = self.value()
        if value == "archived":
            return archived
        if value == "active":
            return queryset.exclude(pk__in=archived.values("pk"))
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'size', 'price', 'in_stock', 'created_at']
    list_filter = ['in_stock', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'in_stock']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'first_name',
        'last_name',
        'email',
        'product',
        'quantity',
        'total_price',
        'status_badge',
        'status',
        'payment_status_badge',
        'payment_status',
        'acknowledged_badge',
        'created_at',
    ]
    list_filter = [OrderArchiveFilter, 'status', 'payment_status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'qb_invoice_id']
    list_editable = ['status']
    actions = ['acknowledge_selected_orders']
    readonly_fields = [
        'total_price',
        'created_at',
        'updated_at',
        'acknowledged_at',
        'reminder_sent_at',
        'qb_invoice_id',
        'qb_payment_id',
        'payment_url',
        'paid_at',
    ]
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
        ('Order Tracking', {
            'fields': ('acknowledged_at', 'reminder_sent_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        cutoff = timezone.now() - timedelta(days=30)
        archived = queryset.filter(status="completed", updated_at__lte=cutoff)
        if request.GET.get("archive") == "archived":
            return archived
        return queryset.exclude(pk__in=archived.values("pk"))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:order_id>/acknowledge/",
                self.admin_site.admin_view(self.acknowledge_order),
                name="shop_order_acknowledge",
            ),
        ]
        return custom_urls + urls

    def _has_action_taken(self, order):
        return order.status != "pending" or order.payment_status != "unpaid"

    @admin.action(description="Acknowledge selected orders")
    def acknowledge_selected_orders(self, request, queryset):
        now = timezone.now()
        acknowledged = 0
        skipped = 0
        for order in queryset:
            if not self._has_action_taken(order):
                skipped += 1
                continue
            order.acknowledged_at = now
            order.save(update_fields=["acknowledged_at", "updated_at"])
            acknowledged += 1

        if acknowledged:
            self.message_user(
                request,
                f"Acknowledged {acknowledged} order(s).",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Skipped {skipped} order(s) because no action was taken yet.",
                level=messages.WARNING,
            )

    def acknowledge_order(self, request, order_id):
        order = self.get_object(request, order_id)
        if not order:
            self.message_user(request, "Order not found.", level=messages.ERROR)
            return redirect("..")

        if not self._has_action_taken(order):
            self.message_user(
                request,
                "Please update the order status or payment status before acknowledging.",
                level=messages.WARNING,
            )
            return redirect("..")

        order.acknowledged_at = timezone.now()
        order.save(update_fields=["acknowledged_at", "updated_at"])
        self.message_user(request, "Order acknowledged.", level=messages.SUCCESS)
        return redirect("..")

    def status_badge(self, obj):
        colors = {
            "pending": "#fff3cd",
            "awaiting_payment": "#d1ecf1",
            "processing": "#dfe6ff",
            "paid": "#d4edda",
            "completed": "#d4edda",
            "cancelled": "#f8d7da",
            "refunded": "#f8d7da",
        }
        color = colors.get(obj.status, "#e2e3e5")
        return format_html(
            '<span style="background:{}; padding:2px 8px; border-radius:12px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Order Status"

    def payment_status_badge(self, obj):
        colors = {
            "unpaid": "#fff3cd",
            "pending": "#d1ecf1",
            "completed": "#d4edda",
            "failed": "#f8d7da",
            "refunded": "#f8d7da",
        }
        color = colors.get(obj.payment_status, "#e2e3e5")
        return format_html(
            '<span style="background:{}; padding:2px 8px; border-radius:12px;">{}</span>',
            color,
            obj.get_payment_status_display(),
        )

    payment_status_badge.short_description = "Payment"

    def acknowledged_badge(self, obj):
        if obj.acknowledged_at:
            return format_html(
                '<span style="background:#d4edda; padding:2px 8px; border-radius:12px;">Acknowledged</span>'
            )
        return format_html(
            '<span style="background:#fff3cd; padding:2px 8px; border-radius:12px;">Unacknowledged</span>'
        )

    acknowledged_badge.short_description = "Acknowledged"


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
