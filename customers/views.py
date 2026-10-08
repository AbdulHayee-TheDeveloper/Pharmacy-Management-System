
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import (
    Count,
    DecimalField,
    F,
    Max,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, Greatest
from django.http import JsonResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.template.loader import render_to_string
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)

from accounts.decorators import role_permission_required
from sales.models import Sale, SalePayment
from sales.views import get_sales_queryset_for_user

from .forms import CustomerForm
from .models import Customer, CustomerSaleLinkAudit


# ============================================================
# HELPERS
# ============================================================

MONEY_ZERO = Decimal("0.00")


def get_customer_sales_queryset(user, customer):
    """
    Completed sales linked to the customer.

    Follow existing Sale History branch access:
    - Assigned user: own branch
    - Unassigned permitted user: all branches

    Caller must separately enforce sales.view_sale.
    """

    return (
        get_sales_queryset_for_user(user)
        .filter(
            customer=customer,
            status=Sale.Status.COMPLETED,
        )
    )


def get_outstanding_expression(prefix=""):
    """
    Outstanding =
        total_amount - paid_amount + change_amount

    The paid_amount field includes original and subsequent
    payments. change_amount is returned cash, not revenue.
    """

    money_field = DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    return Greatest(
        F(f"{prefix}total_amount")
        - F(f"{prefix}paid_amount")
        + F(f"{prefix}change_amount"),
        Value(
            MONEY_ZERO,
            output_field=money_field,
        ),
        output_field=money_field,
    )


# ============================================================
# 1. CUSTOMER LIST
# AJAX SEARCH + FILTERS + FINANCIAL STATISTICS
# ============================================================

@login_required
@role_permission_required("customers.view_customer")
@require_GET
def customer_list(request):

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    customer_type = request.GET.get("type", "").strip()

    valid_statuses = {
        "active",
        "inactive",
    }

    valid_types = {
        value
        for value, label in Customer.CustomerType.choices
    }

    if status not in valid_statuses:
        status = ""

    if customer_type not in valid_types:
        customer_type = ""

    # --------------------------------------------------------
    # SUMMARY STATISTICS
    # --------------------------------------------------------

    base_queryset = Customer.objects.all()

    total_customers = base_queryset.count()

    active_customers = base_queryset.filter(
        is_active=True
    ).count()

    inactive_customers = base_queryset.filter(
        is_active=False
    ).count()

    wholesale_customers = base_queryset.filter(
        customer_type=Customer.CustomerType.WHOLESALE
    ).count()

    customers = base_queryset

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if query:
        customers = customers.filter(
            Q(customer_code__icontains=query)
            | Q(name__icontains=query)
            | Q(phone__icontains=query)
            | Q(alternate_phone__icontains=query)
            | Q(email__icontains=query)
            | Q(city__icontains=query)
        )

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    if status == "active":
        customers = customers.filter(
            is_active=True
        )

    elif status == "inactive":
        customers = customers.filter(
            is_active=False
        )

    # --------------------------------------------------------
    # CUSTOMER TYPE FILTER
    # --------------------------------------------------------

    if customer_type:
        customers = customers.filter(
            customer_type=customer_type
        )

    # --------------------------------------------------------
    # CUSTOMER FINANCIAL STATISTICS
    # --------------------------------------------------------

    can_view_sales = request.user.has_perm(
        "sales.view_sale"
    )

    if can_view_sales:

        sales_filter = Q(
            sales__status=Sale.Status.COMPLETED
        )

        user_branch = getattr(
            request.user,
            "branch",
            None,
        )

        if user_branch is not None:
            sales_filter &= Q(
                sales__branch=user_branch
            )

        money_field = DecimalField(
            max_digits=14,
            decimal_places=2,
        )

        customers = customers.annotate(
            purchase_count=Count(
                "sales",
                filter=sales_filter,
                distinct=True,
            ),

            outstanding_total=Coalesce(
                Sum(
                    get_outstanding_expression(
                        prefix="sales__"
                    ),
                    filter=sales_filter,
                ),
                Value(
                    MONEY_ZERO,
                    output_field=money_field,
                ),
                output_field=money_field,
            ),
        )

    # --------------------------------------------------------
    # ORDERING AND PAGINATION
    # --------------------------------------------------------

    customers = customers.order_by(
        "name",
        "pk",
    )

    paginator = Paginator(
        customers,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "customers": page_obj.object_list,
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "customer_type": customer_type,
        "type_choices": Customer.CustomerType.choices,
        "total_customers": total_customers,
        "active_customers": active_customers,
        "inactive_customers": inactive_customers,
        "wholesale_customers": wholesale_customers,
        "can_view_sales": can_view_sales,
    }

    # --------------------------------------------------------
    # AJAX RESPONSE
    # --------------------------------------------------------

    if request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest":

        html = render_to_string(
            "customers/partials/list_results.html",
            context,
            request=request,
        )

        return JsonResponse({
            "html": html,
        })

    return render(
        request,
        "customers/list.html",
        context,
    )


# ============================================================
# 2. CREATE CUSTOMER
# ============================================================

@login_required
@role_permission_required("customers.add_customer")
@require_http_methods(["GET", "POST"])
def customer_create(request):

    form = CustomerForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        customer = form.save()

        messages.success(
            request,
            (
                f"Customer {customer.customer_code} "
                "created successfully."
            ),
        )

        return redirect(
            "customers:detail",
            pk=customer.pk,
        )

    return render(
        request,
        "customers/form.html",
        {
            "form": form,
            "customer": None,
            "is_edit": False,
            "page_title": "Add Customer",
        },
    )


# ============================================================
# 3. CUSTOMER DETAIL
# PURCHASE HISTORY + FINANCIAL SUMMARY
# PAYMENT COLLECTION HISTORY + LINKING AUDIT
# ============================================================

@login_required
@role_permission_required("customers.view_customer")
@require_GET
def customer_detail(request, pk):

    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    can_view_sales = request.user.has_perm(
        "sales.view_sale"
    )

    context = {
        "customer": customer,
        "can_view_sales": can_view_sales,
    }

    # Don't expose financial data without permission.
    if not can_view_sales:
        return render(
            request,
            "customers/detail.html",
            context,
        )

    # --------------------------------------------------------
    # BRANCH-SCOPED COMPLETED SALES
    # --------------------------------------------------------

    sales = get_customer_sales_queryset(
        request.user,
        customer,
    )

    sales = sales.annotate(
        outstanding_balance=(
            get_outstanding_expression()
        )
    )

    # --------------------------------------------------------
    # FINANCIAL SUMMARY
    # --------------------------------------------------------

    statistics = sales.aggregate(
        total_purchases=Count("pk"),

        total_spending=Sum(
            "total_amount"
        ),

        total_outstanding=Sum(
            "outstanding_balance"
        ),

        last_purchase=Max(
            "completed_at"
        ),
    )

    total_purchases = (
        statistics["total_purchases"] or 0
    )

    total_spending = (
        statistics["total_spending"]
        or MONEY_ZERO
    )

    total_outstanding = (
        statistics["total_outstanding"]
        or MONEY_ZERO
    )

    total_collected = (
        total_spending - total_outstanding
    )

    # --------------------------------------------------------
    # PURCHASE HISTORY PAGINATION
    # --------------------------------------------------------

    sales = (
        sales
        .select_related(
            "branch",
            "cashier",
        )
        .order_by(
            "-completed_at",
            "-pk",
        )
    )

    sale_paginator = Paginator(
        sales,
        10,
    )

    page_obj = sale_paginator.get_page(
        request.GET.get("page")
    )

    # --------------------------------------------------------
    # ADDITIONAL CUSTOMER PAYMENT HISTORY
    # --------------------------------------------------------

    payments = (
        SalePayment.objects
        .filter(
            sale__customer=customer,
            sale__status=Sale.Status.COMPLETED,
        )
        .select_related(
            "sale",
            "sale__branch",
            "received_by",
        )
    )

    user_branch = getattr(
        request.user,
        "branch",
        None,
    )

    if user_branch is not None:
        payments = payments.filter(
            sale__branch=user_branch
        )

    payments = payments.order_by(
        "-received_at",
        "-pk",
    )

    payment_paginator = Paginator(
        payments,
        10,
    )

    payment_page_obj = payment_paginator.get_page(
        request.GET.get("payment_page")
    )

    # --------------------------------------------------------
    # HISTORICAL INVOICE LINKING AUDIT
    # --------------------------------------------------------

    can_view_link_audits = (
        request.user.has_perm(
            "customers.change_customer"
        )
        and request.user.has_perm(
            "sales.change_sale"
        )
    )

    link_audits = CustomerSaleLinkAudit.objects.none()

    if can_view_link_audits:

        link_audits = (
            CustomerSaleLinkAudit.objects
            .filter(
                customer=customer
            )
            .select_related(
                "sale",
                "sale__branch",
                "linked_by",
            )
        )

        if user_branch is not None:
            link_audits = link_audits.filter(
                sale__branch=user_branch
            )

        link_audits = link_audits.order_by(
            "-linked_at",
            "-pk",
        )[:20]

    # --------------------------------------------------------
    # TEMPLATE CONTEXT
    # --------------------------------------------------------

    context.update({
        "total_purchases": total_purchases,
        "total_spending": total_spending,
        "total_outstanding": total_outstanding,
        "total_collected": total_collected,
        "last_purchase": statistics["last_purchase"],

        "sales": page_obj.object_list,
        "page_obj": page_obj,

        "payments": payment_page_obj.object_list,
        "payment_page_obj": payment_page_obj,

        "link_audits": link_audits,
        "can_view_link_audits": can_view_link_audits,
    })

    return render(
        request,
        "customers/detail.html",
        context,
    )


# ============================================================
# 4. EDIT CUSTOMER
# ============================================================

@login_required
@role_permission_required("customers.change_customer")
@require_http_methods(["GET", "POST"])
def customer_edit(request, pk):

    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    form = CustomerForm(
        request.POST or None,
        instance=customer,
    )

    if request.method == "POST" and form.is_valid():

        customer = form.save()

        messages.success(
            request,
            "Customer updated successfully.",
        )

        return redirect(
            "customers:detail",
            pk=customer.pk,
        )

    return render(
        request,
        "customers/form.html",
        {
            "form": form,
            "customer": customer,
            "is_edit": True,
            "page_title": "Edit Customer",
        },
    )


# ============================================================
# 5. ACTIVATE / DEACTIVATE CUSTOMER
# ============================================================

@login_required
@role_permission_required("customers.change_customer")
@require_POST
def customer_toggle_status(request, pk):

    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    customer.is_active = not customer.is_active

    customer.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            f"{customer.name} is now "
            f"{'active' if customer.is_active else 'inactive'}."
        ),
    )

    return redirect(
        "customers:detail",
        pk=customer.pk,
    )


# ============================================================
# 6. POS REGISTERED CUSTOMER SEARCH
# ============================================================

@login_required
@role_permission_required("sales.add_sale")
@require_GET
def customer_pos_search(request):

    query = request.GET.get(
        "q", ""
    ).strip()

    if len(query) < 2:
        return JsonResponse({
            "results": [],
        })

    customers = (
        Customer.objects
        .filter(is_active=True)
        .filter(
            Q(name__icontains=query)
            | Q(customer_code__icontains=query)
            | Q(phone__icontains=query)
            | Q(alternate_phone__icontains=query)
            | Q(email__icontains=query)
        )
        .order_by(
            "name",
            "pk",
        )[:20]
    )

    results = [
        {
            "id": customer.pk,
            "code": customer.customer_code,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "customer_type": (
                customer.get_customer_type_display()
            ),
        }
        for customer in customers
    ]

    return JsonResponse({
        "results": results,
    })


# ============================================================
# 7. VERIFIED HISTORICAL SALE LINKING
# ============================================================

@login_required
@role_permission_required("customers.change_customer")
@role_permission_required("sales.change_sale")
@role_permission_required("sales.view_sale")
@require_http_methods(["GET", "POST"])
def customer_link_sale(request, pk):

    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    error = None

    if request.method == "POST":

        sale_id = request.POST.get(
            "sale_id", ""
        ).strip()

        invoice_confirmation = request.POST.get(
            "invoice_confirmation", ""
        ).strip()

        reason = request.POST.get(
            "reason", ""
        ).strip()

        confirmed = (
            request.POST.get("confirm") == "yes"
        )

        # ----------------------------------------------------
        # INPUT VALIDATION
        # ----------------------------------------------------

        if not confirmed:
            error = (
                "You must confirm that this invoice "
                "belongs to the selected customer."
            )

        elif len(reason) < 10:
            error = (
                "Please provide a linking reason "
                "of at least 10 characters."
            )

        elif len(reason) > 2000:
            error = (
                "Linking reason is too long."
            )

        elif not sale_id.isdecimal() or int(sale_id) <= 0:
            error = (
                "Select a valid invoice."
            )

        elif not customer.is_active:
            error = (
                "Cannot link an invoice to "
                "an inactive customer."
            )

        else:

            # ------------------------------------------------
            # ATOMIC LINKING + AUDIT
            # ------------------------------------------------

            with transaction.atomic():

                authorized_sales = get_sales_queryset_for_user(
                    request.user
                )

                sale = (
                    authorized_sales
                    .select_related(None)
                    .select_for_update(of=("self",))
                    .filter(pk=int(sale_id))
                    .first()
                )

                if sale is None:
                    error = (
                        "Invoice not found or "
                        "access denied."
                    )

                elif sale.status != Sale.Status.COMPLETED:
                    error = (
                        "Only completed sales "
                        "can be linked."
                    )

                elif sale.customer_id is not None:
                    error = (
                        "This invoice is already linked "
                        "to a customer."
                    )

                elif (
                    invoice_confirmation
                    != sale.invoice_number
                ):
                    error = (
                        "Invoice confirmation "
                        "does not match."
                    )

                else:

                    sale.customer = customer

                    sale.save(
                        update_fields=[
                            "customer",
                            "updated_at",
                        ]
                    )

                    CustomerSaleLinkAudit.objects.create(
                        customer=customer,
                        sale=sale,
                        linked_by=request.user,
                        reason=reason,
                    )

                    messages.success(
                        request,
                        (
                            f"Invoice {sale.invoice_number} "
                            f"linked to {customer.name}."
                        ),
                    )

                    return redirect(
                        "customers:detail",
                        pk=customer.pk,
                    )

    # --------------------------------------------------------
    # SEARCH UNLINKED SALES
    # --------------------------------------------------------

    query = request.GET.get(
        "q", ""
    ).strip()

    candidates = Sale.objects.none()

    if len(query) >= 4:

        candidates = (
            get_sales_queryset_for_user(
                request.user
            )
            .filter(
                customer__isnull=True,
                status=Sale.Status.COMPLETED,
                invoice_number__icontains=query,
            )
            .order_by(
                "-created_at"
            )[:20]
        )

    return render(
        request,
        "customers/link_sale.html",
        {
            "customer": customer,
            "candidates": candidates,
            "query": query,
            "error": error,
        },
    )
