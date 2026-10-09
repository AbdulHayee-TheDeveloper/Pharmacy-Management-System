from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_permission_required

from .forms import MedicineForm
from .models import Category, Medicine


@login_required
@role_permission_required("medicines.view_medicine")
def medicine_list(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()

    medicines = Medicine.objects.select_related(
        "category"
    ).all()

    if query:
        medicines = medicines.filter(
            Q(name__icontains=query)
            | Q(generic_name__icontains=query)
            | Q(manufacturer__icontains=query)
            | Q(barcode__icontains=query)
            | Q(sku__icontains=query)
        )

    if category_id:
        medicines = medicines.filter(
            category_id=category_id
        )

    if status == "active":
        medicines = medicines.filter(
            is_active=True
        )

    elif status == "inactive":
        medicines = medicines.filter(
            is_active=False
        )

    context = {
        "medicines": medicines,
        "categories": Category.objects.filter(
            is_active=True
        ),
        "query": query,
        "selected_category": category_id,
        "selected_status": status,
        "total_medicines": Medicine.objects.count(),
        "active_medicines": Medicine.objects.filter(
            is_active=True
        ).count(),
        "inactive_medicines": Medicine.objects.filter(
            is_active=False
        ).count(),
    }

    return render(
        request,
        "medicines/list.html",
        context,
    )



@login_required
@role_permission_required("medicines.view_medicine")
def medicine_detail(request, pk):
    medicine = get_object_or_404(
        Medicine.objects.select_related("category"),
        pk=pk,
    )

    today = timezone.localdate()

    # Get only active, unexpired batches with available stock.
    available_batches = medicine.inventory_batches.filter(
        is_active=True,
        quantity__gt=0,
        expiry_date__gte=today,
        branch__is_active=True,
    )

    # Super Admin / Owner can see stock from all branches.
    if not request.user.is_superuser:

        # Normal employees must have an assigned branch.
        if request.user.branch_id is None:
            messages.error(
                request,
                "No branch is assigned to your account. "
                "Please contact the administrator.",
            )
            return redirect("medicines:list")

        # Employees can only see stock from their own branch.
        available_batches = available_batches.filter(
            branch_id=request.user.branch_id
        )

    stock_summary = available_batches.aggregate(
        total_quantity=Sum("quantity")
    )

    total_quantity = stock_summary["total_quantity"] or 0

    pack_size = medicine.pack_size or 1

    full_packs = total_quantity // pack_size
    loose_units = total_quantity % pack_size

    total_batches = available_batches.count()

    total_branches = (
        available_batches
        .values("branch_id")
        .distinct()
        .count()
    )

    context = {
        "medicine": medicine,
        "total_quantity": total_quantity,
        "full_packs": full_packs,
        "loose_units": loose_units,
        "total_batches": total_batches,
        "total_branches": total_branches,
    }

    return render(
        request,
        "medicines/detail.html",
        context,
    )



@login_required
@role_permission_required("medicines.change_medicine")
def medicine_edit(request, pk):
    medicine = get_object_or_404(
        Medicine.objects.select_related(
            "category"
        ),
        pk=pk,
    )

    if request.method == "POST":
        form = MedicineForm(
            request.POST,
            request.FILES,
            instance=medicine,
        )

        if form.is_valid():
            medicine = form.save()

            messages.success(
                request,
                f"{medicine.name} updated successfully.",
            )

            return redirect(
                "medicines:detail",
                pk=medicine.pk,
            )

    else:
        form = MedicineForm(
            instance=medicine,
        )

    context = {
        "form": form,
        "medicine": medicine,
        "page_title": "Edit Medicine",
        "submit_text": "Save Changes",
        "has_inventory_batches": (
            form.has_inventory_batches
        ),
    }

    return render(
        request,
        "medicines/edit.html",
        context,
    )