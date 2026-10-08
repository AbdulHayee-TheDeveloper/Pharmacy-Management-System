
from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "customer_code",
        "name",
        "phone",
        "customer_type",
        "city",
        "is_active",
        "created_at",
    )

    list_filter = (
        "customer_type",
        "is_active",
        "city",
    )

    search_fields = (
        "customer_code",
        "name",
        "phone",
        "email",
        "city",
    )

    readonly_fields = (
        "customer_code",
        "created_at",
        "updated_at",
    )

    list_per_page = 20
