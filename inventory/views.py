from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_permission_required
from medicines.models import Medicine

from .forms import (
    InventoryBatchEditForm,
    InventoryEntryForm, StockAdjustmentForm
)
from .models import InventoryBatch, StockAdjustment


@login_required
@role_permission_required("inventory.view_inventorybatch")
def inventory_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    batches = InventoryBatch.objects.select_related(
        "medicine",
        "branch",
    )

    if query:
        batches = batches.filter(
            Q(medicine__name__icontains=query)
            | Q(medicine__generic_name__icontains=query)
            | Q(batch_number__icontains=query)
            | Q(medicine__barcode__icontains=query)
            | Q(medicine__sku__icontains=query)
        )

    if status == "active":
        batches = batches.filter(
            is_active=True
        )

    elif status == "inactive":
        batches = batches.filter(
            is_active=False
        )

    elif status == "out_of_stock":
        batches = batches.filter(
            quantity=0
        )

    elif status == "low_stock":
        batches = batches.filter(
            quantity__gt=0,
            quantity__lte=F(
                "medicine__minimum_stock_level"
            ),
        )

    context = {
        "batches": batches,
        "query": query,
        "selected_status": status,
        "total_batches": InventoryBatch.objects.count(),
        "active_batches": InventoryBatch.objects.filter(
            is_active=True
        ).count(),
        "out_of_stock": InventoryBatch.objects.filter(
            quantity=0
        ).count(),
    }

    return render(
        request,
        "inventory/list.html",
        context,
    )


@login_required
@role_permission_required("inventory.view_inventorybatch")
def inventory_detail(request, pk):
    batch = get_object_or_404(
        InventoryBatch.objects.select_related(
            "medicine",
            "branch",
        ),
        pk=pk,
    )

    adjustments = (
        batch.adjustments
        .select_related("created_by")
        .all()[:20]
    )

    return render(
        request,
        "inventory/detail.html",
        {
            "batch": batch,
            "adjustments": adjustments,
        },
    )


@login_required
@role_permission_required("inventory.change_inventorybatch")
def inventory_edit(request, pk):
    batch = get_object_or_404(
        InventoryBatch.objects.select_related(
            "medicine",
            "branch",
        ),
        pk=pk,
    )

    if request.method == "POST":
        form = InventoryBatchEditForm(
            request.POST,
            instance=batch,
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    batch = form.save()

            except IntegrityError:
                form.add_error(
                    "batch_number",
                    (
                        "This batch number already exists "
                        "for this medicine and branch."
                    ),
                )

            else:
                messages.success(
                    request,
                    (
                        f"Batch {batch.batch_number} "
                        f"updated successfully."
                    ),
                )

                return redirect(
                    "inventory:detail",
                    pk=batch.pk,
                )

    else:
        form = InventoryBatchEditForm(
            instance=batch,
        )

    return render(
        request,
        "inventory/edit.html",
        {
            "form": form,
            "batch": batch,
            "page_title": "Edit Inventory Batch",
        },
    )


@login_required
@role_permission_required("inventory.view_inventorybatch")
def search_medicines(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse(
            {
                "results": [],
            }
        )

    medicines = (
        Medicine.objects
        .filter(is_active=True)
        .filter(
            Q(name__icontains=query)
            | Q(generic_name__icontains=query)
            | Q(barcode__icontains=query)
            | Q(sku__icontains=query)
        )
        .select_related("category")
        .order_by("name")[:10]
    )

    results = [
        {
            "id": medicine.pk,
            "name": medicine.name,
            "generic_name": medicine.generic_name,
            "strength": medicine.strength,
            "dosage_form": (
                medicine.get_dosage_form_display()
            ),
            "unit": medicine.unit,
            "unit_label": medicine.get_unit_display(),
            "pack_size": medicine.pack_size,
            "allow_loose_sale": (
                medicine.allow_loose_sale
            ),
            "barcode": medicine.barcode or "",
            "sku": medicine.sku or "",
            "category": medicine.category.name,
        }
        for medicine in medicines
    ]

    return JsonResponse(
        {
            "results": results,
        }
    )


@login_required
@role_permission_required("inventory.add_inventorybatch")
def inventory_create(request):
    form = InventoryEntryForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        entry_type = data["entry_type"]

        try:
            with transaction.atomic():

                # ================================================
                # CREATE / RESOLVE MEDICINE
                # ================================================

                if entry_type == "new":
                    medicine = Medicine.objects.create(
                        name=data["name"],
                        generic_name=data.get(
                            "generic_name",
                            "",
                        ),
                        category=data["category"],
                        manufacturer=data.get(
                            "manufacturer",
                            "",
                        ),
                        country_of_origin=data.get(
                            "country_of_origin",
                            "",
                        ),
                        dosage_form=data["dosage_form"],
                        strength=data.get(
                            "strength",
                            "",
                        ),
                        unit=data["unit"],
                        pack_size=(
                            data.get("pack_size") or 1
                        ),
                        allow_loose_sale=data.get(
                            "allow_loose_sale",
                            False,
                        ),
                        barcode=data.get("barcode"),
                        sku=data.get("sku"),
                        purchase_price=data[
                            "purchase_price"
                        ],
                        selling_price=data[
                            "selling_price"
                        ],
                        minimum_stock_level=(
                            data.get(
                                "minimum_stock_level"
                            )
                            if data.get(
                                "minimum_stock_level"
                            ) is not None
                            else 10
                        ),
                        reorder_level=(
                            data.get("reorder_level")
                            if data.get(
                                "reorder_level"
                            ) is not None
                            else 20
                        ),
                        prescription_required=data.get(
                            "prescription_required",
                            False,
                        ),
                        controlled_medicine=data.get(
                            "controlled_medicine",
                            False,
                        ),
                        storage_condition=data.get(
                            "storage_condition",
                            "",
                        ),
                        description=data.get(
                            "description",
                            "",
                        ),
                        is_active=True,
                    )

                else:
                    medicine = data["medicine"]

                # ================================================
                # PACKS -> SMALLEST STOCK UNITS
                # ================================================

                packs_received = data["quantity"]

                pack_size = max(
                    medicine.pack_size,
                    1,
                )

                stock_quantity = (
                    packs_received * pack_size
                )

                # ================================================
                # CREATE INVENTORY BATCH
                # ================================================

                InventoryBatch.objects.create(
                    medicine=medicine,
                    branch=data["branch"],
                    batch_number=data[
                        "batch_number"
                    ],
                    expiry_date=data[
                        "expiry_date"
                    ],
                    quantity=stock_quantity,
                    purchase_price=data[
                        "purchase_price"
                    ],
                    selling_price=data[
                        "selling_price"
                    ],
                    is_active=data.get(
                        "is_active",
                        True,
                    ),
                )

        except IntegrityError:
            form.add_error(
                "batch_number",
                (
                    "This batch number already exists "
                    "for the selected medicine and branch."
                ),
            )

        else:
            if entry_type == "new":
                messages.success(
                    request,
                    (
                        f"{medicine.name} and its first "
                        f"inventory batch were added "
                        f"successfully. "
                        f"{packs_received} pack(s) = "
                        f"{stock_quantity} "
                        f"{medicine.get_unit_display()}"
                        f"(s)."
                    ),
                )

            else:
                messages.success(
                    request,
                    (
                        f"Inventory batch "
                        f"{data['batch_number']} was added "
                        f"successfully. "
                        f"{packs_received} pack(s) = "
                        f"{stock_quantity} "
                        f"{medicine.get_unit_display()}"
                        f"(s)."
                    ),
                )

            return redirect(
                "inventory:list"
            )

    return render(
        request,
        "inventory/form.html",
        {
            "form": form,
            "page_title": "Add Medicine / Stock",
            "submit_text": "Save Inventory",
        },
    )
@login_required
@role_permission_required("inventory.add_stockadjustment")
def stock_adjustment_create(request, pk):
    batch = get_object_or_404(
        InventoryBatch.objects.select_related(
            "medicine",
            "branch",
        ),
        pk=pk,
    )

    form = StockAdjustmentForm(
        request.POST or None,
        batch=batch,
    )

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data

        adjustment_type = data[
            "adjustment_type"
        ]

        quantity = data[
            "quantity"
        ]

        reason = data[
            "reason"
        ].strip()

        try:
            with transaction.atomic():

                locked_batch = (
                    InventoryBatch.objects
                    .select_for_update()
                    .select_related(
                        "medicine",
                        "branch",
                    )
                    .get(pk=batch.pk)
                )

                previous_quantity = (
                    locked_batch.quantity
                )

                if (
                    adjustment_type
                    == StockAdjustment.AdjustmentType.REMOVE
                ):
                    if quantity > previous_quantity:
                        form.add_error(
                            "quantity",
                            (
                                "Stock changed while this page "
                                "was open. The requested quantity "
                                "is no longer available."
                            ),
                        )

                        raise ValueError(
                            "Insufficient stock"
                        )

                    resulting_quantity = (
                        previous_quantity - quantity
                    )

                else:
                    if locked_batch.is_expired:
                        form.add_error(
                            "adjustment_type",
                            (
                                "Stock cannot be added "
                                "to an expired batch."
                            ),
                        )

                        raise ValueError(
                            "Expired batch"
                        )

                    resulting_quantity = (
                        previous_quantity + quantity
                    )

                locked_batch.quantity = (
                    resulting_quantity
                )

                locked_batch.save(
                    update_fields=[
                        "quantity",
                        "updated_at",
                    ]
                )

                StockAdjustment.objects.create(
                    batch=locked_batch,
                    adjustment_type=adjustment_type,
                    quantity=quantity,
                    previous_quantity=previous_quantity,
                    resulting_quantity=resulting_quantity,
                    reason=reason,
                    created_by=request.user,
                )

        except ValueError:
            pass

        else:
            direction = (
                "added to"
                if adjustment_type
                == StockAdjustment.AdjustmentType.ADD
                else "removed from"
            )

            messages.success(
                request,
                (
                    f"{quantity} "
                    f"{batch.medicine.unit_label}(s) "
                    f"{direction} batch "
                    f"{batch.batch_number}. "
                    f"New stock: "
                    f"{resulting_quantity}."
                ),
            )

            return redirect(
                "inventory:detail",
                pk=batch.pk,
            )

    return render(
        request,
        "inventory/adjust.html",
        {
            "form": form,
            "batch": batch,
            "page_title": "Adjust Stock",
        },
    )