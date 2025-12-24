# Quick Start Guide - RentMatrix AI Triage Lambda

## 🚀 5-Minute Setup

### Prerequisites
- Docker installed
- AWS CLI configured
- AWS account with Lambda and ECR permissions

### Step 1: Setup Environment (2 minutes)

```bash
cd triage_lambda

# Copy environment template
cp env-template.txt .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

Required credentials:
- Auth0 credentials
- OpenAI or Anthropic API key

### Step 2: Build Docker Image (1 minute)

```bash
docker build -t rentmatrix-triage-lambda .
```

### Step 3: Test Locally (1 minute)

```bash
# Option 1: Test with sample data
python test_local.py data

# Option 2: Test with maintenanceId (requires backend access)
python test_local.py
```

### Step 4: Deploy to AWS Lambda (1 minute)

**Option A: Automated Script (Linux/Mac)**

```bash
chmod +x deploy.sh
./deploy.sh
```

**Option B: Manual Steps (Windows/Linux/Mac)**

```bash
# Set your AWS account ID and region
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=us-west-2

# Create ECR repository
aws ecr create-repository --repository-name rentmatrix-triage-lambda --region $AWS_REGION

# Authenticate Docker
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push
docker tag rentmatrix-triage-lambda:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/rentmatrix-triage-lambda:latest

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/rentmatrix-triage-lambda:latest

# Create Lambda function
aws lambda create-function \
  --function-name rentmatrix-triage-processor \
  --package-type Image \
  --code ImageUri=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/rentmatrix-triage-lambda:latest \
  --role arn:aws:iam::$AWS_ACCOUNT_ID:role/your-lambda-role \
  --timeout 300 \
  --memory-size 1024 \
  --region $AWS_REGION
```

## ✅ Verify Deployment

```bash
# Invoke the function
aws lambda invoke \
  --function-name rentmatrix-triage-processor \
  --payload '{"maintenanceId":"8ec5ee0b-1952-4c66-8773-55baf33faba1"}' \
  --region us-west-2 \
  response.json

# View response
cat response.json | jq .
```

## 🎯 Expected Response

```json
{
  "dto": {
    "triage": {
      "severity": "HIGH",
      "trade": "PLUMBING",
      ...
    },
    "priority": {
      "priorityScore": 89.7,
      ...
    },
    "explanation": {...},
    "confidence": {...},
    "sla": {...},
    "weather": {...}
  }
}
```

## 🔄 Updates

To update after code changes:

```bash
# Rebuild and push
docker build -t rentmatrix-triage-lambda .
docker tag rentmatrix-triage-lambda:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/rentmatrix-triage-lambda:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/rentmatrix-triage-lambda:latest

# Update Lambda
aws lambda update-function-code \
  --function-name rentmatrix-triage-processor \
  --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/rentmatrix-triage-lambda:latest \
  --region us-west-2
```

## 🆘 Troubleshooting

### Issue: Docker build fails
- Check Docker is running
- Ensure all files are present
- Check requirements.txt dependencies

### Issue: Lambda timeout
- Increase timeout: `--timeout 600`
- Increase memory: `--memory-size 2048`

### Issue: Environment variables not set
```bash
aws lambda update-function-configuration \
  --function-name rentmatrix-triage-processor \
  --environment Variables='{...}' \
  --region us-west-2
```

## 📚 Next Steps

- See [README.md](README.md) for detailed documentation
- Configure API Gateway for REST API
- Set up CloudWatch alarms
- Implement CI/CD pipeline

## 🎉 You're Done!

Your Lambda function is now running and ready to process triage requests!

