from django.http import JsonResponse
from django.template.loader import render_to_string

from decimal import Decimal

from django.views.decorators.http import require_POST

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.core.exceptions import PermissionDenied

from django.core.paginator import Paginator

from django.db import transaction

from django.db.models import Q, Sum

from django.db.models.functions import Coalesce

from django.shortcuts import (

    get_object_or_404,

    redirect,

    render,

)

from accounts.decorators import role_permission_required

from branches.models import Branch

from .forms import PurchaseForm, PurchaseItemFormSet

from django.db.models import Prefetch

from .models import (

    Purchase,

    PurchaseItem,

    PurchaseReceipt,

    PurchaseReceiptItem,

)

from django.core.exceptions import ValidationError

from django.db import DatabaseError

from .receiving_forms import (

    PurchaseReceivingForm,

    PurchaseReceivingItemFormSet,

)

from .services import (

    receive_purchase_stock,

    StockReceivingError,

)

ZERO = Decimal("0.00")

# ============================================================

# BRANCH ACCESS HELPERS

# ============================================================

def user_is_admin(user):

    """

    Superusers and users whose assigned role

    is named Admin can access all branches.

    Verify the role attribute against the

    existing accounts.User model.

    """

    if user.is_superuser:

        return True

    role = getattr(user, "role", None)

    if isinstance(role, str):

        role_name = role

    else:

        role_name = (

            getattr(role, "name", None)

            or getattr(role, "role_name", None)

            or ""

        )

    return str(role_name).strip().lower() == "admin"

def get_user_branch_id(user):

    """

    Default integration:

    user.branch_id

    If the existing User model stores branch

    elsewhere, adapt only this helper.

    """

    return getattr(user, "branch_id", None)

def get_accessible_branches(user):

    """

    Fail closed if a non-admin user does not

    have a valid branch assignment.

    """

    if user_is_admin(user):

        return Branch.objects.all()

    branch_id = get_user_branch_id(user)

    if not branch_id:

        return Branch.objects.none()

    return Branch.objects.filter(pk=branch_id)

def get_purchase_queryset(user):

    """

    Every purchase read operation must use

    this branch-scoped queryset.

    """

    queryset = Purchase.objects.select_related(

        "supplier",

        "branch",

        "created_by",

    )

    if user_is_admin(user):

        return queryset

    branch_id = get_user_branch_id(user)

    if not branch_id:

        return queryset.none()

    return queryset.filter(branch_id=branch_id)

def configure_purchase_form(form, user):

    """

    Restrict selectable branches on the server,

    not just in the frontend.

    """

    branches = get_accessible_branches(user)

    form.fields["branch"].queryset = branches

    if not user_is_admin(user):

        branch = branches.first()

        if branch:

            form.fields["branch"].initial = branch.pk

    return form

# ============================================================

# PURCHASE TOTAL CALCULATION

# ============================================================

def recalculate_purchase_totals(purchase):

    """

    Recalculate monetary totals using saved

    PurchaseItem records.

    All item prices are per full pack.

    """

    subtotal = purchase.items.aggregate(

        amount=Coalesce(

            Sum("line_total"),

            ZERO,

            output_field=Purchase._meta.get_field(

                "subtotal"

            ),

        )

    )["amount"]

    purchase.subtotal = subtotal

    calculated_total = (

        subtotal

        - purchase.discount_amount

        + purchase.tax_amount

    )

    if calculated_total < ZERO:

        raise ValueError(

            "Purchase total cannot be negative."

        )

    purchase.total_amount = calculated_total

    purchase.save(

        update_fields=[

            "subtotal",

            "total_amount",

            "updated_at",

        ]

    )

# ============================================================

# PURCHASE ITEM SAVE HELPER

# ============================================================

def save_purchase_items(purchase, formset):

    """

    Save all purchase items from a validated

    inline formset.

    Must be called inside transaction.atomic().

    """

    formset.instance = purchase

    items = formset.save(commit=False)

    # Delete removed items only on allowed draft edits.

    for deleted_item in formset.deleted_objects:

        if deleted_item.received_packs > 0:

            raise PermissionDenied(

                "Received purchase items cannot be deleted."

            )

        deleted_item.delete()

    for item in items:

        item.purchase = purchase

        if not item.pk:

            # Preserve medicine pack size at purchase time.

            item.pack_size = item.medicine.pack_size

            item.received_packs = 0

        item.save()

    formset.save_m2m()

    recalculate_purchase_totals(purchase)

# ============================================================

# PURCHASE LIST

# ============================================================

@login_required

@role_permission_required("purchases.view_purchase")

def purchase_list(request):

    query = request.GET.get("q", "").strip()

    status = request.GET.get(

        "status", ""

    ).strip().lower()

    valid_statuses = {

        choice.value

        for choice in Purchase.Status

    }

    if status not in valid_statuses:

        status = ""

    base_queryset = get_purchase_queryset(

        request.user

    )

    # Dashboard summary counters

    total_purchases = base_queryset.count()

    draft_purchases = base_queryset.filter(

        status=Purchase.Status.DRAFT

    ).count()

    ordered_purchases = base_queryset.filter(

        status=Purchase.Status.ORDERED

    ).count()

    received_purchases = base_queryset.filter(

        status=Purchase.Status.RECEIVED

    ).count()

    purchases = base_queryset

    # Search by purchase number, supplier,

    # invoice number and branch.

    if query:

        purchases = purchases.filter(

            Q(purchase_number__icontains=query)

            | Q(supplier__name__icontains=query)

            | Q(supplier__company_name__icontains=query)

            | Q(supplier_invoice_number__icontains=query)

            | Q(branch__name__icontains=query)

        )

    if status:

        purchases = purchases.filter(

            status=status

        )

    purchases = purchases.order_by(

        "-purchase_date",

        "-pk",

    )

    paginator = Paginator(

        purchases,

        10,

    )

    page_obj = paginator.get_page(

        request.GET.get("page")

    )

    context = {

        "purchases": page_obj.object_list,

        "page_obj": page_obj,

        "query": query,

        "status": status,

        "status_choices": Purchase.Status.choices,

        "total_purchases": total_purchases,

        "draft_purchases": draft_purchases,

        "ordered_purchases": ordered_purchases,

        "received_purchases": received_purchases,

    }

    # AJAX: render only results, preserving normal GET fallback.
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "purchases/partials/list_results.html",
            context,
            request=request,
        )
        return JsonResponse({"html": html})

    return render(
        request,
        "purchases/list.html",
        context,
    )

# ============================================================

# PURCHASE CREATE

# ============================================================

@login_required

@role_permission_required("purchases.add_purchase")

def purchase_create(request):

    accessible_branches = get_accessible_branches(

        request.user

    )

    if not accessible_branches.exists():

        raise PermissionDenied(

            "You are not assigned to an accessible branch."

        )

    # The unsaved instance must be shared by

    # PurchaseForm and PurchaseItemFormSet.

    purchase = Purchase(

        created_by=request.user,

        status=Purchase.Status.DRAFT,

    )

    if request.method == "POST":

        form = PurchaseForm(

            request.POST,

            instance=purchase,

        )

        form = configure_purchase_form(

            form,

            request.user,

        )

        formset = PurchaseItemFormSet(

            request.POST,

            instance=purchase,

            prefix="items",

        )

        form_valid = form.is_valid()

        formset_valid = formset.is_valid()

        if form_valid and formset_valid:

            with transaction.atomic():

                purchase = form.save(commit=False)

                purchase.created_by = request.user

                purchase.status = (

                    Purchase.Status.DRAFT

                )

                # Never allow a branch submitted outside

                # the user's authorized branch queryset.

                if not accessible_branches.filter(

                    pk=purchase.branch_id

                ).exists():

                    raise PermissionDenied(

                        "Invalid purchase branch."

                    )

                purchase.full_clean()

                purchase.save()

                save_purchase_items(

                    purchase,

                    formset,

                )

            messages.success(

                request,

                (

                    f"Purchase {purchase.purchase_number} "

                    "created successfully."

                ),

            )

            return redirect(

                "purchases:detail",

                pk=purchase.pk,

            )

    else:

        form = PurchaseForm(

            instance=purchase,

        )

        form = configure_purchase_form(

            form,

            request.user,

        )

        formset = PurchaseItemFormSet(

            instance=purchase,

            prefix="items",

        )

    context = {

        "form": form,

        "formset": formset,

        "purchase": None,

        "is_edit": False,

        "page_title": "Create Purchase Order",

    }

    return render(

        request,

        "purchases/form.html",

        context,

    )

# ============================================================

# PURCHASE DETAIL

# ============================================================

@login_required

@role_permission_required("purchases.view_purchase")

def purchase_detail(request, pk):

    purchase = get_object_or_404(

        get_purchase_queryset(request.user)

        .prefetch_related("items__medicine"),

        pk=pk,

    )

    items = purchase.items.all()

    total_ordered_packs = sum(

        item.ordered_packs

        for item in items

    )

    total_received_packs = sum(

        item.received_packs

        for item in items

    )

    receipts = (

    PurchaseReceipt.objects

    .filter(purchase=purchase)

    .select_related("received_by")

    .prefetch_related(

        Prefetch(

            "items",

            queryset=(

                PurchaseReceiptItem.objects

                .select_related(

                    "purchase_item__medicine",

                    "inventory_batch",

                )

                .order_by("pk")

            ),

        )

    )

    .order_by("-received_at", "-pk")

)

    context = {
    "purchase": purchase,
    "items": items,
    "total_ordered_packs": total_ordered_packs,
    "total_received_packs": total_received_packs,
    "is_draft": (
        purchase.status == Purchase.Status.DRAFT
    ),
    "receipts": receipts,
}

    return render(

        request,

        "purchases/detail.html",

        context,

    )

# ============================================================

# PURCHASE EDIT

# ============================================================

@login_required

@role_permission_required("purchases.change_purchase")

def purchase_edit(request, pk):

    accessible_branches = get_accessible_branches(

        request.user

    )

    if request.method == "POST":

        with transaction.atomic():

            purchase = get_object_or_404(

                get_purchase_queryset(request.user)

                .select_for_update(),

                pk=pk,

            )

            if purchase.status != Purchase.Status.DRAFT:

                raise PermissionDenied(

                    "Only draft purchases can be edited."

                )

            # Once receiving starts, normal editing

            # must not alter the purchase.

            if purchase.items.filter(

                received_packs__gt=0

            ).exists():

                raise PermissionDenied(

                    "This purchase contains received stock."

                )

            form = PurchaseForm(

                request.POST,

                instance=purchase,

            )

            form = configure_purchase_form(

                form,

                request.user,

            )

            formset = PurchaseItemFormSet(

                request.POST,

                instance=purchase,

                prefix="items",

            )

            form_valid = form.is_valid()

            formset_valid = formset.is_valid()

            if form_valid and formset_valid:

                updated_purchase = form.save(

                    commit=False

                )

                # These fields belong to system logic,

                # not user-submitted form data.

                updated_purchase.created_by_id = (

                    purchase.created_by_id

                )

                updated_purchase.status = (

                    Purchase.Status.DRAFT

                )

                if not accessible_branches.filter(

                    pk=updated_purchase.branch_id

                ).exists():

                    raise PermissionDenied(

                        "Invalid purchase branch."

                    )

                updated_purchase.full_clean()

                updated_purchase.save()

                save_purchase_items(

                    updated_purchase,

                    formset,

                )

                messages.success(

                    request,

                    "Purchase order updated successfully.",

                )

                return redirect(

                    "purchases:detail",

                    pk=updated_purchase.pk,

                )

    else:

        purchase = get_object_or_404(

            get_purchase_queryset(request.user),

            pk=pk,

        )

        if purchase.status != Purchase.Status.DRAFT:

            raise PermissionDenied(

                "Only draft purchases can be edited."

            )

        if purchase.items.filter(

            received_packs__gt=0

        ).exists():

            raise PermissionDenied(

                "This purchase contains received stock."

            )

        form = PurchaseForm(

            instance=purchase,

        )

        form = configure_purchase_form(

            form,

            request.user,

        )

        formset = PurchaseItemFormSet(

            instance=purchase,

            prefix="items",

        )

    context = {

        "form": form,

        "formset": formset,

        "purchase": purchase,

        "is_edit": True,

        "page_title": "Edit Purchase Order",

    }

    return render(

        request,

        "purchases/form.html",

        context,

    )

# ============================================================

# PHASE 7.7 — CONFIRM PURCHASE ORDER

# DRAFT -> ORDERED

# ============================================================

@login_required

@role_permission_required("purchases.change_purchase")

@require_POST

def purchase_confirm(request, pk):

    with transaction.atomic():

        # Lock purchase to prevent concurrent status changes.

        purchase = get_object_or_404(

            get_purchase_queryset(

                request.user

            ).select_for_update(),

            pk=pk,

        )

        # Only draft purchases can be confirmed.

        if purchase.status != Purchase.Status.DRAFT:

            messages.error(

                request,

                "Only draft purchase orders can be confirmed.",

            )

            return redirect(

                "purchases:detail",

                pk=purchase.pk,

            )

        # A purchase must contain medicine items.

        items = list(

            purchase.items.select_related(

                "medicine"

            ).all()

        )

        if not items:

            messages.error(

                request,

                "Add at least one medicine before confirming.",

            )

            return redirect(

                "purchases:detail",

                pk=purchase.pk,

            )

        # Validate saved item quantities and prices.

        for item in items:

            if item.ordered_packs < 1:

                messages.error(

                    request,

                    "Purchase contains an invalid medicine quantity.",

                )

                return redirect(

                    "purchases:detail",

                    pk=purchase.pk,

                )

            if item.pack_size < 1:

                messages.error(

                    request,

                    "Purchase contains an invalid pack size.",

                )

                return redirect(

                    "purchases:detail",

                    pk=purchase.pk,

                )

            if item.received_packs != 0:

                messages.error(

                    request,

                    "Draft purchase cannot contain received stock.",

                )

                return redirect(

                    "purchases:detail",

                    pk=purchase.pk,

                )

            if (

                item.purchase_price < ZERO

                or item.selling_price < ZERO

                or item.discount_amount < ZERO

            ):

                messages.error(

                    request,

                    "Purchase contains invalid pricing.",

                )

                return redirect(

                    "purchases:detail",

                    pk=purchase.pk,

                )

        # Refresh totals before confirmation.

        recalculate_purchase_totals(purchase)

        # Confirm the purchase order.

        purchase.status = Purchase.Status.ORDERED

        purchase.save(

            update_fields=[

                "status",

                "updated_at",

            ]

        )

    messages.success(

        request,

        (

            f"Purchase {purchase.purchase_number} "

            "confirmed successfully. "

            "The order is now marked as Ordered."

        ),

    )

    return redirect(

        "purchases:detail",

        pk=purchase.pk,

    )

# ============================================================

# PHASE 7.8.4 — PURCHASE STOCK RECEIVING

# ============================================================

@login_required

@role_permission_required("purchases.change_purchase")

def purchase_receive(request, pk):

    """

    Receive supplier-delivered stock against an

    Ordered or Partially Received purchase.

    Stock changes are performed exclusively by

    receive_purchase_stock() inside a transaction.

    """

    purchase = get_object_or_404(

        get_purchase_queryset(request.user),

        pk=pk,

    )

    allowed_statuses = {

        Purchase.Status.ORDERED,

        Purchase.Status.PARTIALLY_RECEIVED,

    }

    # Completed, cancelled and draft purchases

    # cannot receive stock.

    if purchase.status not in allowed_statuses:

        messages.error(

            request,

            "Stock receiving is only allowed for "

            "Ordered or Partially Received purchases.",

        )

        return redirect(

            "purchases:detail",

            pk=purchase.pk,

        )

    # Get branches that the current user may access.

    authorized_branches = get_accessible_branches(

        request.user

    )

    if not authorized_branches.filter(

        pk=purchase.branch_id

    ).exists():

        raise PermissionDenied(

            "You cannot receive stock for this branch."

        )

    if request.method == "POST":

        header_form = PurchaseReceivingForm(

            request.POST

        )

        item_formset = PurchaseReceivingItemFormSet(

            request.POST,

            purchase=purchase,

            prefix="receiving",

        )

        header_valid = header_form.is_valid()

        items_valid = item_formset.is_valid()

        if header_valid and items_valid:

            try:

                receipt = receive_purchase_stock(

                    purchase_id=purchase.pk,

                    received_by=request.user,

                    items=(

                        item_formset.get_receiving_items()

                    ),

                    authorized_branches=(

                        authorized_branches

                    ),

                    supplier_delivery_note=(

                        header_form.cleaned_data[

                            "supplier_delivery_note"

                        ]

                    ),

                    notes=(

                        header_form.cleaned_data[

                            "notes"

                        ]

                    ),

                )

            except StockReceivingError as exc:

                messages.error(

                    request,

                    str(exc),

                )

            except ValidationError as exc:

                messages.error(

                    request,

                    "; ".join(exc.messages),

                )

            except DatabaseError:

                # Do not expose database internals to

                # the browser.

                messages.error(

                    request,

                    "Stock receiving could not be "

                    "completed due to a database error. "

                    "No stock changes were committed. "

                    "Please retry or contact the administrator.",

                )

            else:

                messages.success(

                    request,

                    f"Stock received successfully. "

                    f"Receipt: {receipt.receipt_number}",

                )

                return redirect(

                    "purchases:detail",

                    pk=purchase.pk,

                )

        else:

            messages.error(

                request,

                "Please correct the receiving form errors.",

            )

    else:

        header_form = PurchaseReceivingForm()

        item_formset = PurchaseReceivingItemFormSet(

            purchase=purchase,

            prefix="receiving",

        )

    # Remaining medicines are displayed in the

    # receiving page and used by the item dropdown.

    remaining_items = [

        item

        for item in (

            purchase.items

            .select_related("medicine")

            .order_by("medicine__name", "pk")

        )

        if item.remaining_packs > 0

    ]

    context = {

        "purchase": purchase,

        "header_form": header_form,

        "item_formset": item_formset,

        "remaining_items": remaining_items,

        "page_title": (

            f"Receive Stock - {purchase.purchase_number}"

        ),

    }

    return render(

        request,

        "purchases/receive.html",

        context,

    )
