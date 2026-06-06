#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ALERTS_FILE = DATA_DIR / "alerts.json"
API_KEY = os.environ.get("N8N_API_KEY", "change-me")
API_HEADER = os.environ.get("N8N_API_HEADER", "X-API-Key")


def read_alerts():
    if not ALERTS_FILE.exists():
        return []
    try:
        with ALERTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def write_alerts(alerts):
    DATA_DIR.mkdir(exist_ok=True)
    with ALERTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(alerts, file, indent=2)


def alert_number(alert_id):
    digits = "".join(character for character in str(alert_id or "") if character.isdigit())
    return int(digits) if digits else 0


def next_alert_id(alerts):
    highest = max((alert_number(alert.get("id")) for alert in alerts), default=0)
    return f"SOC-{highest + 1:06d}"


def normalize_alert(payload, alerts):
    alert = payload.get("alert", payload) if isinstance(payload, dict) else {}
    if isinstance(alert, dict) and isinstance(alert.get("_source"), dict):
        alert = {**alert["_source"], "_id": alert.get("_id"), "_index": alert.get("_index")}
    title = first_value(alert, [
        "title", "summary", "kibana.alert.rule.name", "signal.rule.name",
        "rule.name", "event.action", "message"
    ])
    description = first_value(alert, [
        "description", "kibana.alert.reason", "kibana.alert.rule.description",
        "signal.reason", "rule.description", "message"
    ])
    severity = normalize_severity(first_value(alert, [
        "severity", "kibana.alert.severity", "signal.rule.severity",
        "rule.severity", "event.severity", "log.level"
    ]))
    asset = first_value(alert, [
        "asset", "host.name", "host.hostname", "agent.name", "user.name",
        "source.ip", "destination.ip"
    ])
    return {
        "id": alert.get("id") if str(alert.get("id", "")).startswith("SOC-") else next_alert_id(alerts),
        "title": title or "Untitled alert",
        "description": description or "Imported from Elastic JSON.",
        "source": first_value(alert, ["source", "event.module", "event.dataset", "data_stream.dataset", "_index"]) or "n8n",
        "severity": severity,
        "status": alert.get("status") or "New",
        "analyst": alert.get("analyst") or "Unassigned",
        "tactic": first_value(alert, ["tactic", "kibana.alert.rule.threat.tactic.name", "threat.tactic.name"]) or "Unknown",
        "asset": asset or "Unknown",
        "iocs": alert.get("iocs") if isinstance(alert.get("iocs"), list) else collect_iocs(alert),
        "slaHours": int(alert.get("slaHours") or sla_for_severity(severity)),
        "createdAt": first_value(alert, ["createdAt", "@timestamp", "event.created", "kibana.alert.start"]) or payload.get("sentAt") or datetime.now(timezone.utc).isoformat(),
        "lastSentAt": alert.get("lastSentAt") or "",
    }


def first_value(record, paths):
    for path in paths:
        value = read_path(record, path)
        values = flatten(value)
        if values:
            return values[0]
    return ""


def read_path(record, path):
    if not isinstance(record, dict):
        return None
    if path in record:
        return record[path]
    value = record
    for key in path.split("."):
        if isinstance(value, list):
            value = [item.get(key) for item in value if isinstance(item, dict) and key in item]
        elif isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    return value


def flatten(value):
    if value is None:
        return []
    if isinstance(value, list):
        output = []
        for item in value:
            output.extend(flatten(item))
        return output
    if isinstance(value, dict):
        for key in ("name", "ip"):
            if key in value:
                return flatten(value[key])
        return []
    text = str(value).strip()
    return [text] if text else []


def collect_iocs(alert):
    fields = [
        "source.ip", "destination.ip", "client.ip", "server.ip", "host.ip", "related.ip",
        "url.domain", "dns.question.name", "destination.domain", "related.hosts",
        "file.hash.sha256", "file.hash.sha1", "file.hash.md5", "process.hash.sha256", "related.hash",
        "user.name", "source.user.name", "destination.user.name",
    ]
    values = []
    for field in fields:
        values.extend(flatten(read_path(alert, field)))
    return list(dict.fromkeys(values))


def normalize_severity(value):
    text = str(value or "").lower()
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = -1
    if text in ("critical", "fatal") or number >= 70:
        return "Critical"
    if text in ("high", "error") or number >= 50:
        return "High"
    if text in ("medium", "warning", "warn") or number >= 20:
        return "Medium"
    return "Low"


def sla_for_severity(severity):
    return {"Critical": 2, "High": 4, "Medium": 8}.get(severity, 24)


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path == "/api/alerts":
            self.send_json(read_alerts())
            return
        super().do_GET()

    def do_PUT(self):
        if urlparse(self.path).path != "/api/alerts":
            self.send_error(404)
            return
        alerts = self.read_json()
        if not isinstance(alerts, list):
            self.send_error(400, "Expected a JSON array")
            return
        write_alerts(alerts)
        self.send_json({"ok": True, "count": len(alerts)})

    def do_POST(self):
        if urlparse(self.path).path != "/api/webhook/n8n":
            self.send_error(404)
            return
        if self.headers.get(API_HEADER) != API_KEY:
            self.send_error(401, "Invalid API key")
            return

        payload = self.read_json()
        if not isinstance(payload, dict):
            self.send_error(400, "Expected a JSON object")
            return

        alerts = read_alerts()
        incoming = normalize_alert(payload, alerts)
        existing_index = next((index for index, item in enumerate(alerts) if item.get("id") == incoming["id"]), -1)
        if existing_index >= 0:
            alerts[existing_index] = {**alerts[existing_index], **incoming}
        else:
            alerts.insert(0, incoming)
        write_alerts(alerts)
        self.send_json({"ok": True, "alert": incoming})

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else None

    def send_json(self, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    os.chdir(ROOT)
    print(f"SOC Alert Tracker listening on http://0.0.0.0:{port}")
    print(f"n8n webhook endpoint: POST /api/webhook/n8n with {API_HEADER}: {API_KEY}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
