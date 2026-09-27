from django.urls import path

from . import views


app_name = "medicines"

urlpatterns = [
    path("", views.medicine_list, name="list"),
    path("<int:pk>/", views.medicine_detail, name="detail"),
]