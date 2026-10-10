
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from .models import PurchaseOrderEmail

logger = logging.getLogger(__name__)


def send_purchase_order_email(notification_id):
    """
    Send the supplier's purchase order email.

    Email errors are recorded, without reverting
    the already-confirmed purchase order.
    """

    with transaction.atomic():
        notification = (
            PurchaseOrderEmail.objects
            .select_for_update()
            .select_related("purchase")
            .get(pk=notification_id)
        )

        if notification.status in (
            PurchaseOrderEmail.Status.SENT,
            PurchaseOrderEmail.Status.SENDING,
        ):
            return False

        notification.status = PurchaseOrderEmail.Status.SENDING
        notification.attempts += 1
        notification.last_error = ""
        notification.save(
            update_fields=[
                "status",
                "attempts",
                "last_error",
                "updated_at",
            ]
        )

    try:
        purchase = (
            notification.purchase.__class__.objects
            .select_related("supplier", "branch")
            .prefetch_related("items__medicine")
            .get(pk=notification.purchase_id)
        )

        if purchase.status == purchase.Status.DRAFT:
            raise ValueError("Purchase order is still a draft.")

        if not notification.recipient_email:
            raise ValueError("Supplier has no email address.")

        item_lines = []

        for item in purchase.items.all():
            item_lines.append(
                f"- {item.medicine.name} "
                f"| {item.ordered_packs} packs "
                f"| Rs. {item.purchase_price} per pack "
                f"| Rs. {item.line_total}"
            )

        delivery_date = (
            purchase.expected_delivery_date.strftime("%d %b %Y")
            if purchase.expected_delivery_date
            else "To be confirmed"
        )

        sender_name = purchase.branch.name

        body = "\n".join([
            f"Dear {purchase.supplier.name},",
            "",
            f"{sender_name} would like to place "
            "the following purchase order.",
            "",
            f"Purchase Order: {purchase.purchase_number}",
            f"Purchase Date: {purchase.purchase_date}",
            f"Expected Delivery: {delivery_date}",
            "",
            "ORDER DETAILS",
            "------------------------------",
            *item_lines,
            "------------------------------",
            f"Subtotal: Rs. {purchase.subtotal}",
            f"Discount: Rs. {purchase.discount_amount}",
            f"Tax: Rs. {purchase.tax_amount}",
            f"Total: Rs. {purchase.total_amount}",
            "",
            "Please confirm medicine availability "
            "and the expected delivery date.",
            "",
            "Regards,",
            sender_name,
        ])

        email = EmailMessage(
            subject=(
                f"Purchase Order {purchase.purchase_number}"
                f" - {sender_name}"
            ),
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.recipient_email],
        )

        email.send(fail_silently=False)

    except Exception as exc:
        logger.exception(
            "Purchase order email delivery failed: %s",
            notification_id,
        )

        PurchaseOrderEmail.objects.filter(
            pk=notification_id
        ).update(
            status=PurchaseOrderEmail.Status.FAILED,
            last_error=str(exc)[:2000],
        )
        return False

    PurchaseOrderEmail.objects.filter(
        pk=notification_id
    ).update(
        status=PurchaseOrderEmail.Status.SENT,
        sent_at=timezone.now(),
        last_error="",
    )

    return True
