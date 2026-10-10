
from django.urls import path
from . import views

app_name = "branches"

urlpatterns = [
    path("", views.branch_list, name="list"),
    path("add/", views.branch_create, name="create"),
    path("<int:pk>/edit/", views.branch_edit, name="edit"),
    path(
        "<int:pk>/toggle-status/",
        views.branch_toggle_status,
        name="toggle_status",
    ),
]
