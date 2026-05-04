"""
AWS S3 Backup Automator
========================
Compresses a local directory into a timestamped zip archive
and uploads it to an AWS S3 bucket. Sends a Slack notification
on success or failure.

Author  : Devesh Raj (github.com/devish2)
Repo    : devish2/Python-Scripts
Concept : Cloud Automation & Backup Strategies (DevOps Core Skill)
"""

import os
import sys
import zipfile
import logging
import argparse
import json
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

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
        logging.FileHandler("backup.log"),
    ],
)
log = logging.getLogger(__name__)


# ── Config ─────────────────────────────────────────────────────────────────────
def load_config(path=".env"):
    """Load config from environment variables (12-factor app style)."""
    return {
        "aws": {
            "bucket_name": os.getenv("AWS_S3_BUCKET", ""),
            "region": os.getenv("AWS_REGION", "ap-south-1"),
            "prefix": os.getenv("AWS_S3_PREFIX", "backups"),
        },
        "slack": {
            "enabled": os.getenv("SLACK_ENABLED", "false").lower() == "true",
            "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
        },
        "backup": {
            "retention_days": int(os.getenv("BACKUP_RETENTION_DAYS", 30)),
        },
    }


# ── Compression ────────────────────────────────────────────────────────────────
def create_zip_archive(source_dir, output_dir="/tmp"):
    """
    Zip the source directory into a timestamped archive.
    Returns the path to the created zip file.
    """
    source_path = Path(source_dir).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{source_path.name}_{timestamp}.zip"
    archive_path = Path(output_dir) / archive_name

    log.info(f"Creating archive: {archive_path}")
    file_count = 0

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(source_path.parent)
                zf.write(file_path, arcname)
                file_count += 1

    archive_size_mb = round(archive_path.stat().st_size / (1024 * 1024), 2)
    log.info(f"Archive created: {file_count} files, {archive_size_mb} MB")

    return archive_path, file_count, archive_size_mb


# ── S3 Upload ──────────────────────────────────────────────────────────────────
def upload_to_s3(archive_path, bucket_name, prefix, region):
    """
    Upload the archive to S3.
    Uses IAM role credentials automatically if running on EC2/ECS.
    Falls back to AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY env vars.
    """
    s3 = boto3.client("s3", region_name=region)
    today = datetime.now().strftime("%Y/%m/%d")
    s3_key = f"{prefix}/{today}/{archive_path.name}"

    log.info(f"Uploading to s3://{bucket_name}/{s3_key}")

    try:
        s3.upload_file(
            str(archive_path),
            bucket_name,
            s3_key,
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        log.info(f"Upload complete: {s3_uri}")
        return s3_uri
    except (BotoCoreError, ClientError) as e:
        log.error(f"S3 upload failed: {e}")
        raise


# ── Slack Notification ─────────────────────────────────────────────────────────
def send_slack_notification(webhook_url, success, details):
    """Send a Slack message summarising the backup result."""
    if not SLACK_AVAILABLE or not webhook_url:
        log.warning("Slack notification skipped (not configured).")
        return

    icon = "✅" if success else "❌"
    status = "succeeded" if success else "FAILED"
    color = "#2eb886" if success else "#e74c3c"

    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{icon} *S3 Backup {status.upper()}*\n{details}",
                        },
                    }
                ],
            }
        ]
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        log.info("Slack notification sent.")
    except Exception as e:
        log.error(f"Slack notification failed: {e}")


# ── Cleanup ────────────────────────────────────────────────────────────────────
def cleanup_local_archive(archive_path):
    """Remove the local zip archive after upload."""
    try:
        Path(archive_path).unlink()
        log.info(f"Local archive removed: {archive_path}")
    except Exception as e:
        log.warning(f"Could not remove local archive: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Backup a local directory to AWS S3 with Slack notification."
    )
    parser.add_argument("source_dir", help="Path to the directory to back up")
    parser.add_argument(
        "--temp-dir", default="/tmp",
        help="Directory to store the temp zip archive (default: /tmp)"
    )
    parser.add_argument(
        "--keep-local", action="store_true",
        help="Keep the local zip archive after upload (default: delete)"
    )
    args = parser.parse_args()

    config = load_config()

    if not config["aws"]["bucket_name"]:
        log.error("AWS_S3_BUCKET environment variable is not set.")
        sys.exit(1)

    archive_path = None
    try:
        # Step 1: Compress
        archive_path, file_count, size_mb = create_zip_archive(
            args.source_dir, args.temp_dir
        )

        # Step 2: Upload
        s3_uri = upload_to_s3(
            archive_path,
            config["aws"]["bucket_name"],
            config["aws"]["prefix"],
            config["aws"]["region"],
        )

        # Step 3: Notify
        details = (
            f"Source: `{args.source_dir}`\n"
            f"Files: {file_count} | Size: {size_mb} MB\n"
            f"Destination: `{s3_uri}`"
        )
        send_slack_notification(
            config["slack"]["webhook_url"], success=True, details=details
        )

        print(f"\n✅ Backup complete → {s3_uri}\n")

    except Exception as e:
        details = f"Source: `{args.source_dir}`\nError: `{e}`"
        send_slack_notification(
            config["slack"]["webhook_url"], success=False, details=details
        )
        log.error(f"Backup failed: {e}")
        sys.exit(1)

    finally:
        if archive_path and not args.keep_local:
            cleanup_local_archive(archive_path)


if __name__ == "__main__":
    main()
