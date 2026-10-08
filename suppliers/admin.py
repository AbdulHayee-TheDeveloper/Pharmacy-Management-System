
from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        "supplier_code",
        "name",
        "company_name",
        "phone",
        "city",
        "opening_balance",
        "is_active",
    ]

    list_filter = [
        "is_active",
        "city",
        "created_at",
    ]

    search_fields = [
        "supplier_code",
        "name",
        "company_name",
        "contact_person",
        "phone",
        "email",
    ]

    readonly_fields = [
        "supplier_code",
        "created_at",
        "updated_at",
    ]

    list_per_page = 20
