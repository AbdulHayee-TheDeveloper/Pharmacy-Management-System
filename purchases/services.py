
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from inventory.models import InventoryBatch

from .models import (
    Purchase,
    PurchaseItem,
    PurchaseReceipt,
    PurchaseReceiptItem,
)


class StockReceivingError(Exception):
    """
    A business-rule error during stock receiving.
    """


def _positive_integer(value, label):
    """
    Accept whole positive numbers only.
    """
    if isinstance(value, bool):
        raise StockReceivingError(
            f"{label} must be a positive whole number."
        )

    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        raise StockReceivingError(
            f"{label} must be a positive whole number."
        )

    if str(value).strip() != str(number) and not (
        isinstance(value, int)
    ):
        raise StockReceivingError(
            f"{label} must be a positive whole number."
        )

    if number < 1:
        raise StockReceivingError(
            f"{label} must be greater than zero."
        )

    return number


def _expiry_date(value):
    """
    Accept a Python date or ISO date string: YYYY-MM-DD.
    """
    if isinstance(value, date) and not isinstance(
        value, __import__("datetime").datetime
    ):
        expiry = value

    elif isinstance(value, str):
        try:
            expiry = date.fromisoformat(value)
        except ValueError:
            raise StockReceivingError(
                "Expiry date must use YYYY-MM-DD format."
            )

    else:
        raise StockReceivingError(
            "A valid expiry date is required."
        )

    if expiry <= timezone.localdate():
        raise StockReceivingError(
            "Expired medicines cannot be received."
        )

    return expiry


@transaction.atomic
def receive_purchase_stock(
    *,
    purchase_id,
    received_by,
    items,
    authorized_branches,
    supplier_delivery_note="",
    notes="",
):
    """
    Receive medicine stock against an existing purchase.

    Parameters
    ----------
    purchase_id:
        ID of the purchase order.

    received_by:
        Authenticated User performing the receiving.

    items:
        List of dictionaries containing:
            purchase_item_id
            batch_number
            expiry_date
            received_packs

    authorized_branches:
        Branch queryset already restricted to the
        current user by the calling view.

    supplier_delivery_note:
        Optional supplier delivery reference.

    notes:
        Optional receiving remarks.

    Returns
    -------
    PurchaseReceipt:
        The saved receipt with its receipt items.

    IMPORTANT:
    This function performs the actual inventory update.
    Only call it after explicit user confirmation.
    """

    # ========================================================
    # 1. VERIFY USER
    # ========================================================

    if (
        received_by is None
        or not received_by.is_authenticated
        or not received_by.is_active
    ):
        raise StockReceivingError(
            "An authenticated active user is required."
        )

    if not received_by.has_perm(
        "purchases.change_purchase"
    ):
        raise StockReceivingError(
            "You do not have permission to receive purchases."
        )

    if authorized_branches is None:
        raise StockReceivingError(
            "Authorized branches are required."
        )

    if not isinstance(items, (list, tuple)) or not items:
        raise StockReceivingError(
            "Add at least one medicine to receive."
        )

    # ========================================================
    # 2. LOCK THE PURCHASE ORDER
    # ========================================================

    try:
        purchase = (
            Purchase.objects
            .select_for_update()
            .select_related("supplier", "branch")
            .get(pk=purchase_id)
        )
    except Purchase.DoesNotExist:
        raise StockReceivingError(
            "Purchase order was not found."
        )

    # Branch authorization is enforced again here.
    if not authorized_branches.filter(
        pk=purchase.branch_id
    ).exists():
        raise StockReceivingError(
            "You cannot receive stock for this branch."
        )

    allowed_statuses = {
        Purchase.Status.ORDERED,
        Purchase.Status.PARTIALLY_RECEIVED,
    }

    if purchase.status not in allowed_statuses:
        raise StockReceivingError(
            "Only Ordered or Partially Received "
            "purchases can receive stock."
        )

    # ========================================================
    # 3. LOAD PURCHASE ITEMS
    # ========================================================

    purchase_items = list(
        PurchaseItem.objects
        .select_for_update()
        .select_related("medicine")
        .filter(purchase=purchase)
        .order_by("pk")
    )

    if not purchase_items:
        raise StockReceivingError(
            "The purchase has no medicine items."
        )

    item_lookup = {
        item.pk: item
        for item in purchase_items
    }

    # ========================================================
    # 4. VALIDATE RECEIVING INPUT
    # ========================================================

    prepared_items = []
    receiving_totals = {}
    seen_batches = set()

    for index, entry in enumerate(items, start=1):

        if not isinstance(entry, dict):
            raise StockReceivingError(
                f"Receiving row {index} is invalid."
            )

        purchase_item_id = _positive_integer(
            entry.get("purchase_item_id"),
            f"Row {index}: purchase item ID",
        )

        purchase_item = item_lookup.get(
            purchase_item_id
        )

        if purchase_item is None:
            raise StockReceivingError(
                f"Row {index}: medicine does not "
                "belong to this purchase."
            )

        batch_number = str(
            entry.get("batch_number") or ""
        ).strip()

        if not batch_number:
            raise StockReceivingError(
                f"Row {index}: batch number is required."
            )

        if len(batch_number) > 100:
            raise StockReceivingError(
                f"Row {index}: batch number is too long."
            )

        expiry = _expiry_date(
            entry.get("expiry_date")
        )

        received_packs = _positive_integer(
            entry.get("received_packs"),
            f"Row {index}: received packs",
        )

        if purchase_item.pack_size < 1:
            raise StockReceivingError(
                f"Row {index}: invalid medicine pack size."
            )

        if (
            purchase_item.purchase_price < Decimal("0.00")
            or purchase_item.selling_price < Decimal("0.00")
        ):
            raise StockReceivingError(
                f"Row {index}: invalid purchase pricing."
            )

        # Prevent repeating the same medicine + batch
        # within one receiving transaction.
        batch_key = (
            purchase_item.medicine_id,
            batch_number,
        )

        if batch_key in seen_batches:
            raise StockReceivingError(
                f"Row {index}: duplicate medicine "
                "and batch number."
            )

        seen_batches.add(batch_key)

        receiving_totals[purchase_item_id] = (
            receiving_totals.get(purchase_item_id, 0)
            + received_packs
        )

        prepared_items.append({
            "purchase_item": purchase_item,
            "batch_number": batch_number,
            "expiry_date": expiry,
            "received_packs": received_packs,
            "received_units": (
                received_packs * purchase_item.pack_size
            ),
        })

    # ========================================================
    # 5. VALIDATE REMAINING ORDER QUANTITIES
    # ========================================================

    for purchase_item_id, incoming_packs in (
        receiving_totals.items()
    ):
        purchase_item = item_lookup[
            purchase_item_id
        ]

        remaining_packs = (
            purchase_item.ordered_packs
            - purchase_item.received_packs
        )

        if incoming_packs > remaining_packs:
            raise StockReceivingError(
                f"{purchase_item.medicine.name}: "
                f"only {remaining_packs} pack(s) remain "
                "to be received."
            )

    # ========================================================
    # 6. CREATE RECEIPT HEADER
    # ========================================================

    receipt = PurchaseReceipt(
        purchase=purchase,
        received_by=received_by,
        supplier_delivery_note=(
            supplier_delivery_note or ""
        ).strip(),
        notes=(notes or "").strip(),
    )

    try:
        receipt.full_clean()
    except ValidationError as exc:
        raise StockReceivingError(
            "; ".join(exc.messages)
        )

    receipt.save()

    # ========================================================
    # 7. UPDATE INVENTORY + CREATE RECEIPT ITEMS
    # ========================================================

    # Consistent ordering makes concurrent batch
    # locking more predictable.
    prepared_items.sort(
        key=lambda entry: (
            entry["purchase_item"].medicine_id,
            entry["batch_number"],
        )
    )

    for entry in prepared_items:

        purchase_item = entry["purchase_item"]

        medicine = purchase_item.medicine

        batch_number = entry["batch_number"]
        expiry = entry["expiry_date"]

        received_packs = entry["received_packs"]
        received_units = entry["received_units"]

        # Batch identity:
        # medicine + branch + batch_number
        batch_lookup = {
            "medicine": medicine,
            "branch": purchase.branch,
            "batch_number": batch_number,
        }

        # get_or_create uses the existing model's
        # unique constraint to handle concurrent inserts.
        inventory_batch, created = (
            InventoryBatch.objects.get_or_create(
                **batch_lookup,
                defaults={
                    "expiry_date": expiry,
                    "quantity": 0,
                    "purchase_price": (
                        purchase_item.purchase_price
                    ),
                    "selling_price": (
                        purchase_item.selling_price
                    ),
                    "is_active": True,
                },
            )
        )

        # Lock the matching row before reading/changing
        # its stock quantity.
        inventory_batch = (
            InventoryBatch.objects
            .select_for_update()
            .get(pk=inventory_batch.pk)
        )

        # Never silently mix batches with different
        # expiry dates or prices.
        if inventory_batch.expiry_date != expiry:
            raise StockReceivingError(
                f"{medicine.name}, batch {batch_number}: "
                "expiry date does not match existing stock."
            )

        if (
            inventory_batch.purchase_price
            != purchase_item.purchase_price
            or inventory_batch.selling_price
            != purchase_item.selling_price
        ):
            raise StockReceivingError(
                f"{medicine.name}, batch {batch_number}: "
                "batch prices differ from existing inventory."
            )

        if not inventory_batch.is_active:
            raise StockReceivingError(
                f"{medicine.name}, batch {batch_number}: "
                "inactive inventory batch cannot be received."
            )

        # Smallest unit quantity:
        # received packs * original pack size.
        inventory_batch.quantity += received_units

        inventory_batch.full_clean()

        inventory_batch.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        # Store permanent receiving history.
        receipt_item = PurchaseReceiptItem(
            receipt=receipt,
            purchase_item=purchase_item,
            batch_number=batch_number,
            expiry_date=expiry,
            received_packs=received_packs,
            pack_size=purchase_item.pack_size,
            purchase_price=purchase_item.purchase_price,
            selling_price=purchase_item.selling_price,
            inventory_batch=inventory_batch,
        )

        try:
            receipt_item.full_clean()
        except ValidationError as exc:
            raise StockReceivingError(
                "; ".join(exc.messages)
            )

        receipt_item.save()

    # ========================================================
    # 8. UPDATE PURCHASE ITEM RECEIVED COUNTERS
    # ========================================================

    for purchase_item_id, incoming_packs in (
        receiving_totals.items()
    ):
        purchase_item = item_lookup[
            purchase_item_id
        ]

        purchase_item.received_packs += incoming_packs

        purchase_item.save(
            update_fields=[
                "received_packs",
                "updated_at",
            ]
        )

    # ========================================================
    # 9. CALCULATE PURCHASE STATUS
    # ========================================================

    all_received = all(
        item.received_packs == item.ordered_packs
        for item in purchase_items
    )

    if all_received:
        purchase.status = Purchase.Status.RECEIVED

    else:
        purchase.status = (
            Purchase.Status.PARTIALLY_RECEIVED
        )

    purchase.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

   
    return receipt
