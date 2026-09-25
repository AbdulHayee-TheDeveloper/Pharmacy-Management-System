from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MedicineForm
from .models import Category, Medicine


@login_required
def medicine_list(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()

    medicines = Medicine.objects.select_related("category")

    if query:
        medicines = medicines.filter(
            Q(name__icontains=query)
            | Q(generic_name__icontains=query)
            | Q(manufacturer__icontains=query)
            | Q(barcode__icontains=query)
            | Q(sku__icontains=query)
        )

    if category_id:
        medicines = medicines.filter(category_id=category_id)

    if status == "active":
        medicines = medicines.filter(is_active=True)
    elif status == "inactive":
        medicines = medicines.filter(is_active=False)

    context = {
        "medicines": medicines,
        "categories": Category.objects.filter(is_active=True),
        "query": query,
        "selected_category": category_id,
        "selected_status": status,
        "total_medicines": Medicine.objects.count(),
        "active_medicines": Medicine.objects.filter(is_active=True).count(),
        "inactive_medicines": Medicine.objects.filter(is_active=False).count(),
    }

    return render(
        request,
        "medicines/list.html",
        context,
    )


@login_required
def medicine_create(request):
    if request.method == "POST":
        form = MedicineForm(request.POST,request.FILES,)

        if form.is_valid():
            medicine = form.save()
            messages.success(
                request,
                f"{medicine.name} was added successfully.",
            )
            return redirect("medicines:list")
    else:
        form = MedicineForm()

    return render(
        request,
        "medicines/form.html",
        {
            "form": form,
            "page_title": "Add Medicine",
            "submit_text": "Add Medicine",
        },
    )

@login_required
def medicine_detail(request, pk):
    medicine = get_object_or_404(
        Medicine.objects.select_related("category"),
        pk=pk,
    )

    return render(
        request,
        "medicines/detail.html",
        {
            "medicine": medicine,
        },
    )
@login_required
def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)

    if request.method == "POST":
        form = MedicineForm(
        request.POST,
        instance=medicine,
    )

        if form.is_valid():
            medicine = form.save()
            messages.success(
                request,
                f"{medicine.name} was updated successfully.",
            )
            return redirect("medicines:list")
    else:
        form = MedicineForm(instance=medicine)

    return render(
        request,
        "medicines/form.html",
        {
            "form": form,
            "medicine": medicine,
            "page_title": "Edit Medicine",
            "submit_text": "Update Medicine",
        },
    )
@login_required
def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)

    if request.method == "POST":
        medicine_name = medicine.name
        medicine.delete()

        messages.success(
            request,
            f"{medicine_name} was deleted successfully.",
        )

    return redirect("medicines:list")

@login_required
def medicine_toggle_status(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)

    if request.method == "POST":
        medicine.is_active = not medicine.is_active
        medicine.save(update_fields=["is_active", "updated_at"])

        status = "activated" if medicine.is_active else "deactivated"

        messages.success(
            request,
            f"{medicine.name} was {status} successfully.",
        )

    return redirect("medicines:list")