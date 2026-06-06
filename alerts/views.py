import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .elastic import parse_elastic_alerts, record_to_alert, records_from
from .forms import AlertForm, AssignAlertForm, ElasticJsonForm
from .models import Alert, AlertEvent
from .permissions import assignable_roles_for, can_assign_alert, can_create_alert, can_delete_alert, can_edit_alert, can_escalate_alert


@login_required
def dashboard(request):
    alerts = filtered_alerts(request)
    context = {
        "alerts": alerts[:80],
        "counts": {
            "total": alerts.count(),
            "open": alerts.exclude(status=Alert.Status.CLOSED).count(),
            "critical": alerts.filter(severity=Alert.Severity.CRITICAL).count(),
            "escalated": alerts.filter(status=Alert.Status.ESCALATED).count(),
        },
        "status_counts": alerts.values("status").annotate(count=Count("id")),
    }
    return render(request, "alerts/dashboard.html", context)


@login_required
def alert_list(request):
    return render(request, "alerts/list.html", {"alerts": filtered_alerts(request)})


@login_required
def alert_detail(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    assign_roles = assignable_roles_for(request.user)
    return render(request, "alerts/detail.html", {
        "alert": alert,
        "can_edit": can_edit_alert(request.user, alert),
        "can_escalate": can_escalate_alert(request.user) and alert.status != Alert.Status.ESCALATED,
        "can_assign": can_assign_alert(request.user),
        "assign_form": AssignAlertForm(assignable_roles=assign_roles) if assign_roles else None,
    })


@login_required
def alert_report(request, alert_id):
    alert = get_object_or_404(Alert, alert_id=alert_id)
    return redirect(alert)


@login_required
def alert_create(request):
    if not can_create_alert(request.user):
        raise PermissionDenied
    form = AlertForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        alert = form.save(commit=False)
        alert.created_by = request.user
        alert.updated_by = request.user
        if alert.status == Alert.Status.ESCALATED:
            alert.escalated_by = request.user
        alert.save()
        AlertEvent.objects.create(alert=alert, event_type=AlertEvent.EventType.CREATED, actor=request.user, message=f"{request.user.username} created {alert.alert_id}.")
        messages.success(request, f"Created {alert.alert_id}.")
        return redirect(alert)
    return render(request, "alerts/form.html", {"form": form, "title": "New alert"})


@login_required
def alert_edit(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    if not can_edit_alert(request.user, alert):
        raise PermissionDenied
    old_status = alert.status
    form = AlertForm(request.POST or None, instance=alert)
    if request.method == "POST" and form.is_valid():
        alert = form.save(commit=False)
        alert.updated_by = request.user
        if old_status != Alert.Status.ESCALATED and alert.status == Alert.Status.ESCALATED:
            alert.escalated_by = request.user
        alert.save()
        AlertEvent.objects.create(alert=alert, event_type=AlertEvent.EventType.UPDATED, actor=request.user, message=f"{request.user.username} updated {alert.alert_id}.")
        messages.success(request, f"Updated {alert.alert_id}.")
        return redirect(alert)
    return render(request, "alerts/form.html", {"form": form, "title": f"Edit {alert.alert_id}", "alert": alert})


@login_required
@require_POST
def alert_escalate(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    if not can_escalate_alert(request.user):
        raise PermissionDenied
    alert.status = Alert.Status.ESCALATED
    alert.escalated_by = request.user
    alert.updated_by = request.user
    alert.save(update_fields=["status", "escalated_by", "updated_by", "updated_at"])
    AlertEvent.objects.create(alert=alert, event_type=AlertEvent.EventType.ESCALATED, actor=request.user, message=f"{request.user.username} escalated this alert.")
    messages.success(request, f"Escalated {alert.alert_id}.")
    return redirect(alert)


@login_required
@require_POST
def alert_assign(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    assign_roles = assignable_roles_for(request.user)
    if not assign_roles:
        raise PermissionDenied
    form = AssignAlertForm(request.POST, assignable_roles=assign_roles)
    if not form.is_valid():
        messages.error(request, "Select a valid analyst for your role.")
        return redirect(alert)
    assigned_to = form.cleaned_data["assigned_to"]
    previous_assignee = alert.assigned_to
    alert.assigned_to = assigned_to
    alert.assigned_by = request.user
    alert.analyst = assigned_to.username
    alert.status = Alert.Status.INVESTIGATING
    alert.updated_by = request.user
    alert.save(update_fields=["assigned_to", "assigned_by", "analyst", "status", "updated_by", "updated_at"])
    AlertEvent.objects.create(
        alert=alert,
        event_type=AlertEvent.EventType.ASSIGNED,
        actor=request.user,
        assigned_from=previous_assignee,
        assigned_to=assigned_to,
        message=f"{request.user.username} assigned this alert to {assigned_to.username}.",
    )
    messages.success(request, f"Assigned {alert.alert_id} to {assigned_to.username}.")
    return redirect(alert)


@login_required
@require_POST
def alert_delete(request, pk):
    if not can_delete_alert(request.user):
        raise PermissionDenied
    alert = get_object_or_404(Alert, pk=pk)
    alert_id = alert.alert_id
    alert.delete()
    messages.success(request, f"Deleted {alert_id}.")
    return redirect("alert_list")


@login_required
def elastic_import(request):
    if not can_create_alert(request.user):
        raise PermissionDenied
    form = ElasticJsonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        parsed = parse_elastic_alerts(form.cleaned_data["raw_json"])
        created = []
        for item in parsed:
            alert = Alert.objects.create(created_by=request.user, updated_by=request.user, **item)
            created.append(alert)
        messages.success(request, f"Imported {len(created)} Elastic alert(s).")
        return redirect("alert_list")
    return render(request, "alerts/elastic_import.html", {"form": form})


def filtered_alerts(request):
    queryset = Alert.objects.all()
    search = request.GET.get("q", "").strip()
    severity = request.GET.get("severity", "")
    status = request.GET.get("status", "")
    if search:
        queryset = queryset.filter(
            Q(alert_id__icontains=search)
            | Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(asset__icontains=search)
            | Q(source__icontains=search)
            | Q(analyst__icontains=search)
        )
    if severity:
        queryset = queryset.filter(severity=severity)
    if status:
        queryset = queryset.filter(status=status)
    return queryset


@csrf_exempt
@require_POST
def n8n_webhook(request):
    if request.headers.get(settings.N8N_API_HEADER) != settings.N8N_API_KEY:
        return JsonResponse({"ok": False, "error": "invalid api key"}, status=401)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as error:
        return JsonResponse({"ok": False, "error": str(error)}, status=400)

    records = records_from(payload)
    if not records:
        return JsonResponse({"ok": False, "error": "no alert records found"}, status=400)

    created = []
    for record in records:
        alert = Alert.objects.create(**record_to_alert(record))
        AlertEvent.objects.create(alert=alert, event_type=AlertEvent.EventType.CREATED, message="n8n created this alert.", source="n8n", payload=record)
        created.append(alert)
    return JsonResponse({"ok": True, "created": [alert.alert_id for alert in created]})


@csrf_exempt
@require_POST
def n8n_log_webhook(request):
    if request.headers.get(settings.N8N_API_HEADER) != settings.N8N_API_KEY:
        return JsonResponse({"ok": False, "error": "invalid api key"}, status=401)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as error:
        return JsonResponse({"ok": False, "error": str(error)}, status=400)

    alert_id = payload.get("alert_id") or payload.get("alertId") or payload.get("alert", {}).get("id")
    alert = get_object_or_404(Alert, alert_id=alert_id)
    message = payload.get("message") or payload.get("log") or payload.get("event") or "n8n workflow log received."
    event = AlertEvent.objects.create(
        alert=alert,
        event_type=AlertEvent.EventType.N8N_LOG,
        message=message,
        source="n8n",
        payload=payload,
    )
    return JsonResponse({"ok": True, "event_id": event.id, "alert_id": alert.alert_id})
