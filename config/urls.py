from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("medicines/", include("medicines.urls")),
    path( "inventory/", include("inventory.urls"), ),
    path("sales/",include("sales.urls"),),
    path("suppliers/", include("suppliers.urls")),
    path("purchases/",include("purchases.urls"),),
    path("customers/", include("customers.urls")),
    path("reports/", include("reports.urls")),
    path("settings/",include("core_settings.urls"),),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )