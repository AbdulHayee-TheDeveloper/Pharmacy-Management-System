from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from inventory.models import InventoryBatch

from .models import Sale, SaleItem


MONEY_PLACES = Decimal("0.01")

SALE_TYPE_PACK = SaleItem.SaleType.PACK
SALE_TYPE_UNIT = SaleItem.SaleType.UNIT

VALID_SALE_TYPES = {
    SALE_TYPE_PACK,
    SALE_TYPE_UNIT,
}


class CheckoutError(Exception):
    pass


def money(value):
    try:
        return Decimal(str(value)).quantize(
            MONEY_PLACES,
            rounding=ROUND_HALF_UP,
        )
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise CheckoutError(
            "Invalid monetary value."
        ) from exc


def calculate_payment_status(
    total_amount,
    paid_amount,
):
    if paid_amount <= Decimal("0.00"):
        return Sale.PaymentStatus.UNPAID

    if paid_amount < total_amount:
        return Sale.PaymentStatus.PARTIAL

    return Sale.PaymentStatus.PAID


@transaction.atomic
def checkout_sale(
    *,
    user,
    branch,
    items,
    payment_method,
    paid_amount=Decimal("0.00"),
    discount_amount=Decimal("0.00"),
    customer_name="",
    customer_phone="",
    notes="",
):
    # ============================================================
    # BASIC VALIDATION
    # ============================================================

    if not isinstance(items, list) or not items:
        raise CheckoutError(
            "Cart is empty."
        )

    valid_payment_methods = {
        choice[0]
        for choice in Sale.PaymentMethod.choices
    }

    if payment_method not in valid_payment_methods:
        raise CheckoutError(
            "Invalid payment method."
        )

    paid_amount = money(
        paid_amount
    )

    discount_amount = money(
        discount_amount
    )

    if paid_amount < Decimal("0.00"):
        raise CheckoutError(
            "Paid amount cannot be negative."
        )

    if discount_amount < Decimal("0.00"):
        raise CheckoutError(
            "Discount cannot be negative."
        )

    # ============================================================
    # NORMALIZE CART ITEMS
    # ============================================================
    #
    # Frontend item:
    #
    # {
    #     "batch_id": 12,
    #     "quantity": 2,
    #     "sale_type": "pack"
    # }
    #
    # OR:
    #
    # {
    #     "batch_id": 12,
    #     "quantity": 3,
    #     "sale_type": "unit"
    # }
    #
    # Price is NEVER accepted from frontend.
    # ============================================================

    requested_items = defaultdict(int)

    for item in items:
        if not isinstance(item, dict):
            raise CheckoutError(
                "Invalid cart item."
            )

        try:
            batch_id = int(
                item["batch_id"]
            )

            quantity = int(
                item["quantity"]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise CheckoutError(
                "Every cart item must contain "
                "a valid batch ID and quantity."
            ) from exc

        sale_type = str(
            item.get(
                "sale_type",
                SALE_TYPE_PACK,
            )
        ).strip().lower()

        if batch_id <= 0:
            raise CheckoutError(
                "Invalid inventory batch."
            )

        if quantity <= 0:
            raise CheckoutError(
                "Item quantity must be greater than zero."
            )

        if sale_type not in VALID_SALE_TYPES:
            raise CheckoutError(
                "Invalid sale type."
            )

        requested_items[
            (
                batch_id,
                sale_type,
            )
        ] += quantity

    # ============================================================
    # GET UNIQUE BATCH IDS
    # ============================================================

    batch_ids = list(
        {
            batch_id
            for batch_id, _sale_type
            in requested_items
        }
    )

    # ============================================================
    # LOCK INVENTORY ROWS
    # ============================================================

    batches = list(
        InventoryBatch.objects
        .select_for_update()
        .select_related(
            "medicine",
            "branch",
        )
        .filter(
            id__in=batch_ids,
            branch=branch,
        )
    )

    batch_map = {
        batch.id: batch
        for batch in batches
    }

    if len(batch_map) != len(batch_ids):
        raise CheckoutError(
            "One or more selected inventory "
            "batches are invalid for this branch."
        )

    # ============================================================
    # VALIDATE + CALCULATE EACH SALE LINE
    # ============================================================

    subtotal = Decimal("0.00")
    tax_amount = Decimal("0.00")

    sale_item_data = []

    today = timezone.localdate()

    # Keep track of total stock deduction per batch.
    #
    # This matters because same batch can now appear as:
    #
    # 1 Pack
    # +
    # 2 Tablets
    #
    # in the same sale.
    stock_deductions = defaultdict(int)

    for (
        batch_id,
        sale_type,
    ), sale_quantity in requested_items.items():

        batch = batch_map[
            batch_id
        ]

        medicine = batch.medicine

        # --------------------------------------------------------
        # STATUS VALIDATION
        # --------------------------------------------------------

        if not medicine.is_active:
            raise CheckoutError(
                f"{medicine.name} is inactive."
            )

        if not batch.is_active:
            raise CheckoutError(
                f"{medicine.name} batch "
                f"{batch.batch_number} is inactive."
            )

        if batch.expiry_date < today:
            raise CheckoutError(
                f"{medicine.name} batch "
                f"{batch.batch_number} is expired."
            )

        # --------------------------------------------------------
        # PACK INFORMATION
        # --------------------------------------------------------

        pack_size = max(
            int(
                medicine.pack_size or 1
            ),
            1,
        )

        unit_label = (
            medicine.get_unit_display()
            or "Unit"
        )

        # --------------------------------------------------------
        # PACK SALE
        # --------------------------------------------------------

        if sale_type == SALE_TYPE_PACK:
            unit_price = money(
                batch.selling_price
            )

            stock_quantity = (
                sale_quantity
                * pack_size
            )

        # --------------------------------------------------------
        # LOOSE UNIT SALE
        # --------------------------------------------------------

        else:
            if not medicine.allow_loose_sale:
                raise CheckoutError(
                    f"{medicine.name} cannot be sold "
                    f"as individual "
                    f"{unit_label.lower()}."
                )

            if pack_size <= 1:
                raise CheckoutError(
                    f"{medicine.name} does not have "
                    f"a separate loose-unit configuration."
                )

            unit_price = money(
                batch.unit_selling_price
            )

            stock_quantity = (
                sale_quantity
            )

        # ========================================================
        # ACCUMULATE TOTAL STOCK DEDUCTION
        # ========================================================

        stock_deductions[
            batch_id
        ] += stock_quantity

        # ========================================================
        # LINE TOTAL
        # ========================================================

        line_subtotal = money(
            unit_price
            * sale_quantity
        )

        tax_rate = Decimal(
            str(
                medicine.tax_rate or 0
            )
        )

        line_tax = money(
            line_subtotal
            * tax_rate
            / Decimal("100")
        )

        line_total = money(
            line_subtotal
            + line_tax
        )

        subtotal += (
            line_subtotal
        )

        tax_amount += (
            line_tax
        )

        sale_item_data.append(
            {
                "batch": batch,

                "sale_type":
                    sale_type,

                "unit_label":
                    unit_label,

                "pack_size":
                    pack_size,

                "sale_quantity":
                    sale_quantity,

                "stock_quantity":
                    stock_quantity,

                "unit_price":
                    unit_price,

                "tax_amount":
                    line_tax,

                "line_total":
                    line_total,
            }
        )

    # ============================================================
    # FINAL STOCK VALIDATION
    # ============================================================
    #
    # Validate AFTER combining pack + unit deductions.
    #
    # Example:
    #
    # Stock = 12 tablets
    #
    # 1 pack of 10
    # +
    # 3 tablets
    #
    # Total deduction = 13
    #
    # Must fail.
    # ============================================================

    for batch_id, total_stock_quantity in stock_deductions.items():
        batch = batch_map[
            batch_id
        ]

        if total_stock_quantity > batch.quantity:
            raise CheckoutError(
                f"Insufficient stock for "
                f"{batch.medicine.name}. "
                f"Available: "
                f"{batch.stock_display}."
            )

    # ============================================================
    # SALE TOTALS
    # ============================================================

    subtotal = money(
        subtotal
    )

    tax_amount = money(
        tax_amount
    )

    gross_total = money(
        subtotal
        + tax_amount
    )

    if discount_amount > gross_total:
        raise CheckoutError(
            "Discount cannot exceed sale total."
        )

    total_amount = money(
        gross_total
        - discount_amount
    )

    payment_status = (
        calculate_payment_status(
            total_amount,
            paid_amount,
        )
    )

    change_amount = Decimal(
        "0.00"
    )

    if paid_amount > total_amount:
        change_amount = money(
            paid_amount
            - total_amount
        )

    # ============================================================
    # CREATE SALE
    # ============================================================

    sale = Sale.objects.create(
        branch=branch,
        cashier=user,

        customer_name=str(
            customer_name or ""
        ).strip(),

        customer_phone=str(
            customer_phone or ""
        ).strip(),

        subtotal=subtotal,

        discount_amount=(
            discount_amount
        ),

        tax_amount=(
            tax_amount
        ),

        total_amount=(
            total_amount
        ),

        paid_amount=(
            paid_amount
        ),

        change_amount=(
            change_amount
        ),

        payment_method=(
            payment_method
        ),

        payment_status=(
            payment_status
        ),

        status=(
            Sale.Status.COMPLETED
        ),

        notes=str(
            notes or ""
        ).strip(),

        completed_at=(
            timezone.now()
        ),
    )

    # ============================================================
    # CREATE SALE ITEMS
    # ============================================================

    sale_items = []

    for item in sale_item_data:
        batch = item[
            "batch"
        ]

        sale_items.append(
            SaleItem(
                sale=sale,

                medicine=(
                    batch.medicine
                ),

                inventory_batch=(
                    batch
                ),

                medicine_name=(
                    batch.medicine.name
                ),

                batch_number=(
                    batch.batch_number
                ),

                sale_type=(
                    item[
                        "sale_type"
                    ]
                ),

                unit_label=(
                    item[
                        "unit_label"
                    ]
                ),

                pack_size=(
                    item[
                        "pack_size"
                    ]
                ),

                quantity=(
                    item[
                        "sale_quantity"
                    ]
                ),

                stock_quantity=(
                    item[
                        "stock_quantity"
                    ]
                ),

                unit_price=(
                    item[
                        "unit_price"
                    ]
                ),

                discount_amount=(
                    Decimal("0.00")
                ),

                tax_amount=(
                    item[
                        "tax_amount"
                    ]
                ),

                line_total=(
                    item[
                        "line_total"
                    ]
                ),
            )
        )

    SaleItem.objects.bulk_create(
        sale_items
    )

    # ============================================================
    # DEDUCT STOCK
    # ============================================================

    now = timezone.now()

    for batch_id, deduction in stock_deductions.items():
        batch = batch_map[
            batch_id
        ]

        batch.quantity -= (
            deduction
        )

        batch.updated_at = now

    InventoryBatch.objects.bulk_update(
        batches,
        [
            "quantity",
            "updated_at",
        ],
    )

    return sale