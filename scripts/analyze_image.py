#!/usr/bin/env python3
"""
analyze_image.py

Reads images from the local `images/` folder, uploads them to S3, calls Amazon Rekognition
to detect labels, and stores results in DynamoDB.
"""

import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

import boto3


IMAGES_DIR = Path("images")
S3_PREFIX = "rekognition-input"


def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def list_image_files(images_dir: Path) -> List[Path]:
    if not images_dir.exists():
        print(f"ℹ️ No '{images_dir}' folder found.")
        return []

    image_files: List[Path] = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        image_files.extend(images_dir.glob(ext))

    return sorted(image_files)


def upload_to_s3(s3_client: Any, bucket: str, file_path: Path) -> str:
    s3_key = f"{S3_PREFIX}/{file_path.name}"
    print(f"⬆️ Uploading {file_path} to s3://{bucket}/{s3_key}")
    s3_client.upload_file(str(file_path), bucket, s3_key)
    return s3_key


def detect_labels(rekognition_client: Any, bucket: str, s3_key: str) -> List[Dict[str, Any]]:
    print(f"👁️ Calling Rekognition detect_labels for s3://{bucket}/{s3_key}")

    response = rekognition_client.detect_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": s3_key}},
        MaxLabels=10,
        MinConfidence=70,  # int (not float)
    )

    labels: List[Dict[str, Any]] = []
    for label in response.get("Labels", []):
        labels.append(
            {
                "Name": label.get("Name", "Unknown"),
                "Confidence": Decimal(str(label.get("Confidence", 0.0))),
            }
        )

    return labels


def convert_floats_to_decimal(value: Any) -> Any:
    # DynamoDB (boto3) does not support float. Convert all floats recursively.
    if isinstance(value, float):
        return Decimal(str(value))

    if isinstance(value, list):
        return [convert_floats_to_decimal(v) for v in value]

    if isinstance(value, dict):
        return {k: convert_floats_to_decimal(v) for k, v in value.items()}

    return value


def write_to_dynamodb(
    dynamodb_table: Any,
    s3_key: str,
    labels: List[Dict[str, Any]],
    timestamp: str,
    branch: str,
) -> None:
    item = {
        "filename": s3_key,
        "labels": labels,
        "timestamp": timestamp,
        "branch": branch,
    }

    safe_item = convert_floats_to_decimal(item)

    print(f"🧾 Writing results to DynamoDB for {s3_key}")
    dynamodb_table.put_item(Item=safe_item)


def main() -> None:
    aws_region = get_env_var("AWS_REGION")
    s3_bucket = get_env_var("S3_BUCKET")
    dynamodb_table_name = get_env_var("DYNAMODB_TABLE")
    branch_name = os.getenv("BRANCH_NAME", "unknown")

    print("✅ Starting Rekognition image analysis")
    print(f"Region: {aws_region}")
    print(f"Bucket: {s3_bucket}")
    print(f"DynamoDB Table: {dynamodb_table_name}")
    print(f"Branch: {branch_name}")

    session = boto3.session.Session(region_name=aws_region)
    s3_client = session.client("s3")
    rekognition_client = session.client("rekognition")
    dynamodb = session.resource("dynamodb").Table(dynamodb_table_name)

    images = list_image_files(IMAGES_DIR)
    if not images:
        print("ℹ️ No images found. Exiting.")
        return

    for image in images:
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        try:
            s3_key = upload_to_s3(s3_client, s3_bucket, image)
            labels = detect_labels(rekognition_client, s3_bucket, s3_key)
            write_to_dynamodb(dynamodb, s3_key, labels, timestamp, branch_name)

            print("✅ Success")
            print(
                json.dumps(
                    {
                        "filename": s3_key,
                        "labels": labels,
                        "timestamp": timestamp,
                        "branch": branch_name,
                    },
                    indent=2,
                    default=str,
                )
            )

        except Exception as exc:
            print(f"❌ Failed processing {image.name}: {exc}")


if __name__ == "__main__":
    main()
