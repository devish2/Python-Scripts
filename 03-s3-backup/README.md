# 03 — AWS S3 Backup Automator

> **DevOps Concept:** Cloud Automation & Backup Strategies

A production-style Python script that compresses a local directory into a **timestamped zip archive** and uploads it securely to an **AWS S3 bucket**. Sends a Slack notification on success or failure. Designed to be IAM-role friendly — no hardcoded credentials needed on EC2.

---

## What It Does

1. Takes a local source directory as input
2. Creates a `.zip` archive with timestamp in the name: `myapp_20260504_183000.zip`
3. Uploads to S3 with a date-partitioned key: `backups/2026/05/04/myapp_20260504_183000.zip`
4. Enables server-side encryption (AES256) on the S3 object
5. Sends a Slack message with backup summary (files, size, S3 URI)
6. Cleans up the local temp archive

---

## Project Structure

```
03-s3-backup/
├── backup.py             # Main script
├── .env.example          # Environment variable template
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Setup & Run

```bash
cd Python-Scripts/03-s3-backup
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your bucket name, region, and Slack webhook

# Export env vars
export $(grep -v '^#' .env | xargs)

# Run backup
python backup.py /path/to/your/app-data

# Keep local zip (skip cleanup)
python backup.py /path/to/app-data --keep-local

# Custom temp directory
python backup.py /path/to/app-data --temp-dir /var/backups
```

---

## AWS IAM Policy Required

Attach this policy to your IAM user or EC2 role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::your-backup-bucket-name",
        "arn:aws:s3:::your-backup-bucket-name/*"
      ]
    }
  ]
}
```

> On EC2 with an attached IAM role, no `AWS_ACCESS_KEY_ID` is needed. `boto3` picks up credentials automatically.

---

## Automate with Cron

```bash
# Daily backup at 2 AM
0 2 * * * cd /home/ubuntu/Python-Scripts/03-s3-backup && python backup.py /var/www/myapp
```

---

## Sample Slack Notification

```
✅ S3 Backup SUCCEEDED
Source: `/var/www/myapp`
Files: 142 | Size: 8.4 MB
Destination: `s3://my-backup-bucket/backups/2026/05/04/myapp_20260504_020005.zip`
```

---

## Key Concepts Learned

- AWS `boto3` for S3 operations
- IAM role-based authentication (best practice — no hardcoded keys)
- Python `zipfile` for compression
- S3 server-side encryption
- Date-partitioned S3 key structure (Hive-style partitioning)
- 12-factor app config via environment variables
- Cron-based automation

---

## Extend This Project

- [ ] Add S3 lifecycle policy to auto-delete backups older than 30 days
- [ ] Support multiple source directories in a single run
- [ ] Add a `--dry-run` flag to preview what would be backed up
- [ ] Use S3 Glacier for cold storage of old backups (cost optimization)
- [ ] Dockerize and deploy as a Kubernetes CronJob
- [ ] Add backup verification: download and checksum comparison
