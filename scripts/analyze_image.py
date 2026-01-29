#!/usr/bin/env python3
"""
analyze_image.py

Reads images from the local `images/` folder, uploads them to S3, calls Amazon Rekognition
to detect labels, and stores results in DynamoDB.

Required environment variables:
- AWS_REGION
- S3_BUCKET
- DYNAMODB_TABLE
- BRANCH_NAME (set by GitHub Actions)
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import boto3


# Folder in the repo that contains images to analyze
IMAGES_DIR = Path("images")

# Prefix inside S3 bucket to keep inputs organized
S3_PREFIX = "rekognition-input"


def get_env_var(name: str) -> str:
    # Fail fast with a clear message when env vars are missing
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def list_image_files(images_dir: Path) -> List[Path]:
    # Find .jpg, .jpeg, and .png files
    if not images_dir.exists():
        print(f"ℹ️ No '{images_dir}' folder found. Nothing to analyze.")
        return []

    image_files: List[Path] = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        image_files.extend(images_dir.glob(ext))

    # Sort for stable output
    image_files = sorted(image_files)
    return image_files


def upload_to_s3(s3_client: Any, bucket: str, file_path: Path) -> str:
    # Build the S3 key: rekognition-input/<filename>
    s3_key = f"{S3_PREFIX}/{file_path.name}"

    print(f"⬆️ Uploading {file_path} to s3://{bucket}/{s3_key}")
    s3_client.upload_file(str(file_path), bucket, s3_key)

    return s3_key


def detect_labels(rekognition_client: Any, bucket: str, s3_key: str) -> List[Dict[str, float]]:
    print(f"👁️ Calling Rekognition detect_labels for s3://{bucket}/{s3_key}")

    response = rekognition_client.detect_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": s3_key}},
        MaxLabels=10,
        MinConfidence=70.0,
    )

    labels_out: List[Dict[str, float]] = []
    for label in response.get("Labels", []):
        labels_out.append(
            {
                "Name": label.get("Name", "Unknown"),
                "Confidence": float(label.get("Confidence", 0.0)),
            }
        )

    return labels_out


def write_to_dynamodb(
    dynamodb_table: Any,
    s3_key: str,
    labels: List[Dict[str, float]],
    timestamp: str,
    branch: str,
) -> None:
    item = {
        # Partition key for your table
        "filename": s3_key,
        "labels": labels,
        "timestamp": timestamp,
        "branch": branch,
    }

    print(f"🧾 Writing results to DynamoDB for {s3_key}")
    dynamodb_table.put_item(Item=item)


def main() -> None:
    # Load configuration from env vars
    aws_region = get_env_var("AWS_REGION")
    s3_bucket = get_env_var("S3_BUCKET")
    dynamodb_table_name = get_env_var("DYNAMODB_TABLE")

    # Branch name is helpful metadata; default to "unknown" if not provided
    branch_name = os.getenv("BRANCH_NAME", "unknown")

    # Timestamp in ISO 8601 UTC
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    print("✅ Starting Rekognition image analysis job")
    print(f"   Region: {aws_region}")
    print(f"   Bucket: {s3_bucket}")
    print(f"   DynamoDB table: {dynamodb_table_name}")
    print(f"   Branch: {branch_name}")

    # Create AWS clients
    session = boto3.session.Session(region_name=aws_region)
    s3_client = session.client("s3")
    rekognition_client = session.client("rekognition")

    dynamodb_resource = session.resource("dynamodb")
    dynamodb_table = dynamodb_resource.Table(dynamodb_table_name)

    # Locate images
    image_files = list_image_files(IMAGES_DIR)
    if not image_files:
        print("ℹ️ No images found in 'images/'. Add a .jpg/.png file and rerun.")
        return

    for image_path in image_files:
        try:
            # Upload to S3
            s3_key = upload_to_s3(s3_client, s3_bucket, image_path)

            # Rekognition analysis
            labels = detect_labels(rekognition_client, s3_bucket, s3_key)

            # Write to DynamoDB
            write_to_dynamodb(dynamodb_table, s3_key, labels, timestamp, branch_name)

            # Print a nice summary
            print("✅ Success!")
            print(json.dumps(
                {
                    "filename": s3_key,
                    "labels": labels,
                    "timestamp": timestamp,
                    "branch": branch_name,
                },
                indent=2
            ))

        except Exception as exc:
            print(f"❌ Failed processing {image_path.name}: {exc}")
            # Continue to next image instead of failing the entire run
            continue


if __name__ == "__main__":
    main()
