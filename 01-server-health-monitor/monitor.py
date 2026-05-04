"""
Server Health Monitor
=====================
Monitors CPU, memory, and disk usage and sends alerts
via Slack or Email when thresholds are breached.

Author  : Devesh Raj (github.com/devish2)
Repo    : devish2/Python-Scripts
Concept : Observability & Alerting (DevOps Core Skill)
"""

import psutil
import smtplib
import time
import logging
import json
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import requests
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("health_monitor.log"),
    ],
)
log = logging.getLogger(__name__)


# ── Config ─────────────────────────────────────────────────────────────────────
def load_config(path="config.json"):
    """Load config from JSON file or fall back to environment variables."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {
        "thresholds": {
            "cpu_percent": float(os.getenv("THRESHOLD_CPU", 85)),
            "memory_percent": float(os.getenv("THRESHOLD_MEM", 80)),
            "disk_percent": float(os.getenv("THRESHOLD_DISK", 90)),
        },
        "check_interval_seconds": int(os.getenv("CHECK_INTERVAL", 60)),
        "slack": {
            "enabled": os.getenv("SLACK_ENABLED", "false").lower() == "true",
            "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
        },
        "email": {
            "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", 587)),
            "sender": os.getenv("EMAIL_SENDER", ""),
            "password": os.getenv("EMAIL_PASSWORD", ""),
            "recipient": os.getenv("EMAIL_RECIPIENT", ""),
        },
    }


# ── Metrics Collection ─────────────────────────────────────────────────────────
def collect_metrics():
    """Collect current system metrics."""
    disk = psutil.disk_usage("/")
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_used_gb": round(psutil.virtual_memory().used / (1024 ** 3), 2),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / (1024 ** 3), 2),
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
    }
    return metrics


def check_thresholds(metrics, thresholds):
    """Return list of breached threshold alerts."""
    alerts = []
    checks = {
        "CPU Usage": ("cpu_percent", "%"),
        "Memory Usage": ("memory_percent", "%"),
        "Disk Usage": ("disk_percent", "%"),
    }
    for label, (key, unit) in checks.items():
        value = metrics[key]
        limit = thresholds[key]
        if value >= limit:
            alerts.append({
                "metric": label,
                "value": value,
                "threshold": limit,
                "unit": unit,
            })
    return alerts


# ── Alerting ───────────────────────────────────────────────────────────────────
def build_message(alerts, metrics):
    """Build a human-readable alert message."""
    host = os.uname().nodename
    lines = [
        f"🚨 *Server Health Alert* — `{host}`",
        f"🕐 Time: {metrics['timestamp']}",
        "",
        "*Breached Thresholds:*",
    ]
    for a in alerts:
        lines.append(
            f"  • {a['metric']}: *{a['value']}{a['unit']}* (limit: {a['threshold']}{a['unit']})"
        )
    lines += [
        "",
        "*Current System Snapshot:*",
        f"  CPU    : {metrics['cpu_percent']}%",
        f"  Memory : {metrics['memory_percent']}% ({metrics['memory_used_gb']}GB / {metrics['memory_total_gb']}GB)",
        f"  Disk   : {metrics['disk_percent']}% ({metrics['disk_used_gb']}GB / {metrics['disk_total_gb']}GB)",
    ]
    return "\n".join(lines)


def send_slack_alert(webhook_url, message):
    """Send alert to a Slack channel via Incoming Webhook."""
    if not SLACK_AVAILABLE:
        log.warning("requests library not installed. Slack alerts disabled.")
        return
    payload = {"text": message}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        log.info("Slack alert sent successfully.")
    except Exception as e:
        log.error(f"Failed to send Slack alert: {e}")


def send_email_alert(config, message):
    """Send alert via SMTP email."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🚨 Server Health Alert"
        msg["From"] = config["sender"]
        msg["To"] = config["recipient"]
        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
            server.ehlo()
            server.starttls()
            server.login(config["sender"], config["password"])
            server.sendmail(config["sender"], config["recipient"], msg.as_string())
        log.info("Email alert sent successfully.")
    except Exception as e:
        log.error(f"Failed to send email alert: {e}")


# ── Main Loop ──────────────────────────────────────────────────────────────────
def run():
    config = load_config()
    thresholds = config["thresholds"]
    interval = config["check_interval_seconds"]

    log.info("Server Health Monitor started.")
    log.info(f"Thresholds → CPU: {thresholds['cpu_percent']}% | "
             f"Memory: {thresholds['memory_percent']}% | "
             f"Disk: {thresholds['disk_percent']}%")
    log.info(f"Check interval: {interval}s")

    while True:
        metrics = collect_metrics()
        log.info(
            f"CPU={metrics['cpu_percent']}% | "
            f"MEM={metrics['memory_percent']}% | "
            f"DISK={metrics['disk_percent']}%"
        )

        alerts = check_thresholds(metrics, thresholds)

        if alerts:
            message = build_message(alerts, metrics)
            log.warning(f"{len(alerts)} threshold(s) breached!")

            if config["slack"]["enabled"]:
                send_slack_alert(config["slack"]["webhook_url"], message)

            if config["email"]["enabled"]:
                send_email_alert(config["email"], message)

        time.sleep(interval)


if __name__ == "__main__":
    run()
