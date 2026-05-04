# 02 — Log Parser & Report Generator

> **DevOps Concept:** Log Analysis for SRE

A Python CLI tool that parses **Nginx** and **Apache** Combined Format access logs and produces an **HTML dashboard** or **CSV report** with traffic insights. This is exactly what SRE engineers do to understand traffic patterns, find error spikes, and identify bad actors.

---

## What It Does

- Parses standard Combined Log Format (Nginx + Apache compatible)
- Extracts: IP addresses, HTTP methods, paths, status codes, response sizes
- Generates:
  - Top 10 IP addresses by request count
  - Top 10 most requested paths
  - Top error paths (4xx / 5xx)
  - HTTP status code distribution
  - Overall error rate %
  - Total data transferred (MB)
- Exports to **HTML** (visual dashboard) or **CSV** (for spreadsheet analysis)

---

## Project Structure

```
02-log-parser/
├── parser.py             # Main script
├── sample-access.log     # Sample Nginx log for testing
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Setup & Run

```bash
cd Python-Scripts/02-log-parser
pip install -r requirements.txt

# Generate an HTML report (default)
python parser.py sample-access.log

# Generate both HTML and CSV
python parser.py sample-access.log --format both --output my-report

# Parse a real Nginx log
python parser.py /var/log/nginx/access.log --format html --output nginx-report
```

---

## Sample Output

```
── Summary ────────────────────────────────
  Total Requests : 20
  Unique IPs     : 7
  Data Transfer  : 0.02 MB
  Error Rate     : 20.0%
  Top IP         : ('192.168.1.1', 6)
───────────────────────────────────────────
```

The HTML report opens in any browser and shows a full dashboard with tables.

---

## Log Format Supported

Standard **Combined Log Format**:
```
127.0.0.1 - - [04/May/2026:10:00:01 +0530] "GET /api HTTP/1.1" 200 1420 "-" "Mozilla/5.0"
```

---

## Key Concepts Learned

- Regex-based log parsing with named capture groups
- Python `Counter` and `collections` for frequency analysis
- CLI tool design with `argparse`
- HTML report generation without external libraries
- CSV export for data portability
- Real-world SRE skill: reading logs to understand system behaviour

---

## Extend This Project

- [ ] Add time-series analysis — requests per hour chart
- [ ] Flag suspicious IPs (e.g. >1000 req/min) as potential DDoS
- [ ] Send the HTML report to an S3 bucket automatically
- [ ] Add support for JSON-format logs (modern Nginx/Fluent Bit output)
- [ ] Integrate with Grafana Loki for streaming log ingestion
