
from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path(
        "",
        views.customer_list,
        name="list",
    ),
    path(
        "add/",
        views.customer_create,
        name="create",
    ),
    path(
        "<int:pk>/",
        views.customer_detail,
        name="detail",
    ),
    path(
        "<int:pk>/edit/",
        views.customer_edit,
        name="edit",
    ),
    path(
    "pos-search/",
    views.customer_pos_search,
    name="pos_search",
),
    path(
        "<int:pk>/toggle-status/",
        views.customer_toggle_status,
        name="toggle_status",
    ),
    path(
    "<int:pk>/link-sale/",
    views.customer_link_sale,
    name="link_sale",
),
]
