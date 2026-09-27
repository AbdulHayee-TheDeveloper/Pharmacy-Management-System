from django.urls import path

from . import views


app_name = "inventory"

urlpatterns = [
    path("", views.inventory_list, name="list"),
    path(
        "search-medicines/",
        views.search_medicines,
        name="search_medicines",
    ),
    path("add/", views.inventory_create, name="create"),
    path("<int:pk>/", views.inventory_detail, name="detail"),
]