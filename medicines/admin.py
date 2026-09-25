from django.contrib import admin

from .models import Category, Medicine


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "generic_name",
        "category",
        "manufacturer",
        "dosage_form",
        "strength",
        "prescription_required",
        "is_active",
    )

    list_filter = (
        "category",
        "dosage_form",
        "prescription_required",
        "is_active",
    )

    search_fields = (
        "name",
        "generic_name",
        "manufacturer",
        "barcode",
        "sku",
    )

    autocomplete_fields = ("category",)

    list_select_related = ("category",)