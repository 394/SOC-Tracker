import json

from django import forms
from django.contrib.auth.models import User

from .models import Alert


class AlertForm(forms.ModelForm):
    iocs_text = forms.CharField(
        label="IOCs",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "IP, hash, domain, username"}),
    )

    class Meta:
        model = Alert
        fields = ["title", "description", "source", "severity", "status", "analyst", "tactic", "asset", "sla_hours"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 8, "class": "stretch-textarea"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["iocs_text"].initial = ", ".join(self.instance.iocs or [])

    def save(self, commit=True):
        alert = super().save(commit=False)
        alert.iocs = [item.strip() for item in self.cleaned_data.get("iocs_text", "").split(",") if item.strip()]
        if commit:
            alert.save()
        return alert


class ElasticJsonForm(forms.Form):
    raw_json = forms.CharField(
        label="Paste Elastic alert JSON",
        widget=forms.Textarea(attrs={"rows": 14, "class": "json-paste", "placeholder": '{"_source":{"kibana.alert.rule.name":"Suspicious login"}}'}),
    )

    def clean_raw_json(self):
        raw = self.cleaned_data["raw_json"]
        try:
            json.loads(raw)
        except json.JSONDecodeError as error:
            raise forms.ValidationError(f"Invalid JSON: {error}") from error
        return raw


class AssignAlertForm(forms.Form):
    assigned_to = forms.ModelChoiceField(queryset=User.objects.none(), label="Assign to")

    def __init__(self, *args, assignable_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        assignable_roles = assignable_roles or []
        self.fields["assigned_to"].queryset = User.objects.filter(profile__role__in=assignable_roles).order_by("username")
