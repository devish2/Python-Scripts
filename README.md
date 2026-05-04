# Python-Scripts

> **Python automation scripts for DevOps engineers — built for learning, production-ready in design.**

A curated collection of real-world Python automation projects covering core DevOps skills: observability, log analysis, cloud backup, API reporting, and CI/CD visibility. Each project is self-contained, well-documented, and designed to be extended.

---

## Who Is This For?

This repo is for:
- **DevOps beginners** who want hands-on projects beyond hello-world
- **Mentees** working through a structured DevOps learning path
- **Engineers** looking for clean Python automation templates to adapt

Every project includes a `README.md` with setup steps, key concepts, and extension ideas so you learn the *why*, not just the *how*.

---

## Projects

| # | Project | DevOps Concept | Libraries |
|---|---------|---------------|-----------|
| 01 | [Server Health Monitor](#01-server-health-monitor) | Observability & Alerting | `psutil`, `requests` |
| 02 | [Log Parser & Report Generator](#02-log-parser--report-generator) | Log Analysis for SRE | stdlib only |
| 03 | [AWS S3 Backup Automator](#03-aws-s3-backup-automator) | Cloud Automation & Backup | `boto3`, `requests` |
| 04 | [GitHub Repo Stats Aggregator](#04-github-repo-stats-aggregator) | API Integration & Reporting | `requests` |
| 05 | [CI/CD Pipeline Notifier](#05-cicd-pipeline-notifier) | CI/CD Visibility | `requests` |

---

## 01 — Server Health Monitor

Monitors CPU, memory, and disk usage and fires alerts to Slack or Email when thresholds are breached. Runs as a continuous loop — schedule it with cron or `systemd`.

```bash
cd 01-server-health-monitor
pip install -r requirements.txt
cp config.json.example config.json   # add your Slack webhook
python monitor.py
```

**What you learn:** `psutil`, Slack webhooks, SMTP alerting, threshold logic, logging best practices.

📂 [View Project →](./01-server-health-monitor/)

---

## 02 — Log Parser & Report Generator

Parses Nginx/Apache access logs and generates an HTML dashboard or CSV report. Extracts top IPs, error paths, status code distribution, and overall error rate — exactly what SRE engineers do in production.

```bash
cd 02-log-parser
python parser.py sample-access.log --format both
```

**What you learn:** Regex parsing, `Counter`, `argparse`, HTML report generation — zero external dependencies.

📂 [View Project →](./02-log-parser/)

---

## 03 — AWS S3 Backup Automator

Compresses a local directory into a timestamped zip and uploads it to S3 with server-side encryption. IAM-role friendly — no hardcoded keys needed on EC2. Slack notification on success or failure.

```bash
cd 03-s3-backup
pip install -r requirements.txt
export AWS_S3_BUCKET=my-bucket
export SLACK_WEBHOOK_URL=https://hooks.slack.com/...
python backup.py /path/to/your/app-data
```

**What you learn:** `boto3`, S3 encryption, IAM roles, date-partitioned S3 keys, cron automation.

📂 [View Project →](./03-s3-backup/)

---

## 04 — GitHub Repo Stats Aggregator

Fetches stars, forks, open issues, and PRs for a list of GitHub repos and generates a Markdown dashboard. Great for tracking your own portfolio or monitoring open-source projects your team depends on.

```bash
cd 04-github-stats
pip install -r requirements.txt
export GITHUB_TOKEN=ghp_...
python stats.py devish2/Python-Scripts kubernetes/kubernetes
```

**What you learn:** GitHub REST API v3, `requests.Session`, rate limit handling, Markdown report generation.

📂 [View Project →](./04-github-stats/)

---

## 05 — CI/CD Pipeline Notifier

Polls GitHub Actions workflow runs and sends Slack messages with build status, duration, branch, and commit info. Supports branch and workflow filtering. State file prevents duplicate notifications.

```bash
cd 05-cicd-notifier
pip install -r requirements.txt
export GITHUB_TOKEN=ghp_...
export SLACK_WEBHOOK_URL=https://hooks.slack.com/...
python notifier.py devish2/Python-Scripts --branch main
```

**What you learn:** GitHub Actions API, polling vs webhooks, Slack Block Kit, CLI design with `argparse`.

📂 [View Project →](./05-cicd-notifier/)

---

## Getting Started

```bash
# Clone the repo
git clone https://github.com/devish2/Python-Scripts.git
cd Python-Scripts

# Python 3.8+ required
python --version

# Each project has its own requirements.txt — install per project
cd 01-server-health-monitor
pip install -r requirements.txt
```

---

## Learning Path Suggestion

If you are new to DevOps automation, go through the projects in this order:

```
02 (no dependencies, pure Python) →
01 (system monitoring, Slack alerts) →
04 (API integration, GitHub) →
05 (CI/CD, GitHub Actions) →
03 (cloud, AWS S3)
```

---

## Repository Structure

```
Python-Scripts/
├── 01-server-health-monitor/
│   ├── monitor.py
│   ├── config.json.example
│   ├── requirements.txt
│   └── README.md
├── 02-log-parser/
│   ├── parser.py
│   ├── sample-access.log
│   └── README.md
├── 03-s3-backup/
│   ├── backup.py
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
├── 04-github-stats/
│   ├── stats.py
│   ├── repos.txt.example
│   ├── requirements.txt
│   └── README.md
├── 05-cicd-notifier/
│   ├── notifier.py
│   ├── requirements.txt
│   └── README.md
└── README.md
```

---

## Contributing

This is a mentorship reference repo. If you are a mentee building on top of these projects:

1. Fork the repo
2. Create a branch: `git checkout -b feature/add-prometheus-export`
3. Make your changes with a clear commit message
4. Open a PR with a description of what you added and why

---

## About

Built and maintained by **Devesh Raj** — DevOps Engineer, Cloud Architect, and Mentor.

- 🌐 [mealobox.in](https://mealobox.in)
- 💼 [GitHub @devish2](https://github.com/devish2)
- 🎓 Mentoring on [ADPList](https://adplist.org) · [Preplaced](https://preplaced.in) · [Scaler](https://scaler.com) · [Codementor](https://codementor.io)
- 🎤 Speaker at Google I/O Extended & Google DEVFEST

> *"Good automation scripts are like good documentation — they teach as much as they do."*
