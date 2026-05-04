"""
CI/CD Pipeline Notifier
========================
Polls GitHub Actions workflow runs and posts build status
(pass/fail/duration) to a Slack channel. Filters by branch
or workflow name. Webhook-ready design.

Author  : Devesh Raj (github.com/devish2)
Repo    : devish2/Python-Scripts
Concept : CI/CD Visibility (DevOps Core Skill)
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path

import requests

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline_notifier.log"),
    ],
)
log = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"

# Status emoji mapping
STATUS_EMOJI = {
    "success": "✅",
    "failure": "❌",
    "cancelled": "🚫",
    "skipped": "⏭️",
    "in_progress": "🔄",
    "queued": "⏳",
    "waiting": "⏳",
    "neutral": "⚪",
    "timed_out": "⌛",
    "action_required": "⚠️",
}

# Slack color for conclusion
SLACK_COLORS = {
    "success": "#2eb886",
    "failure": "#e74c3c",
    "cancelled": "#95a5a6",
    "timed_out": "#e67e22",
}


# ── GitHub Actions API ─────────────────────────────────────────────────────────
class GitHubActionsClient:
    def __init__(self, token, owner, repo):
        self.owner = owner
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def get_workflow_runs(self, branch=None, workflow_name=None, limit=20):
        """Fetch recent workflow runs for the repo."""
        params = {"per_page": limit}
        if branch:
            params["branch"] = branch

        url = f"{GITHUB_API}/repos/{self.owner}/{self.repo}/actions/runs"
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            runs = resp.json().get("workflow_runs", [])

            if workflow_name:
                runs = [r for r in runs if workflow_name.lower() in r.get("name", "").lower()]

            return runs
        except requests.RequestException as e:
            log.error(f"Failed to fetch workflow runs: {e}")
            return []


# ── Duration Formatter ─────────────────────────────────────────────────────────
def format_duration(run):
    """Calculate and format run duration."""
    try:
        started = run.get("run_started_at") or run.get("created_at")
        updated = run.get("updated_at")
        if not started or not updated:
            return "N/A"

        fmt = "%Y-%m-%dT%H:%M:%SZ"
        start_dt = datetime.strptime(started, fmt).replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(updated, fmt).replace(tzinfo=timezone.utc)
        seconds = int((end_dt - start_dt).total_seconds())
        if seconds < 60:
            return f"{seconds}s"
        return f"{seconds // 60}m {seconds % 60}s"
    except Exception:
        return "N/A"


# ── Slack Notification ─────────────────────────────────────────────────────────
def send_slack_notification(webhook_url, run, repo_fullname):
    """Send a formatted Slack message for a workflow run."""
    conclusion = run.get("conclusion") or run.get("status", "unknown")
    emoji = STATUS_EMOJI.get(conclusion, "❓")
    color = SLACK_COLORS.get(conclusion, "#cccccc")
    duration = format_duration(run)

    branch = run.get("head_branch", "unknown")
    commit_sha = run.get("head_sha", "")[:7]
    commit_msg = run.get("display_title", "—")
    actor = run.get("triggering_actor", {}).get("login", "unknown")
    workflow = run.get("name", "unknown")
    run_url = run.get("html_url", "")
    run_number = run.get("run_number", "")

    text = (
        f"{emoji} *{workflow}* #{run_number} — `{conclusion.upper()}`\n"
        f"Repo: `{repo_fullname}` | Branch: `{branch}` | Duration: `{duration}`\n"
        f"Commit: `{commit_sha}` — {commit_msg}\n"
        f"Triggered by: @{actor}"
    )

    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": text},
                        "accessory": {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Run"},
                            "url": run_url,
                        },
                    }
                ],
            }
        ]
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        log.info(f"Slack notification sent for run #{run_number} ({conclusion})")
    except Exception as e:
        log.error(f"Slack notification failed: {e}")


# ── State Tracking ─────────────────────────────────────────────────────────────
def load_seen_runs(state_file):
    """Load set of already-notified run IDs from state file."""
    path = Path(state_file)
    if not path.exists():
        return set()
    return set(path.read_text().splitlines())


def save_seen_runs(state_file, seen_ids):
    """Persist notified run IDs to avoid duplicate alerts."""
    path = Path(state_file)
    recent = list(seen_ids)[-500:]  # Keep last 500 to avoid unbounded growth
    path.write_text("\n".join(str(i) for i in recent))


# ── Main Loop ──────────────────────────────────────────────────────────────────
def run_once(client, config, seen_runs):
    """Fetch runs and notify for any new completed runs."""
    runs = client.get_workflow_runs(
        branch=config.get("branch"),
        workflow_name=config.get("workflow_name"),
        limit=config.get("limit", 20),
    )

    new_notifications = 0
    for run in runs:
        run_id = str(run.get("id"))
        status = run.get("status")
        conclusion = run.get("conclusion")

        # Only notify on completed runs we haven't seen yet
        if status != "completed" or run_id in seen_runs:
            continue

        # Filter by conclusion if specified
        notify_on = config.get("notify_on", ["success", "failure", "cancelled", "timed_out"])
        if conclusion not in notify_on:
            seen_runs.add(run_id)
            continue

        repo_fullname = f"{client.owner}/{client.repo}"
        send_slack_notification(config["slack_webhook"], run, repo_fullname)
        seen_runs.add(run_id)
        new_notifications += 1

    return new_notifications


def main():
    parser = argparse.ArgumentParser(
        description="Poll GitHub Actions and send Slack notifications for build status."
    )
    parser.add_argument("repo", help="Repository in 'owner/repo' format")
    parser.add_argument(
        "--branch", help="Only track runs on this branch (e.g. main)"
    )
    parser.add_argument(
        "--workflow", help="Filter by workflow name (partial match)"
    )
    parser.add_argument(
        "--interval", type=int, default=60,
        help="Polling interval in seconds (default: 60). Use 0 for single run."
    )
    parser.add_argument(
        "--notify-on",
        default="success,failure,cancelled,timed_out",
        help="Comma-separated conclusions to notify on (default: all terminal states)"
    )
    parser.add_argument(
        "--state-file", default=".seen_runs.txt",
        help="File to track already-notified runs (default: .seen_runs.txt)"
    )
    args = parser.parse_args()

    # Validate required env vars
    token = os.getenv("GITHUB_TOKEN")
    webhook = os.getenv("SLACK_WEBHOOK_URL")

    if not token:
        log.error("GITHUB_TOKEN environment variable is required.")
        sys.exit(1)
    if not webhook:
        log.error("SLACK_WEBHOOK_URL environment variable is required.")
        sys.exit(1)

    parts = args.repo.strip().split("/")
    if len(parts) != 2:
        log.error("Repo must be in 'owner/repo' format.")
        sys.exit(1)

    owner, repo = parts
    client = GitHubActionsClient(token, owner, repo)
    config = {
        "slack_webhook": webhook,
        "branch": args.branch,
        "workflow_name": args.workflow,
        "notify_on": [s.strip() for s in args.notify_on.split(",")],
        "limit": 20,
    }

    log.info(f"CI/CD Notifier started for: {args.repo}")
    log.info(f"Branch filter: {args.branch or 'all'}")
    log.info(f"Notify on: {config['notify_on']}")
    log.info(f"Polling interval: {args.interval}s")

    seen_runs = load_seen_runs(args.state_file)

    while True:
        count = run_once(client, config, seen_runs)
        save_seen_runs(args.state_file, seen_runs)

        if count:
            log.info(f"Sent {count} Slack notification(s).")
        else:
            log.info("No new completed runs to notify.")

        if args.interval == 0:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
