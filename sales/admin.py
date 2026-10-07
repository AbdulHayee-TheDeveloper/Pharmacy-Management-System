from django.contrib import admin

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    can_delete = False

    fields = (
        "medicine",
        "inventory_batch",
        "medicine_name",
        "batch_number",
        "quantity",
        "unit_price",
        "discount_amount",
        "tax_amount",
        "line_total",
    )

    readonly_fields = fields


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "branch",
        "cashier",
        "customer_name",
        "total_amount",
        "paid_amount",
        "payment_method",
        "payment_status",
        "status",
        "created_at",
    )

    list_filter = (
        "branch",
        "status",
        "payment_status",
        "payment_method",
        "created_at",
    )

    search_fields = (
        "invoice_number",
        "customer_name",
        "customer_phone",
        "cashier__username",
        "cashier__first_name",
        "cashier__last_name",
    )

    readonly_fields = (
        "invoice_number",
        "created_at",
        "updated_at",
        "completed_at",
    )

    list_select_related = (
        "branch",
        "cashier",
    )

    date_hierarchy = "created_at"

    ordering = (
        "-created_at",
    )

    inlines = [
        SaleItemInline,
    ]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = (
        "sale",
        "medicine_name",
        "batch_number",
        "quantity",
        "unit_price",
        "line_total",
    )

    search_fields = (
        "sale__invoice_number",
        "medicine_name",
        "batch_number",
        "medicine__name",
    )

    list_select_related = (
        "sale",
        "medicine",
        "inventory_batch",
    )

    readonly_fields = (
        "created_at",
    )