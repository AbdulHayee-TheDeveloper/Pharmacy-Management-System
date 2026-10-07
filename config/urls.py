from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("medicines/", include("medicines.urls")),
    path( "inventory/", include("inventory.urls"), ),
    path("sales/",include("sales.urls"),),
]