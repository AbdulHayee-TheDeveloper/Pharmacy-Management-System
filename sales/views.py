import json
from django.contrib import messages
from django.shortcuts import redirect
from .payment_forms import ReceivePaymentForm
from .payment_services import (
    PaymentError,
    get_sale_outstanding,
    receive_sale_payment,
)
from core_settings.tax import (
    get_default_tax_rate,
    get_effective_tax_rate,
)
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from accounts.decorators import role_permission_required
from inventory.models import InventoryBatch

from .models import Sale
from .services import CheckoutError, checkout_sale


# ================================================================
# HELPERS
# ================================================================


def get_pos_branch(user):
    """
    Return the branch assigned to the logged-in user.

    POS operations require a branch because inventory and sales
    are branch-specific.
    """
    return getattr(user, "branch", None)



def get_sales_queryset_for_user(user):
    """
    Branch-safe sales queryset.

    Superuser:
        Can view all branches.

    Normal users:
        Can only view assigned branch sales.

    Users without a branch:
        Cannot view any sales.
    """

    queryset = Sale.objects.select_related(
        "branch",
        "cashier",
    )

    if not user.is_authenticated or not user.is_active:
        return queryset.none()

    if user.is_superuser:
        return queryset

    if user.branch_id is None:
        return queryset.none()

    return queryset.filter(
        branch_id=user.branch_id
    )



# ================================================================
# POS PAGE
# ================================================================


@login_required
@role_permission_required("sales.add_sale")
@ensure_csrf_cookie
def pos(request):
    return render(
        request,
        "sales/pos.html",
    )


# ================================================================
# PRODUCT SEARCH
# ================================================================


@login_required
@role_permission_required("sales.add_sale")
@require_GET
def product_search(request):
    branch = get_pos_branch(
        request.user
    )

    if not branch:
        return JsonResponse(
            {
                "error": (
                    "Your account is not assigned "
                    "to a branch."
                )
            },
            status=400,
        )

    query = request.GET.get(
        "q",
        "",
    ).strip()
    default_tax_rate = get_default_tax_rate()
    if len(query) < 2:
        return JsonResponse(
            {
                
                "results": [],
            }
        )

    today = timezone.localdate()

    batches = (
        InventoryBatch.objects
        .select_related(
            "medicine",
            "medicine__category",
            "branch",
        )
        .filter(
            branch=branch,
            is_active=True,
            medicine__is_active=True,
            expiry_date__gte=today,
            quantity__gt=0,
        )
        .filter(
            Q(
                medicine__name__icontains=query
            )
            | Q(
                medicine__generic_name__icontains=query
            )
            | Q(
                medicine__barcode__icontains=query
            )
            | Q(
                medicine__sku__icontains=query
            )
            | Q(
                batch_number__icontains=query
            )
        )
        .order_by(
            "expiry_date",
            "medicine__name",
        )[:30]
    )

    results = []

    for batch in batches:
        medicine = batch.medicine

        results.append(
            {
                "batch_id": batch.id,
                "medicine_id": medicine.id,

                "name": medicine.name,
                "generic_name": (
                    medicine.generic_name
                ),
                "strength": medicine.strength,

                "dosage_form": (
                    medicine.get_dosage_form_display()
                ),

                "category": (
                    medicine.category.name
                    if medicine.category
                    else ""
                ),

                "batch_number": (
                    batch.batch_number
                ),

                "expiry_date": (
                    batch.expiry_date.isoformat()
                ),

                # Base/smallest-unit stock
                "quantity": batch.quantity,
                "stock_units": batch.quantity,

                "full_packs_available": (
                    batch.full_packs_available
                ),

                "loose_units_available": (
                    batch.loose_units_available
                ),

                "stock_display": (
                    batch.stock_display
                ),

                # Medicine packaging
                "pack_size": (
                    medicine.pack_size
                ),

                "unit": medicine.unit,

                "unit_label": (
                    medicine.get_unit_display()
                ),

                "allow_loose_sale": (
                    medicine.allow_loose_sale
                ),

                # Prices
                "selling_price": str(
                    batch.selling_price
                ),

                "pack_price": str(
                    batch.selling_price
                ),

                "unit_price": str(
                    batch.unit_selling_price
                ),

                "purchase_price": str(
                    batch.purchase_price
                ),

                "unit_purchase_price": str(
                    batch.unit_purchase_price
                ),

                # Identifiers
                "barcode": (
                    medicine.barcode or ""
                ),

                "sku": (
                    medicine.sku or ""
                ),

                "tax_rate": str(
                get_effective_tax_rate(
                medicine,
                default_rate=default_tax_rate,
                    )
                ),
                "uses_pharmacy_default_tax": (
                    medicine.use_pharmacy_default_tax
                ),
                    }
                )

    return JsonResponse(
        {
            "results": results,
        }
    )


# ================================================================
# CHECKOUT
# ================================================================


@login_required
@role_permission_required("sales.add_sale")
@require_POST
def checkout(request):
    branch = get_pos_branch(
        request.user
    )

    if not branch:
        return JsonResponse(
            {
                "error": (
                    "Your account is not assigned "
                    "to a branch."
                )
            },
            status=400,
        )

    try:
        payload = json.loads(
            request.body.decode(
                "utf-8"
            )
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return JsonResponse(
            {
                "error": (
                    "Invalid checkout request."
                )
            },
            status=400,
        )

    items = payload.get(
        "items",
        [],
    )

    if not isinstance(
        items,
        list,
    ):
        return JsonResponse(
            {
                "error": (
                    "Invalid cart data."
                )
            },
            status=400,
        )

    try:
        sale = checkout_sale(
            user=request.user,
            branch=branch,
            customer_id=payload.get("customer_id"),
            items=items,

            payment_method=payload.get(
                "payment_method",
                Sale.PaymentMethod.CASH,
            ),

            paid_amount=payload.get(
                "paid_amount",
                "0",
            ),

            discount_amount=payload.get(
                "discount_amount",
                "0",
            ),

            customer_name=payload.get(
                "customer_name",
                "",
            ),

            customer_phone=payload.get(
                "customer_phone",
                "",
            ),

            notes=payload.get(
                "notes",
                "",
            ),
        )

    except CheckoutError as exc:
        return JsonResponse(
            {
                "error": str(exc),
            },
            status=400,
        )

    return JsonResponse(
        {
            "message": (
                "Sale completed successfully."
            ),

            "sale": {
                "id": sale.id,

                "invoice_number": (
                    sale.invoice_number
                ),

                "subtotal": str(
                    sale.subtotal
                ),

                "discount_amount": str(
                    sale.discount_amount
                ),

                "tax_amount": str(
                    sale.tax_amount
                ),

                "total_amount": str(
                    sale.total_amount
                ),

                "paid_amount": str(
                    sale.paid_amount
                ),

                "change_amount": str(
                    sale.change_amount
                ),

                "payment_method": (
                    sale.payment_method
                ),

                "payment_status": (
                    sale.payment_status
                ),
            },
        },
        status=201,
    )


# ================================================================
# SALE HISTORY
# ================================================================


@login_required
@role_permission_required("sales.view_sale")
@require_GET
def sale_history(request):
    sales = get_sales_queryset_for_user(
        request.user
    )

    # ------------------------------------------------------------
    # QUERY PARAMETERS
    # ------------------------------------------------------------

    query = request.GET.get(
        "q",
        "",
    ).strip()

    payment_method = request.GET.get(
        "payment_method",
        "",
    ).strip()

    payment_status = request.GET.get(
        "payment_status",
        "",
    ).strip()

    sale_status = request.GET.get(
        "status",
        "",
    ).strip()

    date_from = request.GET.get(
        "date_from",
        "",
    ).strip()

    date_to = request.GET.get(
        "date_to",
        "",
    ).strip()

    # ------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------

    if query:
        sales = sales.filter(
            Q(
                invoice_number__icontains=query
            )
            | Q(
                customer_name__icontains=query
            )
            | Q(
                customer_phone__icontains=query
            )
            | Q(
                cashier__username__icontains=query
            )
            | Q(
                cashier__first_name__icontains=query
            )
            | Q(
                cashier__last_name__icontains=query
            )
        )

    # ------------------------------------------------------------
    # PAYMENT METHOD FILTER
    # ------------------------------------------------------------

    valid_payment_methods = {
        choice[0]
        for choice
        in Sale.PaymentMethod.choices
    }

    if (
        payment_method
        in valid_payment_methods
    ):
        sales = sales.filter(
            payment_method=payment_method
        )

    # ------------------------------------------------------------
    # PAYMENT STATUS FILTER
    # ------------------------------------------------------------

    valid_payment_statuses = {
        choice[0]
        for choice
        in Sale.PaymentStatus.choices
    }

    if (
        payment_status
        in valid_payment_statuses
    ):
        sales = sales.filter(
            payment_status=payment_status
        )

    # ------------------------------------------------------------
    # SALE STATUS FILTER
    # ------------------------------------------------------------

    valid_sale_statuses = {
        choice[0]
        for choice
        in Sale.Status.choices
    }

    if (
        sale_status
        in valid_sale_statuses
    ):
        sales = sales.filter(
            status=sale_status
        )

    # ------------------------------------------------------------
    # DATE FILTERS
    # ------------------------------------------------------------

    if date_from:
        sales = sales.filter(
            created_at__date__gte=date_from
        )

    if date_to:
        sales = sales.filter(
            created_at__date__lte=date_to
        )

    # ------------------------------------------------------------
    # SORT
    # ------------------------------------------------------------

    sales = sales.order_by(
        "-created_at"
    )

    # ------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------

    paginator = Paginator(
        sales,
        20,
    )

    page_obj = paginator.get_page(
        request.GET.get(
            "page"
        )
    )

    context = {
        "page_obj": page_obj,
        "sales": page_obj.object_list,

        "query": query,
        "selected_payment_method": (
            payment_method
        ),
        "selected_payment_status": (
            payment_status
        ),
        "selected_status": (
            sale_status
        ),
        "date_from": date_from,
        "date_to": date_to,

        "payment_methods": (
            Sale.PaymentMethod.choices
        ),

        "payment_statuses": (
            Sale.PaymentStatus.choices
        ),

        "sale_statuses": (
            Sale.Status.choices
        ),
    }

    return render(
        request,
        "sales/history.html",
        context,
    )


# ================================================================
# SALE DETAIL / INVOICE
# ================================================================


@login_required
@role_permission_required("sales.view_sale")
@require_GET
def sale_detail(request, pk):
    queryset = (
        get_sales_queryset_for_user(
            request.user
        )
        .prefetch_related(
            "items",
            "items__medicine",
            "items__inventory_batch",
        )
    )

    sale = get_object_or_404(
        queryset,
        pk=pk,
    )

    context = {
        "sale": sale,
        "outstanding": get_sale_outstanding(sale),
        "additional_payments": sale.additional_payments.select_related( 
    "received_by"
).all(),
        "sale_items": (
            sale.items.all()
        ),
    }

    return render(
        request,
        "sales/detail.html",
        context,
    )

# ================================================================
# SALE RECEIPT
# ================================================================


@login_required
@role_permission_required("sales.view_sale")
@require_GET
def sale_receipt(request, pk):
    queryset = (
        get_sales_queryset_for_user(
            request.user
        )
        .prefetch_related(
            "items",
            "items__medicine",
            "items__inventory_batch",
        )
    )

    sale = get_object_or_404(
        queryset,
        pk=pk,
    )

    context = {
        "sale": sale,
        "sale_items": sale.items.all(),
    }

    return render(
        request,
        "sales/receipt.html",
        context,
    )


# ============================================================
# CUSTOMER PAYMENT COLLECTION
# ============================================================

@login_required
@role_permission_required("sales.change_sale")
def sale_receive_payment(request, pk):

    authorized_sales = get_sales_queryset_for_user(
        request.user
    )

    sale = get_object_or_404(
        authorized_sales,
        pk=pk,
    )

    if sale.status != Sale.Status.COMPLETED:
        messages.error(
            request,
            "Only completed sales can receive payments."
        )
        return redirect(
            "sales:detail",
            pk=sale.pk,
        )

    outstanding = get_sale_outstanding(sale)

    if outstanding <= 0:
        messages.info(
            request,
            "This sale is already fully paid."
        )
        return redirect(
            "sales:detail",
            pk=sale.pk,
        )

    form = ReceivePaymentForm(
        request.POST or None,
        sale=sale,
    )

    if request.method == "POST" and form.is_valid():

        try:
            payment = receive_sale_payment(
                sale_id=sale.pk,
                user=request.user,
                authorized_sales=authorized_sales,
                amount=form.cleaned_data["amount"],
                payment_method=form.cleaned_data[
                    "payment_method"
                ],
                reference_number=form.cleaned_data[
                    "reference_number"
                ],
                notes=form.cleaned_data["notes"],
            )

        except PaymentError as exc:
            form.add_error(None, str(exc))

        else:
            messages.success(
                request,
                (
                    f"Payment {payment.payment_number} "
                    "received successfully."
                ),
            )

            return redirect(
                "sales:detail",
                pk=sale.pk,
            )

    return render(
        request,
        "sales/receive_payment.html",
        {   "settled_amount": sale.paid_amount - sale.change_amount,
            "sale": sale,
            "form": form,
            "outstanding": outstanding,
        },
    )
