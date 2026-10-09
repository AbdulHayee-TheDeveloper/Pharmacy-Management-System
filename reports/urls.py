
from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [

    # Analytics dashboard
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "data/",
        views.dashboard_data,
        name="dashboard_data",
    ),

    # Existing JSON APIs
    path(
        "sales/",
        views.sales_report,
        name="sales",
    ),

    path(
        "purchases/",
        views.purchase_report,
        name="purchases",
    ),

    path(
        "inventory/",
        views.inventory_report,
        name="inventory",
    ),

    path(
        "profit/",
        views.profit_report,
        name="profit",
    ),

    # Existing CSV exports
    path(
        "export/sales/",
        views.export_sales_csv,
        name="export_sales",
    ),

    path(
        "export/purchases/",
        views.export_purchases_csv,
        name="export_purchases",
    ),

    path(
        "export/inventory/",
        views.export_inventory_csv,
        name="export_inventory",
    ),

    
    path(
        "view/<str:report_type>/",
        views.detailed_report_page,
        name="detail_page",
    ),

    
    path(
        "pdf/<str:report_type>/",
        views.export_report_pdf,
        name="export_pdf",
    ),
    

path(
    "rows/sales/",
    views.sales_report_rows,
    name="sales_rows",
),

path(
    "rows/purchases/",
    views.purchase_report_rows,
    name="purchases_rows",
),

path(
    "rows/inventory/",
    views.inventory_report_rows,
    name="inventory_rows",
),
]
