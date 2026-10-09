from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone

from inventory.models import InventoryBatch
from core_settings.operational import (
    get_operational_settings, low_stock_batches, expiring_soon_batches,
)
from medicines.models import Medicine
from sales.models import Sale


def get_branch_queryset(queryset, user):
    """
    Scope branch-specific data safely.

    Superuser:
        Can see data from all branches.

    Normal user with branch:
        Can see only assigned branch.

    Normal user without branch:
        Gets no branch-specific operational data.
    """
    if user.is_superuser:
        return queryset

    if user.branch_id:
        return queryset.filter(
            branch_id=user.branch_id
        )

    return queryset.none()


def calculate_percentage_change(current, previous):
    """
    Calculate percentage difference between
    current and previous values.
    """
    current = Decimal(current or 0)
    previous = Decimal(previous or 0)

    if previous == 0:
        if current > 0:
            return Decimal("100.0")

        return Decimal("0.0")

    return (
        (current - previous)
        / previous
        * Decimal("100")
    ).quantize(
        Decimal("0.1")
    )


@login_required
def dashboard(request):
    user = request.user

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    options = get_operational_settings()

    # ============================================================
    # PERMISSIONS
    # ============================================================

    can_view_sales = user.has_perm(
        "sales.view_sale"
    )

    can_add_sale = user.has_perm(
        "sales.add_sale"
    )

    can_view_inventory = user.has_perm(
        "inventory.view_inventorybatch"
    )

    can_add_inventory = user.has_perm(
        "inventory.add_inventorybatch"
    )

    can_view_medicines = user.has_perm(
        "medicines.view_medicine"
    )

    can_change_medicines = user.has_perm(
        "medicines.change_medicine"
    )

    # ============================================================
    # DEFAULT CONTEXT
    # ============================================================

    context = {
        "can_view_sales": can_view_sales,
        "can_add_sale": can_add_sale,
        "can_view_inventory": can_view_inventory,
        "can_add_inventory": can_add_inventory,
        "can_view_medicines": can_view_medicines,
        "can_change_medicines": can_change_medicines,

        "today_sales": Decimal("0.00"),
        "yesterday_sales": Decimal("0.00"),
        "sales_change": Decimal("0.0"),

        "today_orders": 0,
        "yesterday_orders": 0,
        "orders_change": Decimal("0.0"),

        "recent_sales": [],
        "sales_chart": [],

        "low_stock_count": 0,
        "out_of_stock_count": 0,
        "expiring_soon_count": 0,
        "expiry_alert_days": options["expiry_alert_days"],
        "low_stock_threshold": options["low_stock_threshold"],
        "expired_count": 0,

        "low_stock_batches": [],
        "expiring_batches": [],
        "out_of_stock_batches": [],

        "total_medicines": 0,
        "active_medicines": 0,
    }

    # ============================================================
    # SALES DATA
    # ============================================================

    if can_view_sales:
        sales_queryset = get_branch_queryset(
            Sale.objects.select_related(
                "branch",
                "cashier",
            ),
            user,
        )

        completed_sales = sales_queryset.filter(
            status=Sale.Status.COMPLETED
        )

        # --------------------------------------------------------
        # Today's sales
        # --------------------------------------------------------

        today_queryset = completed_sales.filter(
            completed_at__date=today
        )

        today_sales = (
            today_queryset.aggregate(
                total=Sum("total_amount")
            )["total"]
            or Decimal("0.00")
        )

        today_orders = today_queryset.count()

        # --------------------------------------------------------
        # Yesterday
        # --------------------------------------------------------

        yesterday_queryset = completed_sales.filter(
            completed_at__date=yesterday
        )

        yesterday_sales = (
            yesterday_queryset.aggregate(
                total=Sum("total_amount")
            )["total"]
            or Decimal("0.00")
        )

        yesterday_orders = (
            yesterday_queryset.count()
        )

        sales_change = calculate_percentage_change(
            today_sales,
            yesterday_sales,
        )

        orders_change = calculate_percentage_change(
            today_orders,
            yesterday_orders,
        )

        # --------------------------------------------------------
        # Recent sales
        # --------------------------------------------------------

        recent_sales = (
            completed_sales
            .order_by("-completed_at", "-created_at")[:5]
        )

        # --------------------------------------------------------
        # Last 7 days chart
        # --------------------------------------------------------

        chart_data = []

        for offset in range(6, -1, -1):
            chart_date = (
                today - timedelta(days=offset)
            )

            total = (
                completed_sales
                .filter(
                    completed_at__date=chart_date
                )
                .aggregate(
                    total=Sum("total_amount")
                )["total"]
                or Decimal("0.00")
            )

            chart_data.append(
                {
                    "date": chart_date,
                    "label": chart_date.strftime("%a"),
                    "amount": total,
                    "height": 0,
                }
            )

        max_chart_amount = max(
            (
                item["amount"]
                for item in chart_data
            ),
            default=Decimal("0.00"),
        )

        if max_chart_amount > 0:
            for item in chart_data:
                height = int(
                    (
                        item["amount"]
                        / max_chart_amount
                    )
                    * 100
                )

                if (
                    item["amount"] > 0
                    and height < 5
                ):
                    height = 5

                item["height"] = height

        context.update(
            {
                "today_sales": today_sales,
                "yesterday_sales": yesterday_sales,
                "sales_change": sales_change,

                "today_orders": today_orders,
                "yesterday_orders": yesterday_orders,
                "orders_change": orders_change,

                "recent_sales": recent_sales,
                "sales_chart": chart_data,
            }
        )

    # ============================================================
    # INVENTORY DATA
    # ============================================================

    if can_view_inventory:
        inventory_queryset = get_branch_queryset(
            InventoryBatch.objects.select_related(
                "medicine",
                "branch",
            ),
            user,
        )

        # --------------------------------------------------------
        # Low Stock
        # --------------------------------------------------------

        low_stock_queryset = low_stock_batches(
            inventory_queryset,
            options["low_stock_threshold"],
            today=today,
        ).order_by("quantity", "expiry_date")

        low_stock_count = (
            low_stock_queryset.count()
        )

        # --------------------------------------------------------
        # Out of Stock
        # --------------------------------------------------------

        out_of_stock_queryset = (
            inventory_queryset.filter(
                is_active=True,
                quantity=0,
            )
            .order_by(
                "medicine__name"
            )
        )

        out_of_stock_count = (
            out_of_stock_queryset.count()
        )

        # --------------------------------------------------------
        # Expiring Soon
        # --------------------------------------------------------

        expiring_queryset = expiring_soon_batches(
            inventory_queryset,
            options["expiry_alert_days"],
            today=today,
        ).order_by("expiry_date")

        expiring_soon_count = (
            expiring_queryset.count()
        )

        # --------------------------------------------------------
        # Already Expired
        # --------------------------------------------------------

        expired_count = (
            inventory_queryset.filter(
                expiry_date__lt=today,
                quantity__gt=0,
            )
            .count()
        )

        context.update(
            {
                "low_stock_count": low_stock_count,
                "out_of_stock_count": out_of_stock_count,
                "expiring_soon_count": (
                    expiring_soon_count
                ),
                "expired_count": expired_count,

                "low_stock_batches": (
                    low_stock_queryset[:5]
                ),
                "expiring_batches": (
                    expiring_queryset[:5]
                ),
                "out_of_stock_batches": (
                    out_of_stock_queryset[:5]
                ),
            }
        )

    # ============================================================
    # MEDICINE DATA
    # ============================================================

    if can_view_medicines:
        context.update(
            {
                "total_medicines": (
                    Medicine.objects.count()
                ),
                "active_medicines": (
                    Medicine.objects.filter(
                        is_active=True
                    ).count()
                ),
            }
        )

    # ============================================================
    # CURRENT BRANCH DISPLAY
    # ============================================================

    if user.is_superuser:
        context["dashboard_branch_name"] = (
            "All Branches"
        )

    elif user.branch:
        context["dashboard_branch_name"] = (
            user.branch.name
        )

    else:
        context["dashboard_branch_name"] = (
            "No Branch Assigned"
        )

    return render(
        request,
        "dashboard.html",
        context,
    )