from datetime import timedelta
from urllib.parse import quote

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
        'phone',
        'prefer_callback_badge',
        'product',
        'quantity',
        'total_price',
        'invoice_sent_badge',
        'status_badge',
        'status',
        'created_at',
    ]
    list_filter = [OrderArchiveFilter, 'status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    list_editable = ['status']
    actions = ['acknowledge_selected_orders', 'mark_invoice_sent']
    readonly_fields = [
        'invoice_details',
        'email_customer_link',
        'invoice_sent_at',
        'total_price',
        'created_at',
        'updated_at',
        'acknowledged_at',
        'reminder_sent_at',
    ]
    fieldsets = (
        ('Invoice Info', {
            'fields': ('invoice_details', 'email_customer_link', 'invoice_sent_at'),
            'description': 'Copy these details into QuickBooks to create the invoice, then click "Mark Invoice Sent" in the action menu.',
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'prefer_callback', 'address', 'city', 'state', 'zip_code')
        }),
        ('Order Details', {
            'fields': ('product', 'quantity', 'total_price', 'status', 'notes')
        }),
        ('Order Tracking', {
            'fields': ('acknowledged_at', 'reminder_sent_at'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
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

    # -------------------------------------------------------------------------
    # Invoice helpers
    # -------------------------------------------------------------------------

    def invoice_details(self, obj):
        lines = [
            f"CUSTOMER: {obj.first_name} {obj.last_name}",
            f"Email:    {obj.email}",
            f"Phone:    {obj.phone}",
            f"Address:  {obj.full_address}",
            "",
            f"ITEM:     {obj.product.name} ({obj.product.size})",
            f"Qty:      {obj.quantity}  ×  ${obj.product.price:.2f} each",
            f"TOTAL:    ${obj.total_price:.2f}",
            "",
            f"Order Date: {obj.created_at.strftime('%B %d, %Y')}",
            f"Order #:    {obj.id}",
        ]
        return format_html(
            '<pre style="background:#f8f9fa; padding:14px; border-radius:4px; '
            'font-family:monospace; font-size:13px; line-height:1.7; '
            'white-space:pre-wrap; border:1px solid #dee2e6; margin:0;">{}</pre>',
            "\n".join(lines),
        )

    invoice_details.short_description = "QuickBooks Invoice Details"

    def email_customer_link(self, obj):
        subject = f"Your Bear Creek Apiaries Order #{obj.id}"
        body = (
            f"Dear {obj.first_name},\n\n"
            f"Thank you for your order from Bear Creek Apiaries! "
            f"Please find your invoice attached or see the details below:\n\n"
            f"  {obj.product.name} ({obj.product.size}) "
            f"x{obj.quantity} = ${obj.total_price:.2f}\n\n"
            f"If you have any questions, feel free to reply to this email "
            f"or call us at (850) 545-0205.\n\n"
            f"Thank you,\nBear Creek Apiaries"
        )
        mailto = f"mailto:{obj.email}?subject={quote(subject)}&body={quote(body)}"
        return format_html(
            '<a href="{}" style="display:inline-block; background:#417690; color:white; '
            'padding:7px 14px; text-decoration:none; border-radius:4px; font-size:13px;">'
            '✉ Draft Email to {}</a>',
            mailto,
            obj.email,
        )

    email_customer_link.short_description = "Email Customer"

    # -------------------------------------------------------------------------
    # List display helpers
    # -------------------------------------------------------------------------

    def prefer_callback_badge(self, obj):
        if obj.prefer_callback:
            return format_html(
                '<span style="background:#fff3cd; padding:2px 8px; border-radius:12px; '
                'font-size:11px; font-weight:bold;">📞 Call</span>'
            )
        return ""

    prefer_callback_badge.short_description = "Callback"

    def invoice_sent_badge(self, obj):
        if obj.invoice_sent_at:
            return format_html(
                '<span style="background:#d4edda; padding:2px 8px; border-radius:12px; '
                'font-size:11px;">✓ Invoiced</span>'
            )
        return format_html(
            '<span style="background:#fff3cd; padding:2px 8px; border-radius:12px; '
            'font-size:11px;">Not Sent</span>'
        )

    invoice_sent_badge.short_description = "Invoice"

    def status_badge(self, obj):
        colors = {
            "pending": "#fff3cd",
            "processing": "#dfe6ff",
            "completed": "#d4edda",
            "cancelled": "#f8d7da",
        }
        color = colors.get(obj.status, "#e2e3e5")
        return format_html(
            '<span style="background:{}; padding:2px 8px; border-radius:12px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def acknowledged_badge(self, obj):
        if obj.acknowledged_at:
            return format_html(
                '<span style="background:#d4edda; padding:2px 8px; border-radius:12px;">Acknowledged</span>'
            )
        return format_html(
            '<span style="background:#fff3cd; padding:2px 8px; border-radius:12px;">Unacknowledged</span>'
        )

    acknowledged_badge.short_description = "Acknowledged"

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    @admin.action(description="Mark invoice as sent")
    def mark_invoice_sent(self, request, queryset):
        now = timezone.now()
        updated = 0
        for order in queryset:
            if not order.invoice_sent_at:
                order.invoice_sent_at = now
                order.save(update_fields=["invoice_sent_at", "updated_at"])
                updated += 1
        if updated:
            self.message_user(request, f"Marked {updated} order(s) as invoiced.", level=messages.SUCCESS)
        else:
            self.message_user(request, "All selected orders were already marked as invoiced.", level=messages.WARNING)

    @admin.action(description="Acknowledge selected orders")
    def acknowledge_selected_orders(self, request, queryset):
        now = timezone.now()
        acknowledged = 0
        skipped = 0
        for order in queryset:
            if order.status == "pending":
                skipped += 1
                continue
            order.acknowledged_at = now
            order.save(update_fields=["acknowledged_at", "updated_at"])
            acknowledged += 1

        if acknowledged:
            self.message_user(request, f"Acknowledged {acknowledged} order(s).", level=messages.SUCCESS)
        if skipped:
            self.message_user(
                request,
                f"Skipped {skipped} order(s) still in pending status.",
                level=messages.WARNING,
            )

    def acknowledge_order(self, request, order_id):
        order = self.get_object(request, order_id)
        if not order:
            self.message_user(request, "Order not found.", level=messages.ERROR)
            return redirect("..")

        if order.status == "pending":
            self.message_user(
                request,
                "Please update the order status before acknowledging.",
                level=messages.WARNING,
            )
            return redirect("..")

        order.acknowledged_at = timezone.now()
        order.save(update_fields=["acknowledged_at", "updated_at"])
        self.message_user(request, "Order acknowledged.", level=messages.SUCCESS)
        return redirect("..")


@admin.register(NukeRequest)
class NukeRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone', 'quantity', 'experience_level', 'status', 'created_at']
    list_filter = ['status', 'experience_level', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'prefer_callback', 'address', 'city', 'state', 'zip_code')
        }),
        ('Request Details', {
            'fields': ('quantity', 'experience_level', 'preferred_pickup_date', 'notes')
        }),
        ('Status', {
            'fields': ('status', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(PollinationRequest)
class PollinationRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone', 'crop_type', 'acreage', 'preferred_start_date', 'status', 'created_at']
    list_filter = ['status', 'crop_type', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'city']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'prefer_callback')
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
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(BeeRemovalRequest)
class BeeRemovalRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone', 'city', 'bee_location', 'urgency', 'status', 'created_at']
    list_filter = ['status', 'urgency', 'bee_location', 'property_type', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'city', 'property_address']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'prefer_callback')
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
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(CallbackRequest)
class CallbackRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'email', 'interest', 'best_time', 'status', 'created_at']
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
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
