from django.urls import path
from . import views

app_name = "medicines"

urlpatterns = [
    path("", views.medicine_list, name="list"),
    path("add/", views.medicine_create, name="create"),
    path("<int:pk>/", views.medicine_detail, name="detail"),
    path("<int:pk>/edit/", views.medicine_update, name="update"),
    path("<int:pk>/delete/",views.medicine_delete,name="delete",),
    path("<int:pk>/toggle-status/", views.medicine_toggle_status, name="toggle_status"),
]