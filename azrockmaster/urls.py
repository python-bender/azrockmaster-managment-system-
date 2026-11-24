from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import initial_admin_setup

urlpatterns = [
    path("initial-admin-setup/", initial_admin_setup, name="initial-admin-setup"),
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("core.urls")),
]
