# 05 — CI/CD Pipeline Notifier

> **DevOps Concept:** CI/CD Visibility

A Python script that polls **GitHub Actions** workflow runs and pushes real-time build status notifications to a **Slack channel**. Tracks pass/fail/duration per run, filters by branch or workflow name, and avoids duplicate alerts using a local state file.

---

## What It Does

- Polls GitHub Actions API for workflow runs at a configurable interval
- Sends Slack notifications for: `success`, `failure`, `cancelled`, `timed_out`
- Includes: workflow name, run number, branch, commit SHA, commit message, actor, duration
- "View Run" button links directly to the GitHub Actions run page
- State file prevents duplicate notifications on re-runs
- Supports branch filtering and workflow name filtering

---

## Project Structure

```
05-cicd-notifier/
├── notifier.py            # Main script
├── requirements.txt       # Python dependencies
└── README.md
```

---

## Setup & Run

```bash
cd Python-Scripts/05-cicd-notifier
pip install -r requirements.txt

# Required environment variables
export GITHUB_TOKEN=ghp_yourtokenhere
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Watch all runs on a repo (polls every 60s)
python notifier.py devish2/Python-Scripts

# Filter to main branch only
python notifier.py devish2/Python-Scripts --branch main

# Filter to a specific workflow and poll every 30s
python notifier.py devish2/Python-Scripts --workflow "CI" --interval 30

# Single run (no loop) — useful for testing
python notifier.py devish2/Python-Scripts --interval 0

# Notify only on failures
python notifier.py devish2/Python-Scripts --notify-on failure,timed_out
```

---

## Sample Slack Notification

```
✅ CI Pipeline #42 — SUCCESS
Repo: devish2/Python-Scripts | Branch: main | Duration: 2m 14s
Commit: a1b2c3d — fix: handle empty log file gracefully
Triggered by: @devish2
                                              [View Run]
```

---

## GitHub Token Scopes Required

Generate a token at GitHub → Settings → Developer Settings → Personal Access Tokens

Minimum scopes needed:
- `repo` (for private repos)
- `actions:read` (for workflow runs)

For **public repos only**, a Fine-grained token with `Actions: Read` is sufficient.

---

## Run as a Background Service

```bash
nohup python notifier.py devish2/Python-Scripts --branch main &
```

Or deploy as a **Docker container** on an EC2 instance for always-on monitoring.

---

## Key Concepts Learned

- GitHub Actions REST API — workflow runs endpoint
- Bearer token authentication with `requests.Session`
- Polling vs. webhooks — trade-offs and use cases
- State management with a local file to avoid duplicate notifications
- Slack Block Kit message formatting
- Argparse for rich CLI interfaces

---

## Extend This Project

- [ ] Switch from polling to GitHub Webhooks (push model — more efficient)
- [ ] Post to Microsoft Teams or Google Chat instead of Slack
- [ ] Add per-job breakdown (which step failed)
- [ ] Store run history in SQLite and expose a local web dashboard
- [ ] Dockerize and deploy on ECS or Kubernetes as a sidecar notifier
- [ ] Trigger auto-rollback via AWS CodeDeploy API on failure notification
