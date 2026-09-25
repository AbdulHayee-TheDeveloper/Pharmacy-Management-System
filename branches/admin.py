from django.contrib import admin

from .models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "phone",
        "manager_name",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = (
        "name",
        "code",
        "manager_name",
    )