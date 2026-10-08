
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.http import JsonResponse
from django.template.loader import render_to_string
from accounts.decorators import role_permission_required

from .forms import SupplierForm
from .models import Supplier


# ============================================================
# SUPPLIER LIST
# ============================================================


@login_required
@role_permission_required("suppliers.view_supplier")
def supplier_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip().lower()

    if status not in ("active", "inactive"):
        status = ""

    # Summary cards: all suppliers, independent of filters
    all_suppliers = Supplier.objects.all()

    total_suppliers = all_suppliers.count()
    active_suppliers = all_suppliers.filter(
        is_active=True
    ).count()
    inactive_suppliers = all_suppliers.filter(
        is_active=False
    ).count()

    # Filtered queryset
    suppliers = all_suppliers

    if query:
        suppliers = suppliers.filter(
            Q(supplier_code__icontains=query)
            | Q(name__icontains=query)
            | Q(company_name__icontains=query)
            | Q(contact_person__icontains=query)
            | Q(phone__icontains=query)
            | Q(alternate_phone__icontains=query)
            | Q(email__icontains=query)
            | Q(ntn__icontains=query)
            | Q(city__icontains=query)
        )

    if status == "active":
        suppliers = suppliers.filter(is_active=True)

    elif status == "inactive":
        suppliers = suppliers.filter(is_active=False)

    suppliers = suppliers.order_by("name", "pk")

    # Pagination: 10 suppliers per page
    paginator = Paginator(suppliers, 10)

    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "suppliers": page_obj.object_list,
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "total_suppliers": total_suppliers,
        "active_suppliers": active_suppliers,
        "inactive_suppliers": inactive_suppliers,
    }

    # AJAX request: return HTML partial inside JSON
    if request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest":

        results_html = render_to_string(
            "suppliers/partials/supplier_results.html",
            context,
            request=request,
        )

        return JsonResponse({
            "html": results_html,
            "total_results": paginator.count,
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
        })

    # Normal browser request: full HTML page
    return render(
        request,
        "suppliers/list.html",
        context,
    )



# ============================================================
# CREATE SUPPLIER
# ============================================================

@login_required
@role_permission_required("suppliers.add_supplier")
def supplier_create(request):

    if request.method == "POST":
        form = SupplierForm(request.POST)

        if form.is_valid():
            supplier = form.save()

            messages.success(
                request,
                f"Supplier '{supplier.name}' created successfully.",
            )

            return redirect(
                "suppliers:detail",
                pk=supplier.pk,
            )

    else:
        form = SupplierForm()

    context = {
        "form": form,
        "page_title": "Add Supplier",
        "is_edit": False,
    }

    return render(
        request,
        "suppliers/form.html",
        context,
    )


# ============================================================
# SUPPLIER DETAIL
# ============================================================

@login_required
@role_permission_required("suppliers.view_supplier")
def supplier_detail(request, pk):

    supplier = get_object_or_404(
        Supplier,
        pk=pk,
    )

    context = {
        "supplier": supplier,
    }

    return render(
        request,
        "suppliers/detail.html",
        context,
    )


# ============================================================
# EDIT SUPPLIER
# ============================================================

@login_required
@role_permission_required("suppliers.change_supplier")
def supplier_edit(request, pk):

    supplier = get_object_or_404(
        Supplier,
        pk=pk,
    )

    if request.method == "POST":

        form = SupplierForm(
            request.POST,
            instance=supplier,
        )

        if form.is_valid():

            # SupplierForm disables opening_balance
            # on existing records, so forged POST
            # values cannot change it.
            form.save()

            messages.success(
                request,
                f"Supplier '{supplier.name}' updated successfully.",
            )

            return redirect(
                "suppliers:detail",
                pk=supplier.pk,
            )

    else:
        form = SupplierForm(
            instance=supplier,
        )

    context = {
        "form": form,
        "supplier": supplier,
        "page_title": "Edit Supplier",
        "is_edit": True,
    }

    return render(
        request,
        "suppliers/form.html",
        context,
    )
