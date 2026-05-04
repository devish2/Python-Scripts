"""
GitHub Repo Stats Aggregator
==============================
Fetches stars, forks, open issues, and open PRs for a
list of GitHub repositories and generates a Markdown
dashboard report.

Author  : Devesh Raj (github.com/devish2)
Repo    : devish2/Python-Scripts
Concept : API Integration & Reporting (DevOps Core Skill)
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

import requests

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


# ── GitHub API Client ──────────────────────────────────────────────────────────
class GitHubClient:
    def __init__(self, token=None):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
            log.info("Using authenticated GitHub API (higher rate limits).")
        else:
            log.warning(
                "No GITHUB_TOKEN set. Rate limited to 60 req/hr. "
                "Set GITHUB_TOKEN env var to increase to 5000 req/hr."
            )

    def get(self, endpoint, params=None):
        url = f"{GITHUB_API}{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 404:
                return None, "Not found"
            if resp.status_code == 403:
                return None, "Rate limit exceeded or access forbidden"
            resp.raise_for_status()
            return resp.json(), None
        except requests.RequestException as e:
            return None, str(e)

    def get_repo(self, owner, repo):
        data, err = self.get(f"/repos/{owner}/{repo}")
        return data, err

    def get_open_prs(self, owner, repo):
        data, err = self.get(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": "open", "per_page": 1}
        )
        if err:
            return None, err
        # Use link header or search API for total count
        search_data, serr = self.get(
            "/search/issues",
            params={"q": f"repo:{owner}/{repo} is:pr is:open", "per_page": 1}
        )
        if serr:
            return 0, None
        return search_data.get("total_count", 0), None


# ── Stats Collection ───────────────────────────────────────────────────────────
def fetch_repo_stats(client, repo_fullname):
    """Fetch stats for a single repo. Returns a dict."""
    parts = repo_fullname.strip().split("/")
    if len(parts) != 2:
        log.error(f"Invalid repo format: {repo_fullname}. Use 'owner/repo'.")
        return None

    owner, repo = parts
    log.info(f"Fetching stats for: {repo_fullname}")

    data, err = client.get_repo(owner, repo)
    if err or not data:
        log.error(f"Failed to fetch {repo_fullname}: {err}")
        return {
            "repo": repo_fullname,
            "error": err or "Unknown error",
        }

    pr_count, _ = client.get_open_prs(owner, repo)
    time.sleep(0.3)  # Be a good API citizen

    pushed_at = data.get("pushed_at", "")[:10] if data.get("pushed_at") else "N/A"

    return {
        "repo": repo_fullname,
        "description": data.get("description") or "—",
        "language": data.get("language") or "—",
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "open_prs": pr_count or 0,
        "watchers": data.get("watchers_count", 0),
        "last_push": pushed_at,
        "url": data.get("html_url", ""),
        "archived": data.get("archived", False),
        "license": data.get("license", {}).get("spdx_id", "—") if data.get("license") else "—",
    }


# ── Markdown Report ────────────────────────────────────────────────────────────
def generate_markdown_report(stats_list, output_path):
    """Generate a Markdown dashboard file from repo stats."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    successful = [s for s in stats_list if "error" not in s]
    failed = [s for s in stats_list if "error" in s]

    total_stars = sum(s["stars"] for s in successful)
    total_forks = sum(s["forks"] for s in successful)
    total_issues = sum(s["open_issues"] for s in successful)
    total_prs = sum(s["open_prs"] for s in successful)

    lines = [
        "# GitHub Repository Stats Dashboard",
        "",
        f"> Generated: {now}  ",
        f"> Repos tracked: {len(stats_list)}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Total |",
        f"|--------|-------|",
        f"| ⭐ Stars | {total_stars:,} |",
        f"| 🍴 Forks | {total_forks:,} |",
        f"| 🐛 Open Issues | {total_issues:,} |",
        f"| 🔀 Open PRs | {total_prs:,} |",
        "",
        "---",
        "",
        "## Repository Details",
        "",
        "| Repository | ⭐ Stars | 🍴 Forks | 🐛 Issues | 🔀 PRs | Language | Last Push | License |",
        "|------------|---------|---------|----------|--------|----------|-----------|---------|",
    ]

    for s in sorted(successful, key=lambda x: x["stars"], reverse=True):
        archived = " 📦" if s["archived"] else ""
        lines.append(
            f"| [{s['repo']}]({s['url']}){archived} "
            f"| {s['stars']:,} "
            f"| {s['forks']:,} "
            f"| {s['open_issues']:,} "
            f"| {s['open_prs']:,} "
            f"| {s['language']} "
            f"| {s['last_push']} "
            f"| {s['license']} |"
        )

    if failed:
        lines += [
            "",
            "---",
            "",
            "## Failed to Fetch",
            "",
            "| Repository | Error |",
            "|------------|-------|",
        ]
        for s in failed:
            lines.append(f"| {s['repo']} | {s['error']} |")

    lines += ["", "---", "", f"*Generated by [devish2/Python-Scripts](https://github.com/devish2/Python-Scripts)*"]

    output = Path(output_path)
    output.write_text("\n".join(lines))
    log.info(f"Markdown report saved: {output}")
    return output


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Fetch GitHub repo stats and generate a Markdown dashboard."
    )
    parser.add_argument(
        "repos",
        nargs="*",
        help="Repos in 'owner/repo' format (e.g. devish2/Python-Scripts)",
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to a text file with one 'owner/repo' per line"
    )
    parser.add_argument(
        "--output", "-o",
        default="github-stats-report.md",
        help="Output Markdown file path (default: github-stats-report.md)"
    )
    args = parser.parse_args()

    repos = list(args.repos)
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            log.error(f"Repos file not found: {file_path}")
            sys.exit(1)
        repos += [line.strip() for line in file_path.read_text().splitlines()
                  if line.strip() and not line.startswith("#")]

    if not repos:
        parser.print_help()
        print("\nExample: python stats.py devish2/Python-Scripts torvalds/linux")
        sys.exit(0)

    token = os.getenv("GITHUB_TOKEN")
    client = GitHubClient(token)

    stats_list = [fetch_repo_stats(client, r) for r in repos if r]
    stats_list = [s for s in stats_list if s]  # remove None

    output = generate_markdown_report(stats_list, args.output)
    print(f"\n✅ Report generated: {output}\n")


if __name__ == "__main__":
    main()
