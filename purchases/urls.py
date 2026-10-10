
from django.urls import path
from .views import purchase_retry_email
from . import views


app_name = "purchases"

urlpatterns = [
    path(
        "",
        views.purchase_list,
        name="list",
    ),
    path(
        "add/",
        views.purchase_create,
        name="create",
    ),
    path(
        "<int:pk>/edit/",
        views.purchase_edit,
        name="edit",
    ),
    path(
        "<int:pk>/",
        views.purchase_detail,
        name="detail",
    ),
    path(
    "<int:pk>/confirm/",
    views.purchase_confirm,
    name="confirm",
),
    path(
        "<int:pk>/receive/",
        views.purchase_receive,
        name="receive",
    ),
    path(
    "<int:pk>/retry-email/",
    purchase_retry_email,
    name="retry_email",
),
]
