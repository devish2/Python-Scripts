"""
Log Parser & Report Generator
==============================
Parses Nginx/Apache combined access logs and generates
an HTML or CSV summary report with traffic insights.

Author  : Devesh Raj (github.com/devish2)
Repo    : devish2/Python-Scripts
Concept : Log Analysis for SRE (DevOps Core Skill)
"""

import re
import csv
import argparse
import logging
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Regex: Combined Log Format (Nginx & Apache) ────────────────────────────────
LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
    r'(?: "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)")?'
)


# ── Parsing ────────────────────────────────────────────────────────────────────
def parse_log_file(filepath):
    """Parse a log file and return a list of structured records."""
    records = []
    errors = 0
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Log file not found: {filepath}")

    log.info(f"Parsing: {filepath}")
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line_num, line in enumerate(f, 1):
            match = LOG_PATTERN.match(line.strip())
            if match:
                d = match.groupdict()
                records.append({
                    "ip": d["ip"],
                    "time": d["time"],
                    "method": d["method"],
                    "path": d["path"],
                    "status": d["status"],
                    "status_class": d["status"][0] + "xx",
                    "size": int(d["size"]) if d["size"].isdigit() else 0,
                    "referrer": d.get("referrer", "-"),
                    "user_agent": d.get("user_agent", "-"),
                })
            else:
                errors += 1
                if errors <= 5:
                    log.debug(f"Could not parse line {line_num}: {line[:80]}")

    log.info(f"Parsed {len(records)} records. Skipped {errors} malformed lines.")
    return records


# ── Analysis ───────────────────────────────────────────────────────────────────
def analyze(records):
    """Compute summary statistics from parsed records."""
    if not records:
        return {}

    ip_counter = Counter(r["ip"] for r in records)
    path_counter = Counter(r["path"] for r in records)
    status_counter = Counter(r["status"] for r in records)
    status_class_counter = Counter(r["status_class"] for r in records)
    method_counter = Counter(r["method"] for r in records)
    total_bytes = sum(r["size"] for r in records)

    error_records = [r for r in records if r["status"].startswith(("4", "5"))]
    error_paths = Counter(r["path"] for r in error_records)

    return {
        "total_requests": len(records),
        "total_bytes": total_bytes,
        "total_bytes_mb": round(total_bytes / (1024 * 1024), 2),
        "unique_ips": len(ip_counter),
        "top_ips": ip_counter.most_common(10),
        "top_paths": path_counter.most_common(10),
        "top_error_paths": error_paths.most_common(10),
        "status_distribution": dict(sorted(status_counter.items())),
        "status_class_distribution": dict(sorted(status_class_counter.items())),
        "method_distribution": dict(method_counter),
        "error_rate": round(
            len(error_records) / len(records) * 100, 2
        ) if records else 0,
    }


# ── CSV Export ─────────────────────────────────────────────────────────────────
def export_csv(stats, output_path):
    """Write summary stats to a CSV file."""
    output_path = Path(output_path)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Requests", stats["total_requests"]])
        writer.writerow(["Unique IPs", stats["unique_ips"]])
        writer.writerow(["Total Transfer (MB)", stats["total_bytes_mb"]])
        writer.writerow(["Error Rate (%)", stats["error_rate"]])
        writer.writerow([])

        writer.writerow(["Top IP Addresses", "Request Count"])
        for ip, count in stats["top_ips"]:
            writer.writerow([ip, count])
        writer.writerow([])

        writer.writerow(["Top Requested Paths", "Request Count"])
        for path, count in stats["top_paths"]:
            writer.writerow([path, count])
        writer.writerow([])

        writer.writerow(["HTTP Status Code", "Count"])
        for status, count in stats["status_distribution"].items():
            writer.writerow([status, count])

    log.info(f"CSV report saved to: {output_path}")


# ── HTML Export ────────────────────────────────────────────────────────────────
def export_html(stats, output_path, source_file):
    """Write summary stats to a styled HTML report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def table_rows(items):
        return "".join(
            f"<tr><td>{k}</td><td><strong>{v}</strong></td></tr>" for k, v in items
        )

    status_rows = "".join(
        f"<tr><td>{s}</td><td>{c}</td></tr>"
        for s, c in stats["status_distribution"].items()
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Log Report — {source_file}</title>
<style>
  body {{ font-family: monospace; background: #f5f5f5; padding: 2rem; color: #222; }}
  h1 {{ color: #3B6D11; }} h2 {{ color: #444; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
  .meta {{ color: #666; font-size: 0.85rem; margin-bottom: 2rem; }}
  .summary {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem; }}
  .card {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 1rem 1.5rem; min-width: 160px; }}
  .card .val {{ font-size: 1.8rem; font-weight: bold; color: #3B6D11; }}
  .card .lbl {{ font-size: 0.8rem; color: #666; }}
  table {{ border-collapse: collapse; width: 100%; max-width: 600px; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 2rem; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
  th {{ background: #3B6D11; color: #fff; }}
  tr:hover {{ background: #f0f7e8; }}
  .error {{ color: #c0392b; }}
</style>
</head>
<body>
<h1>Log Analysis Report</h1>
<p class="meta">Source: <code>{source_file}</code> &nbsp;|&nbsp; Generated: {now}</p>

<div class="summary">
  <div class="card"><div class="val">{stats["total_requests"]:,}</div><div class="lbl">Total Requests</div></div>
  <div class="card"><div class="val">{stats["unique_ips"]}</div><div class="lbl">Unique IPs</div></div>
  <div class="card"><div class="val">{stats["total_bytes_mb"]} MB</div><div class="lbl">Data Transferred</div></div>
  <div class="card"><div class="val {'error' if stats['error_rate'] > 5 else ''}">{stats["error_rate"]}%</div><div class="lbl">Error Rate</div></div>
</div>

<h2>Top IP Addresses</h2>
<table><tr><th>IP Address</th><th>Requests</th></tr>{table_rows(stats["top_ips"])}</table>

<h2>Top Requested Paths</h2>
<table><tr><th>Path</th><th>Requests</th></tr>{table_rows(stats["top_paths"])}</table>

<h2>Top Error Paths (4xx / 5xx)</h2>
<table><tr><th>Path</th><th>Errors</th></tr>{table_rows(stats["top_error_paths"])}</table>

<h2>HTTP Status Codes</h2>
<table><tr><th>Status</th><th>Count</th></tr>{status_rows}</table>

<h2>HTTP Methods</h2>
<table><tr><th>Method</th><th>Count</th></tr>{table_rows(stats["method_distribution"].items())}</table>
</body>
</html>"""

    output_path = Path(output_path)
    output_path.write_text(html)
    log.info(f"HTML report saved to: {output_path}")


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Parse Nginx/Apache logs and generate a summary report."
    )
    parser.add_argument("logfile", help="Path to the access log file")
    parser.add_argument(
        "--format", choices=["html", "csv", "both"], default="html",
        help="Output format (default: html)"
    )
    parser.add_argument(
        "--output", default="report",
        help="Output file name without extension (default: report)"
    )
    args = parser.parse_args()

    records = parse_log_file(args.logfile)
    stats = analyze(records)

    if args.format in ("html", "both"):
        export_html(stats, f"{args.output}.html", args.logfile)
    if args.format in ("csv", "both"):
        export_csv(stats, f"{args.output}.csv")

    print(f"\n── Summary ────────────────────────────────")
    print(f"  Total Requests : {stats['total_requests']:,}")
    print(f"  Unique IPs     : {stats['unique_ips']}")
    print(f"  Data Transfer  : {stats['total_bytes_mb']} MB")
    print(f"  Error Rate     : {stats['error_rate']}%")
    print(f"  Top IP         : {stats['top_ips'][0] if stats['top_ips'] else 'N/A'}")
    print(f"───────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
