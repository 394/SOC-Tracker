from django.contrib import admin

from .models import Alert, AlertEvent, UserProfile


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("alert_id", "title", "severity", "status", "source", "analyst", "assigned_to", "assigned_by", "created_at")
    list_filter = ("severity", "status", "source")
    search_fields = ("alert_id", "title", "description", "asset", "analyst")


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ("alert", "event_type", "actor", "assigned_to", "source", "created_at")
    list_filter = ("event_type", "source")
    search_fields = ("alert__alert_id", "message")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
