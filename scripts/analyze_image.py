#!/usr/bin/env python3
"""
analyze_image.py

Reads images from the local `images/` folder, uploads them to S3, calls Amazon Rekognition
to detect labels, and stores results in DynamoDB.

Required environment variables:
- AWS_REGION
- S3_BUCKET
- DYNAMODB_TABLE
- BRANCH_NAME (set by GitHub Actions; default: "unknown")
"""

import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

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
    return sorted(image_files)


def upload_to_s3(s3_client: Any, bucket: str, file_path: Path) -> str:
    # Build the S3 ke

