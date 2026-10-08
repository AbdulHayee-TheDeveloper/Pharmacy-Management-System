from django.urls import path

from . import views


app_name = "sales"


urlpatterns = [
    # ============================================================
    # POS
    # ============================================================

    path(
        "",
        views.pos,
        name="pos",
    ),

    path(
        "search/",
        views.product_search,
        name="product_search",
    ),

    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),

    # ============================================================
    # SALE HISTORY
    # ============================================================

    path(
        "history/",
        views.sale_history,
        name="history",
    ),

    path(
        "history/<int:pk>/",
        views.sale_detail,
        name="detail",
    ),

    # ============================================================
    # RECEIPT
    # ============================================================

    path(
        "history/<int:pk>/receipt/",
        views.sale_receipt,
        name="receipt",
    ),
    path(
    "history/<int:pk>/receive-payment/",
    views.sale_receive_payment,
    name="receive_payment",
),
]