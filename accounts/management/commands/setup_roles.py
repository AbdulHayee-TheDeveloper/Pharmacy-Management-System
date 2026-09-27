from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission

from accounts.models import Role


class Command(BaseCommand):
    help = "Create/update default pharmacy roles and their permissions."

    ROLE_PERMISSIONS = {
        "Administrator": [
            "view_medicine",
            "add_medicine",
            "change_medicine",
            "delete_medicine",
        ],
        "Pharmacist": [
            "view_medicine",
            "add_medicine",
            "change_medicine",
        ],
        "Inventory Manager": [
            "view_medicine",
            "change_medicine",
        ],
        "Cashier": [
            "view_medicine",
        ],
    }

    def handle(self, *args, **options):
        medicine_permissions = Permission.objects.filter(
            content_type__app_label="medicines",
            codename__in={
                permission
                for permissions in self.ROLE_PERMISSIONS.values()
                for permission in permissions
            },
        )

        permissions_by_codename = {
            permission.codename: permission
            for permission in medicine_permissions
        }

        missing_permissions = {
            permission
            for permissions in self.ROLE_PERMISSIONS.values()
            for permission in permissions
            if permission not in permissions_by_codename
        }

        if missing_permissions:
            self.stdout.write(
                self.style.ERROR(
                    "Missing permissions: "
                    + ", ".join(sorted(missing_permissions))
                )
            )
            return

        for role_name, permission_codes in self.ROLE_PERMISSIONS.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    "description": f"Default {role_name} role",
                    "is_active": True,
                },
            )

            role.permissions.set(
                [
                    permissions_by_codename[codename]
                    for codename in permission_codes
                ]
            )

            action = "Created" if created else "Updated"

            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} role: {role_name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Default role permissions configured successfully."
            )
        )