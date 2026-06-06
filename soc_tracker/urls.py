from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from alerts import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("alerts/", views.alert_list, name="alert_list"),
    path("alerts/new/", views.alert_create, name="alert_create"),
    path("r/<str:alert_id>/", views.alert_report, name="alert_report"),
    path("alerts/<int:pk>/", views.alert_detail, name="alert_detail"),
    path("alerts/<int:pk>/edit/", views.alert_edit, name="alert_edit"),
    path("alerts/<int:pk>/escalate/", views.alert_escalate, name="alert_escalate"),
    path("alerts/<int:pk>/assign/", views.alert_assign, name="alert_assign"),
    path("alerts/<int:pk>/delete/", views.alert_delete, name="alert_delete"),
    path("elastic/import/", views.elastic_import, name="elastic_import"),
    path("api/webhook/n8n/", views.n8n_webhook, name="n8n_webhook"),
    path("api/webhook/n8n/logs/", views.n8n_log_webhook, name="n8n_log_webhook"),
]
