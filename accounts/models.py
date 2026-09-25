from django.contrib.auth.models import AbstractUser, Permission
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="pharmacy_roles",
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.name


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    def __str__(self):
        return self.get_full_name() or self.username

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True

        if not self.is_active:
            return False

        if self.role and self.role.is_active:
            return self.role.permissions.filter(
                content_type__app_label=perm.split(".")[0],
                codename=perm.split(".")[1],
            ).exists()

        return False

    def has_module_perms(self, app_label):
        if self.is_superuser:
            return True

        if not self.is_active or not self.role or not self.role.is_active:
            return False

        return self.role.permissions.filter(
            content_type__app_label=app_label
        ).exists()