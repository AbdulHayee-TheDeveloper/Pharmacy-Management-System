from django.urls import path
from . import views

app_name = "core_settings"

urlpatterns = [
    path(
        "pharmacy/",
        views.pharmacy_settings,
        name="pharmacy_settings",
    ),
]