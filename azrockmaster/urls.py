from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import initial_admin_setup
from core import customer_views

urlpatterns = [
    path("initial-admin-setup/", initial_admin_setup, name="initial-admin-setup"),
    path("customer/", customer_views.customer_portal, name="customer-portal"),
    path("customer/register/", customer_views.customer_register, name="customer-register"),
    path("customer/order/", customer_views.customer_order, name="customer-order"),
    path("customer/invoice/<int:pk>/", customer_views.customer_invoice, name="customer-invoice"),
    path("customer/invoice/<int:pk>/receipt/", customer_views.customer_upload_receipt, name="customer-upload-receipt"),
    path("staff/payment-submissions/", customer_views.payment_submissions, name="payment-submissions"),
    path("staff/payment-submissions/<int:pk>/<str:decision>/", customer_views.review_payment_submission, name="review-payment-submission"),
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("core.urls")),
]
