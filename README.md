# Automated Image Recognition CI/CD Pipeline (AWS Rekognition)

Serverless image analysis using Amazon Rekognition, S3, DynamoDB, Python, and GitHub Actions

This repository demonstrates a production-style CI/CD pipeline that automatically analyzes image files using Amazon Rekognition and stores structured results in environment-specific DynamoDB tables, triggered entirely through GitHub Actions.

The project showcases how AI services can be embedded directly into modern DevOps workflows without managing servers or training machine learning models.

---

## 🔍 Key Skills Demonstrated

- AWS Rekognition (Computer Vision / AI Services)
- GitHub Actions (CI/CD Automation)
- Python (boto3, automation scripting)
- Amazon S3 (object storage)
- Amazon DynamoDB (NoSQL data modeling)
- IAM & Secrets Management
- Branch-aware deployment strategies
- Serverless architecture design

---

## 🧠 Use Case Overview

Pixel Learning Co., a digital-first education platform, maintains a growing library of educational images. Manual tagging and review became inefficient and inconsistent across environments.

This solution integrates AI-powered image labeling directly into the CI/CD pipeline, enabling automatic classification, environment separation, and auditability.

---

## 🎯 What This Pipeline Does

- Automatically detects image changes in a GitHub repository
- Uploads images to Amazon S3
- Analyzes images using Amazon Rekognition `detect_labels`
- Stores structured label data in DynamoDB
- Separates results by environment:
  - Pull Requests → Beta
  - Main Branch → Production
- Runs fully serverless using managed AWS services

---

## 🧰 Technology Stack

| Category        | Tools               |
|----------------|---------------------|
| Cloud Platform  | AWS                 |
| AI / ML Service | Amazon Rekognition  |
| CI/CD           | GitHub Actions      |
| Language        | Python              |
| Storage         | Amazon S3           |
| Database        | Amazon DynamoDB     |
| Security        | IAM, GitHub Secrets |

---

## 📁 Repository Structure

    rekognition-image-labeling-pipeline/
    │
    ├── images/                    # Images to analyze
    │
    ├── scripts/
    │   └── analyze_image.py       # Python Rekognition + DynamoDB logic
    │
    ├── .github/workflows/
    │   ├── on_pull_request.yml    # CI workflow (beta)
    │   └── on_merge.yml           # CI workflow (production)
    │
    └── README.md

---

## ⚙️ Required AWS Resources

### Amazon S3

Stores uploaded image files.

Images stored under:

    rekognition-input/<filename>

### Amazon DynamoDB

Two tables used for environment separation:

| Table Name   | Purpose               |
|--------------|-----------------------|
| beta_results | Pull request analysis |
| prod_results | Production analysis   |

Partition Key: `filename` (String)

---

## 🔐 Secure Credential Management

All AWS credentials and configuration values are stored using GitHub Actions Secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET`
- `DYNAMODB_TABLE_BETA`
- `DYNAMODB_TABLE_PROD`

⚠️ No credentials or environment values are hardcoded.

---

## 🤖 CI/CD Workflow Behavior

### Pull Request Workflow

- Trigger: PR targeting `main`
- Executes image analysis
- Writes results to `beta_results` DynamoDB table

### Merge Workflow

- Trigger: Push to `main`
- Executes the same analysis logic
- Writes results to `prod_results` DynamoDB table

---

## 🖼️ Example Output (DynamoDB Record)

    {
      "filename": "rekognition-input/image123.jpg",
      "labels": [
        { "Name": "Balloon", "Confidence": 98.49 },
        { "Name": "Aircraft", "Confidence": 98.46 }
      ],
      "timestamp": "2025-06-01T14:55:32Z",
      "branch": "feature-branch"
    }

---

## ✅ How to Test the Pipeline

1. Add a `.jpg` or `.png` file to the `images/` directory
2. Commit and push a feature branch
3. Open a Pull Request to `main`
4. Verify GitHub Actions workflow success
5. Confirm results in `beta_results` DynamoDB table
6. Merge PR to log results to `prod_results`

---

## 🚀 Why This Project Matters

This project demonstrates:

- Practical AI integration using managed AWS services
- CI/CD pipelines beyond traditional application builds
- Secure, environment-aware automation
- Real-world DevOps and Cloud Engineering patterns

It reflects how modern teams can operationalize AI without ML infrastructure overhead.
