
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from core_settings.models import PharmacyProfile
from .models import Branch


def require_branch_management(user):
    """
    Only the owner may manage branches, and only
    while Multi-Branch Mode is enabled.
    """
    if not user.is_authenticated or not user.is_active:
        raise PermissionDenied("Access denied.")

    if not user.is_superuser:
        raise PermissionDenied(
            "Only the Owner can manage branches."
        )

    if not PharmacyProfile.get_profile().enable_multi_branch:
        raise PermissionDenied(
            "Enable Multi-Branch Mode in Pharmacy Settings first."
        )


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = [
            "name",
            "code",
            "phone",
            "address",
            "manager_name",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "code": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "address": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "manager_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
        }


@login_required
def branch_list(request):
    require_branch_management(request.user)

    branches = Branch.objects.all()

    return render(
        request,
        "branches/branch_list.html",
        {
            "branches": branches,
            "total_branches": branches.count(),
            "active_branches": branches.filter(
                is_active=True
            ).count(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def branch_create(request):
    require_branch_management(request.user)

    form = BranchForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            branch = form.save()

        messages.success(
            request,
            f"Branch '{branch.name}' created successfully."
        )
        return redirect("branches:list")

    return render(
        request,
        "branches/branch_form.html",
        {
            "form": form,
            "page_title": "Add Branch",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def branch_edit(request, pk):
    require_branch_management(request.user)

    branch = get_object_or_404(Branch, pk=pk)

    form = BranchForm(
        request.POST or None,
        instance=branch,
    )

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()

        messages.success(
            request,
            "Branch updated successfully."
        )
        return redirect("branches:list")

    return render(
        request,
        "branches/branch_form.html",
        {
            "form": form,
            "page_title": "Edit Branch",
            "branch": branch,
        },
    )


@login_required
@require_POST
def branch_toggle_status(request, pk):
    require_branch_management(request.user)

    with transaction.atomic():
        branch = get_object_or_404(
            Branch.objects.select_for_update(),
            pk=pk,
        )

        if branch.is_active:
            if Branch.objects.filter(
                is_active=True
            ).count() <= 1:
                messages.error(
                    request,
                    "The last active branch cannot be deactivated."
                )
                return redirect("branches:list")

            # Do not deactivate branches that still have
            # employees assigned or physical stock recorded.
            if branch.users.exists():
                messages.error(
                    request,
                    "Reassign employees before deactivating this branch."
                )
                return redirect("branches:list")

            if branch.inventory_batches.filter(
                quantity__gt=0
            ).exists():
                messages.error(
                    request,
                    "Clear or transfer remaining stock "
                    "before deactivating this branch."
                )
                return redirect("branches:list")

        branch.is_active = not branch.is_active
        branch.save(update_fields=["is_active", "updated_at"])

    messages.success(
        request,
        "Branch status updated successfully."
    )

    return redirect("branches:list")
