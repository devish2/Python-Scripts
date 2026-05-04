# 01 — Server Health Monitor

> **DevOps Concept:** Observability & Alerting

A production-style Python script that continuously monitors CPU, memory, and disk usage and fires alerts to **Slack** or **Email** when thresholds are breached. This is the kind of script SRE and DevOps engineers write to catch resource exhaustion before it causes an outage.

---

## What It Does

| Check | Default Threshold | Alert Channel |
|---|---|---|
| CPU Usage | ≥ 85% | Slack / Email |
| Memory Usage | ≥ 80% | Slack / Email |
| Disk Usage | ≥ 90% | Slack / Email |

- Runs in a continuous loop with a configurable interval (default: 60s)
- Logs every check to `health_monitor.log`
- Sends a detailed alert message with the full system snapshot

---

## Project Structure

```
01-server-health-monitor/
├── monitor.py            # Main script
├── config.json.example   # Config template (copy to config.json)
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Setup & Run

```bash
# 1. Clone the repo
git clone https://github.com/devish2/Python-Scripts.git
cd Python-Scripts/01-server-health-monitor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp config.json.example config.json
# Edit config.json with your Slack webhook URL or email credentials

# 4. Run
python monitor.py
```

### Run as a background service (Linux)

```bash
nohup python monitor.py &
```

Or create a `systemd` unit file for production use.

---

## Config Reference

Edit `config.json` to customize thresholds and alerts:

```json
{
  "thresholds": {
    "cpu_percent": 85,
    "memory_percent": 80,
    "disk_percent": 90
  },
  "check_interval_seconds": 60,
  "slack": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/..."
  },
  "email": {
    "enabled": false,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender": "you@gmail.com",
    "password": "app-password",
    "recipient": "alert@gmail.com"
  }
}
```

Alternatively, use **environment variables** — no config.json required:

```bash
export THRESHOLD_CPU=85
export THRESHOLD_MEM=80
export SLACK_ENABLED=true
export SLACK_WEBHOOK_URL=https://hooks.slack.com/...
python monitor.py
```

---

## Sample Alert Output

```
🚨 Server Health Alert — `prod-server-01`
🕐 Time: 2026-05-04T18:30:00

Breached Thresholds:
  • CPU Usage: 91% (limit: 85%)
  • Disk Usage: 93% (limit: 90%)

Current System Snapshot:
  CPU    : 91%
  Memory : 74% (5.9GB / 8GB)
  Disk   : 93% (186GB / 200GB)
```

---

## Key Concepts Learned

- `psutil` for cross-platform system metrics collection
- Threshold-based alerting logic
- Slack Incoming Webhooks for DevOps notifications
- SMTP email alerting with Python's `smtplib`
- Logging best practices (file + console handler)
- Running Python scripts as long-running services

---

## Extend This Project

- [ ] Add Prometheus metrics export (`/metrics` endpoint with `prometheus_client`)
- [ ] Add per-process CPU tracking (catch runaway processes)
- [ ] Send alerts to PagerDuty or OpsGenie
- [ ] Dockerize the monitor and deploy it on a VM or EC2 instance
- [ ] Store metrics to InfluxDB and visualize in Grafana
