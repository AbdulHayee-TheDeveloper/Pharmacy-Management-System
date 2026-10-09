
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied
from django.db.models import (
    Count,
    DecimalField,
    F,
    Sum,
    Value,
)
from django.db.models.functions import (
    Coalesce,
    Greatest,
    Least,
    TruncDate,
)
from django.utils import timezone
from django.utils.dateparse import parse_date

from branches.models import Branch
from inventory.models import InventoryBatch
from purchases.models import (
    Purchase,
    PurchaseReceipt,
    PurchaseReceiptItem,
)
from sales.models import Sale, SaleItem


ZERO = Decimal("0.00")
PENNY = Decimal("0.01")

MONEY_FIELD = DecimalField(
    max_digits=18,
    decimal_places=2,
)


class ReportValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ReportFilters:
    date_from: object
    date_to: object
    branch_id: int | None


def money(value):
    return Decimal(
        str(value if value is not None else ZERO)
    ).quantize(PENNY, rounding=ROUND_HALF_UP)


def money_sum(field):
    return Coalesce(
        Sum(field),
        Value(ZERO, output_field=MONEY_FIELD),
        output_field=MONEY_FIELD,
    )


# ============================================================
# BRANCH ACCESS
# ============================================================

def user_is_admin(user):
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


def get_report_filters(request):
    params = request.GET
    today = timezone.localdate()

    default_from = today - timedelta(days=29)

    raw_from = (
        params.get("date_from")
        or params.get("from")
        or ""
    ).strip()

    raw_to = (
        params.get("date_to")
        or params.get("to")
        or ""
    ).strip()

    try:
        date_from = (
            parse_date(raw_from)
            if raw_from
            else default_from
        )

        date_to = (
            parse_date(raw_to)
            if raw_to
            else today
        )

    except ValueError as exc:
        raise ReportValidationError(
            "Invalid calendar date."
        ) from exc

    if date_from is None or date_to is None:
        raise ReportValidationError(
            "Dates must use YYYY-MM-DD format."
        )

    if date_from > date_to:
        raise ReportValidationError(
            "Start date cannot be after end date."
        )

    if (date_to - date_from).days > 365:
        raise ReportValidationError(
            "Maximum report range is 366 days."
        )

    raw_branch = params.get("branch", "").strip()

    if raw_branch and not raw_branch.isdecimal():
        raise ReportValidationError(
            "Invalid branch ID."
        )

    selected_branch_id = (
        int(raw_branch) if raw_branch else None
    )

    if user_is_admin(request.user):

        if selected_branch_id is not None:

            if not Branch.objects.filter(
                pk=selected_branch_id
            ).exists():

                raise ReportValidationError(
                    "Selected branch does not exist."
                )

    else:

        assigned_branch_id = getattr(
            request.user,
            "branch_id",
            None,
        )

        if assigned_branch_id is None:
            raise PermissionDenied(
                "No branch assigned to this account."
            )

        if (
            selected_branch_id is not None
            and selected_branch_id != assigned_branch_id
        ):
            raise PermissionDenied(
                "You cannot access another branch."
            )

        selected_branch_id = assigned_branch_id

    return ReportFilters(
        date_from=date_from,
        date_to=date_to,
        branch_id=selected_branch_id,
    )


def scope_to_branch(queryset, filters, field="branch_id"):
    if filters.branch_id is None:
        return queryset

    return queryset.filter(
        **{field: filters.branch_id}
    )


def date_filter(queryset, filters, field):
    return queryset.filter(
        **{
            f"{field}__gte": filters.date_from,
            f"{field}__lte": filters.date_to,
        }
    )


def filter_info(filters):
    return {
        "date_from": filters.date_from.isoformat(),
        "date_to": filters.date_to.isoformat(),
        "branch_id": filters.branch_id,
    }


# ============================================================
# SALES REPORT
# ============================================================

def get_sales_queryset(filters):
    queryset = Sale.objects.filter(
        status=Sale.Status.COMPLETED,
        completed_at__isnull=False,
    )

    queryset = scope_to_branch(
        queryset,
        filters,
    )

    return date_filter(
        queryset,
        filters,
        "completed_at__date",
    )


def add_sale_amounts(queryset):
    collected = Least(
        Greatest(
            F("paid_amount") - F("change_amount"),
            Value(ZERO, output_field=MONEY_FIELD),
            output_field=MONEY_FIELD,
        ),
        F("total_amount"),
        output_field=MONEY_FIELD,
    )

    return queryset.annotate(
        report_collected=collected,
    ).annotate(
        report_outstanding=Greatest(
            F("total_amount") - F("report_collected"),
            Value(ZERO, output_field=MONEY_FIELD),
            output_field=MONEY_FIELD,
        ),
    )


def build_sales_report(filters):
    sales = add_sale_amounts(
        get_sales_queryset(filters)
    )

    totals = sales.aggregate(
        sale_count=Count("id"),
        revenue=money_sum("total_amount"),
        subtotal=money_sum("subtotal"),
        discounts=money_sum("discount_amount"),
        tax=money_sum("tax_amount"),
        collected=money_sum("report_collected"),
        outstanding=money_sum("report_outstanding"),
    )

    count = totals["sale_count"]

    totals["average_sale"] = (
        money(totals["revenue"] / count)
        if count
        else ZERO
    )

    daily = list(
        sales.annotate(
            day=TruncDate("completed_at")
        )
        .values("day")
        .annotate(
            count=Count("id"),
            revenue=money_sum("total_amount"),
            collected=money_sum("report_collected"),
        )
        .order_by("day")
    )

    payment_methods = list(
        sales.values("payment_method")
        .annotate(
            count=Count("id"),
            revenue=money_sum("total_amount"),
        )
        .order_by("-revenue")
    )

    payment_statuses = list(
        sales.values("payment_status")
        .annotate(
            count=Count("id"),
            outstanding=money_sum(
                "report_outstanding"
            ),
        )
        .order_by("payment_status")
    )

    top_medicines = list(
        SaleItem.objects.filter(
            sale_id__in=sales.values("id")
        )
        .values("medicine_id", "medicine_name")
        .annotate(
            sold_units=Sum("stock_quantity"),
            line_revenue=money_sum("line_total"),
        )
        .order_by("-line_revenue")[:10]
    )

    recent_sales = list(
        sales.order_by("-completed_at")
        .values(
            "id",
            "invoice_number",
            "customer_name",
            "branch__name",
            "completed_at",
            "total_amount",
            "payment_status",
        )[:20]
    )

    return {
        "filters": filter_info(filters),
        "summary": totals,
        "daily_sales": daily,
        "payment_methods": payment_methods,
        "payment_statuses": payment_statuses,
        "top_medicines": top_medicines,
        "recent_sales": recent_sales,
        "notes": {
            "revenue": (
                "Completed invoice totals, excluding "
                "voided and refunded sales."
            ),
            "collected": (
                "Current payments recorded against "
                "invoices completed in this date range. "
                "Not cash received strictly during "
                "this date range."
            ),
        },
    }


# ============================================================
# PURCHASE REPORT
# ============================================================

def get_purchase_queryset(filters):
    queryset = Purchase.objects.exclude(
        status__in=[
            Purchase.Status.DRAFT,
            Purchase.Status.CANCELLED,
        ]
    )

    queryset = scope_to_branch(
        queryset,
        filters,
    )

    return date_filter(
        queryset,
        filters,
        "purchase_date",
    )


def get_receipt_queryset(filters):
    queryset = PurchaseReceipt.objects.all()

    queryset = scope_to_branch(
        queryset,
        filters,
        "purchase__branch_id",
    )

    return date_filter(
        queryset,
        filters,
        "received_at__date",
    )


def build_purchase_report(filters):
    purchases = get_purchase_queryset(filters)
    receipts = get_receipt_queryset(filters)

    purchase_totals = purchases.aggregate(
        order_count=Count("id"),
        ordered_value=money_sum("total_amount"),
        discounts=money_sum("discount_amount"),
        tax=money_sum("tax_amount"),
    )

    order_statuses = list(
        purchases.values("status")
        .annotate(
            count=Count("id"),
            value=money_sum("total_amount"),
        )
        .order_by("status")
    )

    suppliers = list(
        purchases.values(
            "supplier_id",
            "supplier__name",
        )
        .annotate(
            order_count=Count("id"),
            ordered_value=money_sum("total_amount"),
        )
        .order_by("-ordered_value")[:10]
    )

    daily_orders = list(
        purchases.values("purchase_date")
        .annotate(
            count=Count("id"),
            value=money_sum("total_amount"),
        )
        .order_by("purchase_date")
    )

    receipt_items = PurchaseReceiptItem.objects.filter(
        receipt_id__in=receipts.values("id")
    )

    
    receipt_totals = receipt_items.aggregate(
        total_received_packs=Coalesce(
            Sum("received_packs"),
            0,
        ),
        gross_received_cost=Coalesce(
            Sum(
                F("received_packs") * F("purchase_price"),
                output_field=MONEY_FIELD,
            ),
            Value(
                ZERO,
                output_field=MONEY_FIELD,
            ),
            output_field=MONEY_FIELD,
        ),
    )


    recent_orders = list(
        purchases.order_by("-purchase_date", "-id")
        .values(
            "id",
            "purchase_number",
            "supplier__name",
            "branch__name",
            "purchase_date",
            "status",
            "total_amount",
        )[:20]
    )

    recent_receipts = list(
        receipts.order_by("-received_at", "-id")
        .values(
            "id",
            "receipt_number",
            "purchase__purchase_number",
            "received_at",
        )[:20]
    )

    return {
        "filters": filter_info(filters),
        "summary": {
            **purchase_totals,
            "receipt_count": receipts.count(),
            **receipt_totals,
        },
        "order_statuses": order_statuses,
        "top_suppliers": suppliers,
        "daily_orders": daily_orders,
        "recent_orders": recent_orders,
        "recent_receipts": recent_receipts,
        "notes": {
            "ordered_value": (
                "Value of non-draft, non-cancelled "
                "purchase orders dated in the range."
            ),
            "gross_received_cost": (
                "Sum of received packs multiplied by "
                "their receipt price, before allocating "
                "purchase-level discounts or taxes. "
                "Receipts are grouped by delivery date, "
                "which may differ from purchase date."
            ),
        },
    }


# ============================================================
# PHASE 9.4 — INVENTORY REPORT QUERYSET
# ============================================================

def get_inventory_report_queryset(filters):
    """
    All inventory batches visible to the report user.

    Branch restriction is applied before records are
    returned, so CSV exports cannot bypass it.
    """
    queryset = (
        InventoryBatch.objects
        .select_related("medicine", "branch")
        .order_by(
            "expiry_date",
            "medicine__name",
            "pk",
        )
    )

    return scope_to_branch(
        queryset,
        filters,
    )

# ============================================================
# INVENTORY REPORT
# ============================================================

def build_inventory_report(filters):
    today = timezone.localdate()
    expiry_limit = today + timedelta(days=30)

    queryset = get_inventory_report_queryset(filters)

    totals = {
        "batch_count": 0,
        "units_in_stock": 0,
        "out_of_stock_batches": 0,
        "expired_batches": 0,
        "expiring_30_days": 0,
        "inactive_batches": 0,
        "estimated_cost_value": ZERO,
        "estimated_retail_value": ZERO,
    }

    all_rows = []

    for batch in queryset.iterator(chunk_size=500):
        totals["batch_count"] += 1
        totals["units_in_stock"] += batch.quantity

        pack_size = max(
            int(batch.medicine.pack_size or 1),
            1,
        )

        cost_value = (
            Decimal(batch.quantity)
            * batch.purchase_price
            / Decimal(pack_size)
        )

        retail_value = (
            Decimal(batch.quantity)
            * batch.selling_price
            / Decimal(pack_size)
        )

        totals["estimated_cost_value"] += cost_value
        totals["estimated_retail_value"] += retail_value

        expired = (
            batch.expiry_date < today
            and batch.quantity > 0
        )

        expiring = (
            today <= batch.expiry_date <= expiry_limit
            and batch.quantity > 0
        )

        if batch.quantity == 0:
            totals["out_of_stock_batches"] += 1

        if expired:
            totals["expired_batches"] += 1

        if expiring:
            totals["expiring_30_days"] += 1

        if not batch.is_active:
            totals["inactive_batches"] += 1

        all_rows.append({
            "batch_id": batch.pk,
            "medicine": batch.medicine.name,
            "branch": batch.branch.name,
            "batch_number": batch.batch_number,
            "quantity_units": batch.quantity,
            "pack_size": pack_size,
            "expiry_date": batch.expiry_date,
            "expired": expired,
            "expiring_soon": expiring,
            "active": batch.is_active,
            "estimated_cost_value": money(cost_value),
            "estimated_retail_value": money(retail_value),
        })

    totals["estimated_cost_value"] = money(
        totals["estimated_cost_value"]
    )

    totals["estimated_retail_value"] = money(
        totals["estimated_retail_value"]
    )

    all_rows.sort(
        key=lambda row: (
            row["expiry_date"],
            row["medicine"],
        )
    )

    return {
        "as_of": timezone.now(),
        "branch_id": filters.branch_id,
        "summary": totals,
        "batches": all_rows[:100],
        "returned_batch_limit": 100,
        "notes": {
            "snapshot": (
                "Current inventory snapshot. Date range "
                "does not reconstruct historical stock."
            ),
            "valuation": (
                "Estimated using current batch pack "
                "prices and current medicine pack sizes. "
                "Historical costs, changing pack sizes, "
                "discounts, taxes and adjustments can "
                "make actual inventory valuation differ."
            ),
        },
    }


# ============================================================
# ESTIMATED GROSS PROFIT
# ============================================================

def build_profit_report(filters):
    sales = get_sales_queryset(filters)

    totals = sales.aggregate(
        sale_count=Count("id"),
        revenue=money_sum("total_amount"),
        tax=money_sum("tax_amount"),
    )

    # This is an estimate, not historical COGS.
    # InventoryBatch.purchase_price can change after a sale.

    estimated_cogs = ZERO
    item_count = 0

    items = (
        SaleItem.objects.filter(
            sale_id__in=sales.values("id")
        )
        .select_related("inventory_batch")
    )

    for item in items.iterator(chunk_size=500):
        item_count += 1

        pack_size = max(int(item.pack_size), 1)

        batch_cost = (
            item.inventory_batch.purchase_price
        )

        estimated_cogs += (
            Decimal(item.stock_quantity)
            * batch_cost
            / Decimal(pack_size)
        )

    # Sales tax isn't operating revenue.
    net_sales_excluding_tax = (
        totals["revenue"] - totals["tax"]
    )

    estimated_gross_profit = (
        net_sales_excluding_tax - estimated_cogs
    )

    margin = ZERO

    if net_sales_excluding_tax > 0:
        margin = (
            estimated_gross_profit
            / net_sales_excluding_tax
            * Decimal("100")
        )

    return {
        "filters": filter_info(filters),
        "summary": {
            "sale_count": totals["sale_count"],
            "item_count": item_count,
            "revenue_including_tax": money(
                totals["revenue"]
            ),
            "net_sales_excluding_tax": money(
                net_sales_excluding_tax
            ),
            "estimated_cogs": money(
                estimated_cogs
            ),
            "estimated_gross_profit": money(
                estimated_gross_profit
            ),
            "estimated_margin_percent": money(
                margin
            ),
        },
        "is_estimate": True,
        "warning": (
            "This is NOT an audited historical profit "
            "report. SaleItem currently lacks a permanent "
            "purchase-cost snapshot. The calculation uses "
            "the inventory batch's current purchase price "
            "with the sold item's historical pack size. "
            "It also excludes operating expenses, supplier "
            "discount allocation and any unrecorded "
            "returns or cost adjustments."
        ),
    }
