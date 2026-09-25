from django.contrib import admin

from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "role",
        "branch",
        "is_active",
    )
    list_filter = ("role", "branch", "is_active")
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )