
from django.urls import path

from . import views


app_name = "medicines"


urlpatterns = [

    # ============================================
    # MEDICINES LIST
    # ============================================

    path(
        "",
        views.medicine_list,
        name="list",
    ),

    # ============================================
    # ADD MEDICINE
    # Uses existing Inventory creation workflow.
    # ============================================

    path(
        "add/",
        views.medicine_create,
        name="create",
    ),

    # ============================================
    # MEDICINE DETAIL
    # ============================================

    path(
        "<int:pk>/",
        views.medicine_detail,
        name="detail",
    ),

    # ============================================
    # EDIT MEDICINE
    # ============================================

    path(
        "<int:pk>/edit/",
        views.medicine_edit,
        name="edit",
    ),
    

    path(
        "categories/",
        views.category_list,
        name="categories",
    ),

    path(
        "categories/add/",
        views.category_create,
        name="category_create",
    ),

    path(
        "categories/<int:pk>/edit/",
        views.category_edit,
        name="category_edit",
    ),

    path(
        "categories/<int:pk>/toggle-status/",
        views.category_toggle_status,
        name="category_toggle_status",
    ),

]
