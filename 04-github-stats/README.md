# 04 — GitHub Repo Stats Aggregator

> **DevOps Concept:** API Integration & Reporting

A Python CLI that queries the **GitHub REST API** to fetch stars, forks, open issues, and open PRs for any list of repositories and generates a **Markdown dashboard report**. Perfect for DevOps teams tracking their open-source portfolio or monitoring vendor projects they depend on.

---

## What It Does

- Fetches repo metadata via GitHub REST API v3
- Collects: stars, forks, open issues, open PRs, language, last push date, license
- Generates a sorted Markdown table (sorted by stars)
- Produces a summary block with totals
- Supports both CLI args and a `repos.txt` file as input
- Handles API rate limits gracefully (warns when unauthenticated)

---

## Project Structure

```
04-github-stats/
├── stats.py               # Main script
├── repos.txt.example      # Sample list of repos to track
├── requirements.txt       # Python dependencies
└── README.md
```

---

## Setup & Run

```bash
cd Python-Scripts/04-github-stats
pip install -r requirements.txt

# Fetch stats for specific repos
python stats.py devish2/Python-Scripts kubernetes/kubernetes

# Use a repos list file
cp repos.txt.example repos.txt
python stats.py --file repos.txt --output my-dashboard.md

# Use GitHub token (recommended — 5000 req/hr vs 60 req/hr)
export GITHUB_TOKEN=ghp_yourtokenhere
python stats.py --file repos.txt
```

---

## Sample Output (Markdown)

```markdown
# GitHub Repository Stats Dashboard

> Generated: 2026-05-04 18:30:00
> Repos tracked: 5

## Summary
| Metric | Total |
|--------|-------|
| ⭐ Stars | 98,421 |
| 🍴 Forks | 12,003 |

## Repository Details
| Repository | ⭐ Stars | 🍴 Forks | Language | Last Push |
|------------|---------|---------|----------|-----------|
| kubernetes/kubernetes | 89,100 | 32,500 | Go | 2026-05-04 |
...
```

---

## Key Concepts Learned

- GitHub REST API v3 authentication (Bearer token)
- Python `requests.Session` for connection reuse
- Pagination handling and rate limit awareness
- Markdown report generation from structured data
- CLI design with `argparse` — flags, positional args, file input
- Good API citizenship (request throttling with `time.sleep`)

---

## Extend This Project

- [ ] Track stats over time — store in SQLite and show trend arrows (↑ ↓)
- [ ] Weekly email digest with top gainers by star count
- [ ] Generate HTML report with Chart.js bar charts
- [ ] Add GitHub Actions workflow to run this daily and commit the report
- [ ] Publish the Markdown report to GitHub Pages automatically
