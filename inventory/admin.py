from django.contrib import admin

from .models import InventoryBatch

@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = (
    "medicine",
    "branch",
    "batch_number",
    "expiry_date",
    "quantity",
    "purchase_price",
    "selling_price",
    "is_active",
    )

    
    list_filter = (
        "branch",
        "is_active",
        "expiry_date",
    )

    search_fields = (
        "medicine__name",
        "medicine__generic_name",
        "batch_number",
        "medicine__barcode",
        "medicine__sku",
    )

    autocomplete_fields = (
        "medicine",
        "branch",
    )

    list_select_related = (
        "medicine",
        "branch",
    )

    ordering = (
        "expiry_date",
        "batch_number",
    )
