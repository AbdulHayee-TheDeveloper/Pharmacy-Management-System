
import csv
from decimal import Decimal
from .pdf_reports import generate_report_pdf
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import (
    Http404,
    HttpResponse,
    JsonResponse,
    StreamingHttpResponse,
)
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from accounts.decorators import role_permission_required
from branches.models import Branch

from .services import (
    ReportValidationError,
    build_inventory_report,
    build_profit_report,
    build_purchase_report,
    build_sales_report,
    get_inventory_report_queryset,
    get_purchase_queryset,
    get_report_filters,
    get_sales_queryset,
    money,
    user_is_admin,
)


# ============================================================
# SHARED RESPONSE HELPERS
# ============================================================

def error_response(message, status=400):
    return JsonResponse(
        {
            "success": False,
            "error": message,
        },
        status=status,
    )


def build_json_report(request, report_builder):
    try:
        filters = get_report_filters(request)
        data = report_builder(filters)

    except ReportValidationError as exc:
        return error_response(str(exc))

    return JsonResponse({
        "success": True,
        "data": data,
    })


def safe_csv_cell(value):
    """
    Protect exported CSV data against spreadsheet
    formula injection.
    """
    if value is None:
        return ""

    value = str(value)

    if value.lstrip().startswith(
        ("=", "+", "-", "@", "\t", "\r", "\n")
    ):
        return "'" + value

    return value


def make_csv_response(filename, headers, rows):
    """
    General helper for small CSV responses.
    Larger exports use StreamingHttpResponse.
    """
    response = HttpResponse(
        content_type="text/csv; charset=utf-8"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"

    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow(headers)

    for row in rows:
        writer.writerow([
            safe_csv_cell(value)
            for value in row
        ])

    return response


class CSVBuffer:
    """
    File-like buffer used by csv.writer
    with StreamingHttpResponse.

    IMPORTANT:
    This helper must not have Django decorators.
    """

    def write(self, value):
        return value


def streaming_csv_response(filename, row_generator):
    """
    Shared CSV streaming response helper.
    """
    response = StreamingHttpResponse(
        row_generator,
        content_type="text/csv; charset=utf-8",
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"

    return response


# ============================================================
# REPORTS DASHBOARD — HTML PAGE
# ============================================================

@login_required
@role_permission_required("sales.view_sale")
@role_permission_required("purchases.view_purchase")
@role_permission_required("inventory.view_inventorybatch")
@require_GET
def dashboard(request):
    """
    Main Reports & Analytics dashboard.

    Financial data is loaded separately using
    the dashboard_data JSON endpoint.
    """

    can_filter_branches = user_is_admin(request.user)

    branches = (
        Branch.objects.order_by("name")
        if can_filter_branches
        else Branch.objects.none()
    )

    context = {
        "branches": branches,
        "can_filter_branches": can_filter_branches,
    }

    return render(
        request,
        "reports/dashboard.html",
        context,
    )


# ============================================================
# REPORTS DASHBOARD — JSON DATA
# ============================================================

@login_required
@role_permission_required("sales.view_sale")
@role_permission_required("purchases.view_purchase")
@role_permission_required("inventory.view_inventorybatch")
@require_GET
def dashboard_data(request):
    """
    Combined JSON response for dashboard cards,
    charts and summary tables.
    """

    try:
        filters = get_report_filters(request)

        sales = build_sales_report(filters)

        purchases = build_purchase_report(filters)

        inventory = build_inventory_report(filters)

    except ReportValidationError as exc:
        return error_response(str(exc))

    return JsonResponse({
        "success": True,
        "data": {
            "filters": sales["filters"],

            "sales": sales["summary"],

            "purchases": purchases["summary"],

            "inventory": inventory["summary"],

            "daily_sales": sales["daily_sales"],

            "top_medicines": sales["top_medicines"],

            "top_suppliers": purchases["top_suppliers"],

            "notes": {
                "inventory_is_current_snapshot": True,
                "collected_is_current_invoice_balance": True,
            },
        },
    })


# ============================================================
# SALES REPORT — JSON
# ============================================================

@login_required
@role_permission_required("sales.view_sale")
@require_GET
def sales_report(request):
    return build_json_report(
        request,
        build_sales_report,
    )


# ============================================================
# PURCHASE REPORT — JSON
# ============================================================

@login_required
@role_permission_required("purchases.view_purchase")
@require_GET
def purchase_report(request):
    return build_json_report(
        request,
        build_purchase_report,
    )


# ============================================================
# INVENTORY REPORT — JSON
# ============================================================

@login_required
@role_permission_required("inventory.view_inventorybatch")
@require_GET
def inventory_report(request):
    return build_json_report(
        request,
        build_inventory_report,
    )


# ============================================================
# ESTIMATED GROSS PROFIT REPORT — JSON
# ============================================================

@login_required
@role_permission_required("sales.view_sale")
@role_permission_required("inventory.view_inventorybatch")
@require_GET
def profit_report(request):
    return build_json_report(
        request,
        build_profit_report,
    )


# ============================================================
# PHASE 9.5 — COMPLETE SALES CSV EXPORT
# ============================================================

@login_required
@role_permission_required("sales.view_sale")
@require_GET
def export_sales_csv(request):
    """
    Export all completed sales in the selected
    date range and authorized branch scope.

    One row represents one completed invoice.

    Collected and outstanding values reflect
    the invoice's current payment balance.
    """

    try:
        filters = get_report_filters(request)

    except ReportValidationError as exc:
        return error_response(str(exc))

    sales = (
        get_sales_queryset(filters)
        .order_by("completed_at", "pk")
        .values(
            "invoice_number",
            "completed_at",
            "branch__name",
            "customer_name",
            "phone",
            "subtotal",
            "discount_amount",
            "tax_amount",
            "total_amount",
            "paid_amount",
            "change_amount",
            "payment_method",
            "payment_status",
            "status",
        )
    )

    def generate_rows():
        writer = csv.writer(CSVBuffer())

        yield "\ufeff"

        yield writer.writerow([
            "Invoice Number",
            "Completed At",
            "Branch",
            "Customer Name",
            "Customer Phone",
            "Subtotal (PKR)",
            "Discount (PKR)",
            "Tax (PKR)",
            "Invoice Total (PKR)",
            "Net Collected (PKR)",
            "Outstanding (PKR)",
            "Checkout Method",
            "Payment Status",
            "Sale Status",
        ])

        for sale in sales.iterator(chunk_size=500):

            total = Decimal(sale["total_amount"])
            paid = Decimal(sale["paid_amount"])
            change = Decimal(sale["change_amount"])

            collected = max(
                Decimal("0.00"),
                min(
                    total,
                    paid - change,
                ),
            )

            outstanding = max(
                Decimal("0.00"),
                total - collected,
            )

            completed_at = sale["completed_at"]

            if completed_at is not None:
                completed_at = timezone.localtime(
                    completed_at
                ).strftime("%Y-%m-%d %H:%M:%S")
            else:
                completed_at = ""

            values = [
                sale["invoice_number"],
                completed_at,
                sale["branch__name"],
                sale["customer_name"],
                sale["phone"],
                money(sale["subtotal"]),
                money(sale["discount_amount"]),
                money(sale["tax_amount"]),
                money(total),
                money(collected),
                money(outstanding),
                sale["payment_method"],
                sale["payment_status"],
                sale["status"],
            ]

            yield writer.writerow([
                safe_csv_cell(value)
                for value in values
            ])

    return streaming_csv_response(
        "sales_transactions.csv",
        generate_rows(),
    )


# ============================================================
# PHASE 9.5 — COMPLETE PURCHASE CSV EXPORT
# ============================================================

@login_required
@role_permission_required("purchases.view_purchase")
@require_GET
def export_purchases_csv(request):
    """
    Export all non-draft, non-cancelled
    purchase orders.

    One CSV row represents one purchase order,
    not one stock receipt.
    """

    try:
        filters = get_report_filters(request)

    except ReportValidationError as exc:
        return error_response(str(exc))

    purchases = (
        get_purchase_queryset(filters)
        .order_by("purchase_date", "pk")
        .values(
            "purchase_number",
            "purchase_date",
            "branch__name",
            "supplier__name",
            "supplier_invoice_number",
            "status",
            "subtotal",
            "discount_amount",
            "tax_amount",
            "total_amount",
            "expected_delivery_date",
        )
    )

    def generate_rows():
        writer = csv.writer(CSVBuffer())

        yield "\ufeff"

        yield writer.writerow([
            "Purchase Number",
            "Purchase Date",
            "Branch",
            "Supplier",
            "Supplier Invoice",
            "Status",
            "Subtotal (PKR)",
            "Discount (PKR)",
            "Tax (PKR)",
            "Ordered Value (PKR)",
            "Expected Delivery Date",
        ])

        for purchase in purchases.iterator(
            chunk_size=500
        ):

            purchase_date = purchase[
                "purchase_date"
            ]

            expected_date = purchase[
                "expected_delivery_date"
            ]

            values = [
                purchase["purchase_number"],

                (
                    purchase_date.isoformat()
                    if purchase_date
                    else ""
                ),

                purchase["branch__name"],

                purchase["supplier__name"],

                purchase["supplier_invoice_number"],

                purchase["status"],

                money(purchase["subtotal"]),

                money(purchase["discount_amount"]),

                money(purchase["tax_amount"]),

                money(purchase["total_amount"]),

                (
                    expected_date.isoformat()
                    if expected_date
                    else ""
                ),
            ]

            yield writer.writerow([
                safe_csv_cell(value)
                for value in values
            ])

    return streaming_csv_response(
        "purchase_orders.csv",
        generate_rows(),
    )


# ============================================================
# PHASE 9.4 — COMPLETE INVENTORY CSV EXPORT
# ============================================================

@login_required
@role_permission_required("inventory.view_inventorybatch")
@require_GET
def export_inventory_csv(request):
    """
    Export every authorized inventory batch.

    No 100-record limit.

    Uses queryset.iterator() to process
    records in chunks.
    """

    try:
        filters = get_report_filters(request)

    except ReportValidationError as exc:
        return error_response(str(exc))

    queryset = get_inventory_report_queryset(filters)

    def generate_rows():
        writer = csv.writer(CSVBuffer())

        yield "\ufeff"

        yield writer.writerow([
            "Medicine",
            "Branch",
            "Batch Number",
            "Quantity (Units)",
            "Units per Pack",
            "Expiry Date",
            "Purchase Price per Pack (PKR)",
            "Selling Price per Pack (PKR)",
            "Estimated Cost Value (PKR)",
            "Estimated Retail Value (PKR)",
            "Active",
            "Expired",
        ])

        today = timezone.localdate()

        for batch in queryset.iterator(
            chunk_size=500
        ):

            pack_size = max(
                int(
                    batch.medicine.pack_size or 1
                ),
                1,
            )

            quantity = Decimal(
                batch.quantity
            )

            cost_value = money(
                quantity
                * batch.purchase_price
                / Decimal(pack_size)
            )

            retail_value = money(
                quantity
                * batch.selling_price
                / Decimal(pack_size)
            )

            expired = (
                batch.expiry_date < today
                and batch.quantity > 0
            )

            values = [
                batch.medicine.name,
                batch.branch.name,
                batch.batch_number,
                batch.quantity,
                pack_size,
                batch.expiry_date.isoformat(),
                batch.purchase_price,
                batch.selling_price,
                cost_value,
                retail_value,
                (
                    "Yes"
                    if batch.is_active
                    else "No"
                ),
                (
                    "Yes"
                    if expired
                    else "No"
                ),
            ]

            yield writer.writerow([
                safe_csv_cell(value)
                for value in values
            ])

    return streaming_csv_response(
        "inventory_report.csv",
        generate_rows(),
    )


# ============================================================
# PHASE 9.3 — DETAILED REPORT PAGE CONFIGURATION
# ============================================================

REPORT_PAGE_CONFIG = {

    "sales": {
        "title": "Sales Report",
        "description": (
            "Completed sales, collections, "
            "payment breakdown and top medicines."
        ),
        "api_name": "reports:sales",
        "export_name": "reports:export_sales",
        "permission": "sales.view_sale",
        "icon": "fa-receipt",
    },

    "purchases": {
        "title": "Purchase Report",
        "description": (
            "Purchase orders, supplier performance "
            "and stock receiving activity."
        ),
        "api_name": "reports:purchases",
        "export_name": "reports:export_purchases",
        "permission": "purchases.view_purchase",
        "icon": "fa-cart-flatbed",
    },

    "inventory": {
        "title": "Inventory Report",
        "description": (
            "Current batch stock, inventory "
            "valuation and expiry monitoring."
        ),
        "api_name": "reports:inventory",
        "export_name": "reports:export_inventory",
        "permission": "inventory.view_inventorybatch",
        "icon": "fa-boxes-stacked",
    },

    "profit": {
        "title": "Estimated Profit Report",
        "description": (
            "Estimated cost of goods sold, "
            "gross profit and profit margin."
        ),
        "api_name": "reports:profit",
        "export_name": None,
        "permission": "sales.view_sale",
        "additional_permission": (
            "inventory.view_inventorybatch"
        ),
        "icon": "fa-chart-pie",
    },
}


# ============================================================
# PHASE 9.3 — DETAILED REPORT HTML PAGES
# ============================================================

@login_required
@require_GET
def detailed_report_page(request, report_type):
    """
    Renders the detailed report interface.

    Permissions are validated server-side
    before the template is rendered.
    """

    config = REPORT_PAGE_CONFIG.get(
        report_type
    )

    if config is None:
        raise Http404(
            "Report not found."
        )

    required_permissions = [
        config["permission"]
    ]

    additional_permission = config.get(
        "additional_permission"
    )

    if additional_permission:
        required_permissions.append(
            additional_permission
        )

    if not all(
        request.user.has_perm(permission)
        for permission in required_permissions
    ):
        raise PermissionDenied(
            "You are not authorized to access this report."
        )

    can_filter_branches = user_is_admin(
        request.user
    )

    branches = (
        Branch.objects.order_by("name")
        if can_filter_branches
        else Branch.objects.none()
    )

    context = {
        "report_type": report_type,
        "report_config": config,
        "branches": branches,
        "can_filter_branches": can_filter_branches,
    }

    return render(
        request,
        "reports/detail.html",
        context,
    )


# ============================================================
# PHASE 9.6 — PROFESSIONAL PDF REPORT EXPORT
# ============================================================

@login_required
@require_GET
def export_report_pdf(request, report_type):
    """
    Export one of four business reports as A4 PDF.

    Permissions and report filters are checked
    before database data is passed to ReportLab.
    """

    allowed_types = {
        "sales": ["sales.view_sale"],

        "purchases": [
            "purchases.view_purchase"
        ],

        "inventory": [
            "inventory.view_inventorybatch"
        ],

        "profit": [
            "sales.view_sale",
            "inventory.view_inventorybatch",
        ],
    }

    required_permissions = allowed_types.get(
        report_type
    )

    if required_permissions is None:
        raise Http404("Report not found.")

    if not all(
        request.user.has_perm(permission)
        for permission in required_permissions
    ):
        raise PermissionDenied(
            "You are not authorized to export this report."
        )

    try:
        filters = get_report_filters(request)

    except ReportValidationError as exc:
        return error_response(str(exc))

    # Resolve branch label after branch authorization.
    if filters.branch_id:
        branch_label = (
            Branch.objects
            .filter(pk=filters.branch_id)
            .values_list("name", flat=True)
            .first()
            or "Selected Branch"
        )
    else:
        branch_label = "All Branches"

    full_name = request.user.get_full_name()

    generated_by = (
        full_name.strip()
        or request.user.get_username()
    )

    pdf_content = generate_report_pdf(
        report_type=report_type,
        filters=filters,
        generated_by=generated_by,
        branch_label=branch_label,
    )

    response = HttpResponse(
        pdf_content,
        content_type="application/pdf",
    )

    filename = (
        f"pharmacare_{report_type}_"
        f"{timezone.localdate().isoformat()}.pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"

    return response


# ============================================================
# PHASE 9.8 — SERVER-SIDE REPORT PAGINATION
# ============================================================

REPORT_PAGE_SIZE = 20
REPORT_SEARCH_MAX_LENGTH = 100


def paginate_report_queryset(request, queryset):
    """
    Shared database pagination.

    A page contains at most 20 records.
    """

    paginator = Paginator(
        queryset,
        REPORT_PAGE_SIZE,
    )

    page = paginator.get_page(
        request.GET.get("page", "1")
    )

    return paginator, page


def paginated_response(paginator, page, rows):
    """
    Consistent JSON structure for the frontend.
    """

    return JsonResponse({
        "success": True,
        "data": {
            "results": rows,
            "pagination": {
                "page": page.number,
                "per_page": REPORT_PAGE_SIZE,
                "total_records": paginator.count,
                "total_pages": paginator.num_pages,
                "has_previous": page.has_previous(),
                "has_next": page.has_next(),
            },
        },
    })


@login_required
@role_permission_required("sales.view_sale")
@require_GET
def sales_report_rows(request):
    """
    Paginated completed sales invoices.

    Security/date restrictions come from the
    existing reporting services.
    """

    try:
        filters = get_report_filters(request)

    except ReportValidationError as exc:
        return error_response(str(exc))

    query = request.GET.get("q", "").strip()

    if len(query) > REPORT_SEARCH_MAX_LENGTH:
        return error_response(
            "Search text is too long."
        )

    queryset = get_sales_queryset(filters)

    if query:
        queryset = queryset.filter(
            Q(invoice_number__icontains=query)
            | Q(customer_name__icontains=query)
            | Q(branch__name__icontains=query)
        )

    queryset = queryset.order_by(
        "-completed_at",
        "-pk",
    )

    paginator, page = paginate_report_queryset(
        request,
        queryset,
    )

    rows = list(
        page.object_list.values(
            "id",
            "invoice_number",
            "completed_at",
            "customer_name",
            "branch__name",
            "subtotal",
            "discount_amount",
            "tax_amount",
            "total_amount",
            "paid_amount",
            "change_amount",
            "payment_status",
            "payment_method",
        )
    )

    return paginated_response(
        paginator,
        page,
        rows,
    )


@login_required
@role_permission_required("purchases.view_purchase")
@require_GET
def purchase_report_rows(request):
    """
    Paginated purchase order records.
    """

    try:
        filters = get_report_filters(request)

    except ReportValidationError as exc:
        return error_response(str(exc))

    query = request.GET.get("q", "").strip()

    if len(query) > REPORT_SEARCH_MAX_LENGTH:
        return error_response(
            "Search text is too long."
        )

    queryset = get_purchase_queryset(filters)

    if query:
        queryset = queryset.filter(
            Q(purchase_number__icontains=query)
            | Q(supplier__name__icontains=query)
            | Q(supplier_invoice_number__icontains=query)
            | Q(branch__name__icontains=query)
        )

    queryset = queryset.order_by(
        "-purchase_date",
        "-pk",
    )

    paginator, page = paginate_report_queryset(
        request,
        queryset,
    )

    rows = list(
        page.object_list.values(
            "id",
            "purchase_number",
            "purchase_date",
            "supplier__name",
            "branch__name",
            "status",
            "total_amount",
            "subtotal",
            "discount_amount",
            "tax_amount",
        )
    )

    return paginated_response(
        paginator,
        page,
        rows,
    )


@login_required
@role_permission_required("inventory.view_inventorybatch")
@require_GET
def inventory_report_rows(request):
    """
    Paginated inventory batch records.

    Includes all authorized batches rather than
    restricting to the first 100.
    """

    try:
        filters = get_report_filters(request)

    except ReportValidationError as exc:
        return error_response(str(exc))

    query = request.GET.get("q", "").strip()

    if len(query) > REPORT_SEARCH_MAX_LENGTH:
        return error_response(
            "Search text is too long."
        )

    queryset = get_inventory_report_queryset(
        filters
    )

    if query:
        queryset = queryset.filter(
            Q(medicine__name__icontains=query)
            | Q(medicine__sku__icontains=query)
            | Q(batch_number__icontains=query)
            | Q(branch__name__icontains=query)
        )

    queryset = queryset.order_by(
        "expiry_date",
        "medicine__name",
        "pk",
    )

    paginator, page = paginate_report_queryset(
        request,
        queryset,
    )

    today = timezone.localdate()

    rows = []

    for batch in page.object_list:

        pack_size = max(
            int(batch.medicine.pack_size or 1),
            1,
        )

        quantity_units = Decimal(
            batch.quantity
        )

        estimated_cost = money(
            quantity_units
            * batch.purchase_price
            / Decimal(pack_size)
        )

        estimated_retail = money(
            quantity_units
            * batch.selling_price
            / Decimal(pack_size)
        )

        expired = (
            batch.expiry_date < today
        )

        expiring_soon = (
            not expired
            and batch.expiry_date
            <= today + timezone.timedelta(days=30)
        )

        rows.append({
            "id": batch.pk,
            "medicine": batch.medicine.name,
            "sku": batch.medicine.sku,
            "batch_number": batch.batch_number,
            "branch": batch.branch.name,
            "expiry_date": batch.expiry_date.isoformat(),
            "quantity_units": batch.quantity,
            "pack_size": pack_size,
            "estimated_cost_value": str(
                estimated_cost
            ),
            "estimated_retail_value": str(
                estimated_retail
            ),
            "active": batch.is_active,
            "expired": expired,
            "expiring_soon": expiring_soon,
        })

    return paginated_response(
        paginator,
        page,
        rows,
    )


@login_required
@role_permission_required("sales.view_sale")
@role_permission_required("inventory.view_inventorybatch")
@require_GET
def profit_report_rows(request):
    """
    Profit report contains aggregated metrics,
    not invoice-level detailed profit records.

    Its breakdown remains available through
    the existing profit JSON API.
    """
    return error_response(
        "Estimated Profit uses summary calculations "
        "and does not support transaction pagination.",
        status=400,
    )
