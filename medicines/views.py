from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from accounts.decorators import role_permission_required

from .models import Category, Medicine


@login_required
@role_permission_required("medicines.view_medicine")
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

    return render(request, "medicines/list.html", context)


@login_required
@role_permission_required("medicines.view_medicine")
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