
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_GET, require_POST
from accounts.decorators import role_permission_required
from .forms import MedicineForm, CategoryForm
from .models import Category, Medicine


# ============================================================
# MEDICINE LIST
# ============================================================

@login_required
@role_permission_required("medicines.view_medicine")
def medicine_list(request):

    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()

    medicines = Medicine.objects.select_related(
        "category"
    ).all()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if query:
        medicines = medicines.filter(
            Q(name__icontains=query)
            | Q(generic_name__icontains=query)
            | Q(manufacturer__icontains=query)
            | Q(barcode__icontains=query)
            | Q(sku__icontains=query)
        )

    # --------------------------------------------------------
    # CATEGORY FILTER
    # --------------------------------------------------------

    if category_id:
        medicines = medicines.filter(
            category_id=category_id
        )

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    if status == "active":
        medicines = medicines.filter(
            is_active=True
        )

    elif status == "inactive":
        medicines = medicines.filter(
            is_active=False
        )

    # --------------------------------------------------------
    # PAGE CONTEXT
    # --------------------------------------------------------

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


# ============================================================
# ADD MEDICINE
# ============================================================
#
# Medicine and inventory creation were integrated earlier.
#
# The existing inventory_create view supports:
#
# 1. Creating a new medicine.
# 2. Selecting an existing medicine.
# 3. Creating a medicine inventory batch.
#
# Therefore, do not create a second MedicineForm workflow.
# Redirect users to the existing Inventory entry page.
#
# ============================================================




@login_required
@role_permission_required("medicines.add_medicine")
def medicine_create(request):

    if request.method == "POST":
        form = MedicineForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            medicine = form.save()

            messages.success(
                request,
                f"{medicine.name} added successfully. "
                "Stock can be added later from Inventory.",
            )

            return redirect(
                "medicines:detail",
                pk=medicine.pk,
            )

    else:
        form = MedicineForm()

    return render(
        request,
        "medicines/edit.html",
        {
            "form": form,
            "medicine": None,
            "page_title": "Add Medicine",
            "submit_text": "Save Medicine",
            "has_inventory_batches": False,
        },
    )





# ============================================================
# MEDICINE DETAIL
# ============================================================

@login_required
@role_permission_required("medicines.view_medicine")
def medicine_detail(request, pk):

    medicine = get_object_or_404(
        Medicine.objects.select_related("category"),
        pk=pk,
    )

    today = timezone.localdate()

    # --------------------------------------------------------
    # AVAILABLE STOCK
    # --------------------------------------------------------
    #
    # Only include batches that are:
    #
    # - Active
    # - Not expired
    # - In stock
    # - Assigned to an active branch
    #
    # --------------------------------------------------------

    available_batches = medicine.inventory_batches.filter(
        is_active=True,
        quantity__gt=0,
        expiry_date__gte=today,
        branch__is_active=True,
    )

    # --------------------------------------------------------
    # BRANCH ISOLATION
    # --------------------------------------------------------

    # Owner / Superuser can view all-branch stock.
    if not request.user.is_superuser:

        # Normal employees require an assigned branch.
        if request.user.branch_id is None:

            messages.error(
                request,
                "No branch is assigned to your account. "
                "Please contact the administrator.",
            )

            return redirect(
                "medicines:list"
            )

        # Employees can only view their assigned branch stock.
        available_batches = available_batches.filter(
            branch_id=request.user.branch_id
        )

    # --------------------------------------------------------
    # STOCK SUMMARY
    # --------------------------------------------------------

    stock_summary = available_batches.aggregate(
        total_quantity=Sum("quantity")
    )

    total_quantity = (
        stock_summary["total_quantity"] or 0
    )

    # --------------------------------------------------------
    # PACK / LOOSE UNIT CALCULATIONS
    # --------------------------------------------------------

    pack_size = medicine.pack_size or 1

    full_packs = total_quantity // pack_size

    loose_units = total_quantity % pack_size

    # --------------------------------------------------------
    # BATCH / BRANCH COUNTS
    # --------------------------------------------------------

    total_batches = available_batches.count()

    total_branches = (
        available_batches
        .values("branch_id")
        .distinct()
        .count()
    )

    # --------------------------------------------------------
    # PAGE CONTEXT
    # --------------------------------------------------------

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


# ============================================================
# EDIT MEDICINE
# ============================================================

@login_required
@role_permission_required("medicines.change_medicine")
def medicine_edit(request, pk):

    medicine = get_object_or_404(
        Medicine.objects.select_related("category"),
        pk=pk,
    )

    # --------------------------------------------------------
    # POST: UPDATE MEDICINE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GET: DISPLAY EXISTING MEDICINE
    # --------------------------------------------------------

    else:

        form = MedicineForm(
            instance=medicine,
        )

    # --------------------------------------------------------
    # PAGE CONTEXT
    # --------------------------------------------------------

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


# ============================================================
# CATEGORY MANAGEMENT
# ============================================================

@login_required
@require_GET
@role_permission_required("medicines.view_category")
def category_list(request):
    categories = Category.objects.all()

    return render(
        request,
        "medicines/categories.html",
        {
            "categories": categories,
            "form": CategoryForm(),
            "editing_category": None,
        },
    )


@login_required
@role_permission_required("medicines.add_category")
def category_create(request):
    if request.method != "POST":
        return redirect("medicines:categories")

    form = CategoryForm(request.POST)

    if form.is_valid():
        category = form.save()

        messages.success(
            request,
            f"Category '{category.name}' created successfully.",
        )
        return redirect("medicines:categories")

    return render(
        request,
        "medicines/categories.html",
        {
            "categories": Category.objects.all(),
            "form": form,
            "editing_category": None,
        },
        status=400,
    )


@login_required
@role_permission_required("medicines.change_category")
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Category updated successfully.",
            )
            return redirect("medicines:categories")
    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        "medicines/categories.html",
        {
            "categories": Category.objects.all(),
            "form": form,
            "editing_category": category,
        },
    )


@login_required
@require_POST
@role_permission_required("medicines.change_category")
def category_toggle_status(request, pk):
    category = get_object_or_404(Category, pk=pk)

    category.is_active = not category.is_active
    category.save(update_fields=["is_active", "updated_at"])

    action = "activated" if category.is_active else "deactivated"

    messages.success(
        request,
        f"Category '{category.name}' {action} successfully.",
    )

    return redirect("medicines:categories")
