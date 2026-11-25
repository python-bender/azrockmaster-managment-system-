from django.urls import path
from . import views
urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.dashboard, name="dashboard"),
    path("customers/", views.customers, name="customers"),
    path("customers/new/", views.customer_create, name="customer-create"),
    path("suppliers/", views.suppliers, name="suppliers"),
    path("suppliers/new/", views.supplier_create, name="supplier-create"),
    path("products/", views.products, name="products"),
    path("products/new/", views.product_create, name="product-create"),
    path("orders/", views.orders, name="orders"),
    path("orders/new/", views.order_create, name="order-create"),
    path("expenses/", views.expenses, name="expenses"),
    path("expenses/new/", views.expense_create, name="expense-create"),
    path("expenses/<int:pk>/<str:decision>/", views.expense_decision, name="expense-decision"),
    path("fleet/", views.fleet, name="fleet"),
    path("fleet/trucks/new/", views.truck_create, name="truck-create"),
    path("fleet/drivers/new/", views.driver_create, name="driver-create"),
]
