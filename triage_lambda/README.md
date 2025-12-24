# RentMatrix AI Triage Lambda

AWS Lambda deployment for the RentMatrix AI Triage Engine using Docker.

## 📁 Directory Structure

```
triage_lambda/
├── agent/                  # AI agent modules
│   ├── core_agents/       # Triage, Priority, Explainer, Confidence agents
│   ├── prompts/           # Agent prompts
│   ├── models/            # Data models
│   └── data/              # Mock data and utilities
├── lambda_handler.py      # AWS Lambda entry point
├── triage_processor.py    # Core triage processing logic
├── Dockerfile             # Docker configuration for Lambda
├── requirements.txt       # Python dependencies
├── env-template.txt       # Environment variables template
└── README.md             # This file
```

## 🚀 Quick Start

### 1. Setup Environment Variables

```bash
# Copy template and edit with your values
cp env-template.txt .env
```

Edit `.env` file with your actual credentials:
- Auth0 credentials (Domain, ClientId, ClientSecret, Audience)
- OpenAI or Anthropic API key
- Backend API URL

### 2. Build Docker Image

```bash
docker build -t rentmatrix-triage-lambda .
```

### 3. Test Locally

```bash
# Test with Docker
docker run -p 9000:8080 rentmatrix-triage-lambda

# In another terminal, invoke the function
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{
    "maintenanceId": "8ec5ee0b-1952-4c66-8773-55baf33faba1"
  }'
```

## ☁️ AWS Lambda Deployment

### Option 1: Using AWS ECR (Recommended)

#### Step 1: Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name rentmatrix-triage-lambda \
  --region us-west-2
```

#### Step 2: Authenticate Docker to ECR

```bash
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com
```

#### Step 3: Tag and Push Image

```bash
# Tag the image
docker tag rentmatrix-triage-lambda:latest \
  <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/rentmatrix-triage-lambda:latest

# Push to ECR
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/rentmatrix-triage-lambda:latest
```

#### Step 4: Create Lambda Function

```bash
aws lambda create-function \
  --function-name rentmatrix-triage-processor \
  --package-type Image \
  --code ImageUri=<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/rentmatrix-triage-lambda:latest \
  --role arn:aws:iam::<YOUR_AWS_ACCOUNT_ID>:role/lambda-execution-role \
  --timeout 300 \
  --memory-size 1024 \
  --region us-west-2
```

#### Step 5: Set Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name rentmatrix-triage-processor \
  --environment Variables='{
    "Auth0Management__Domain":"https://your-domain.auth0.com",
    "Auth0Management__ClientId":"your_client_id",
    "Auth0Management__ClientSecret":"your_client_secret",
    "Auth0Management__Audience":"your_audience",
    "OPENAI_API_KEY":"your_openai_key"
  }' \
  --region us-west-2
```

### Option 2: Using AWS SAM

Create `template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  TriageLambdaFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: rentmatrix-triage-processor
      PackageType: Image
      ImageUri: <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/rentmatrix-triage-lambda:latest
      Timeout: 300
      MemorySize: 1024
      Environment:
        Variables:
          Auth0Management__Domain: !Ref Auth0Domain
          Auth0Management__ClientId: !Ref Auth0ClientId
          Auth0Management__ClientSecret: !Ref Auth0ClientSecret
          Auth0Management__Audience: !Ref Auth0Audience
          OPENAI_API_KEY: !Ref OpenAIKey
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /triage
            Method: post

Parameters:
  Auth0Domain:
    Type: String
  Auth0ClientId:
    Type: String
  Auth0ClientSecret:
    Type: String
    NoEcho: true
  Auth0Audience:
    Type: String
  OpenAIKey:
    Type: String
    NoEcho: true
```

Deploy:

```bash
sam build
sam deploy --guided
```

## 📡 API Usage

### Event Format

#### Option 1: Provide maintenanceId (fetches from backend)

```json
{
  "maintenanceId": "8ec5ee0b-1952-4c66-8773-55baf33faba1"
}
```

#### Option 2: Provide full maintenanceData

```json
{
  "maintenanceData": {
    "request": {
      "requestId": "...",
      "description": "pipe cracked",
      "images": [...],
      "reportedAt": "...",
      "channel": "..."
    },
    "tenant": {...},
    "property": {...},
    "timing": {...},
    "history": {...}
  }
}
```

### Response Format

```json
{
  "dto": {
    "triage": {
      "severity": "HIGH",
      "trade": "PLUMBING",
      "reasoning": "...",
      "confidence": 0.82,
      "keyFactors": [...]
    },
    "priority": {
      "priorityScore": 89.7,
      "severity": "HIGH",
      "baseHazard": 1.5,
      "combinedHazard": 8.663,
      "appliedFactors": [...],
      "appliedInteractions": [...],
      "calculationTrace": "...",
      "confidence": 0.82
    },
    "explanation": {
      "pmExplanation": "...",
      "tenantExplanation": "..."
    },
    "confidence": {
      "confidence": 0.60,
      "routing": "PM_IMMEDIATE_REVIEW",
      "confidenceFactors": [...],
      "riskFlags": [...],
      "recommendation": "..."
    },
    "sla": {
      "tier": null,
      "responseDeadline": null,
      "resolutionDeadline": null,
      "responseHours": 0,
      "resolutionHours": 0,
      "businessHoursOnly": false,
      "vendorTier": null
    },
    "weather": {
      "temperature": 0,
      "temperatureC": 0,
      "feelsLikeF": 0,
      "feelsLikeC": 0,
      "condition": null,
      "humidity": 0,
      "windMph": 0,
      "forecast": null,
      "alerts": [],
      "isExtremeCold": false,
      "isExtremeHeat": false,
      "freezeRisk": false
    }
  }
}
```

## 🔧 Configuration

### Lambda Settings

- **Memory**: 1024 MB (recommended minimum)
- **Timeout**: 300 seconds (5 minutes)
- **Runtime**: Python 3.12
- **Architecture**: x86_64

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `Auth0Management__Domain` | Yes | Auth0 domain URL |
| `Auth0Management__ClientId` | Yes | Auth0 client ID |
| `Auth0Management__ClientSecret` | Yes | Auth0 client secret |
| `Auth0Management__Audience` | Yes | Auth0 API audience |
| `OPENAI_API_KEY` | Yes* | OpenAI API key (*or ANTHROPIC_API_KEY) |
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key (*or OPENAI_API_KEY) |

## 🧪 Testing

### Test Locally

```python
# test_lambda.py
import json
from lambda_handler import lambda_handler

event = {
    "maintenanceId": "8ec5ee0b-1952-4c66-8773-55baf33faba1"
}

result = lambda_handler(event, None)
print(json.dumps(json.loads(result["body"]), indent=2))
```

### Invoke on AWS

```bash
aws lambda invoke \
  --function-name rentmatrix-triage-processor \
  --payload '{"maintenanceId":"8ec5ee0b-1952-4c66-8773-55baf33faba1"}' \
  --region us-west-2 \
  response.json

cat response.json | jq .
```

## 📊 Monitoring

### CloudWatch Logs

```bash
aws logs tail /aws/lambda/rentmatrix-triage-processor --follow
```

### CloudWatch Metrics

- Invocations
- Duration
- Errors
- Throttles

## 🔐 Security

1. **IAM Role**: Lambda needs permissions for:
   - CloudWatch Logs (logging)
   - Secrets Manager (if storing secrets there)
   - ECR (pulling container images)

2. **API Keys**: Store sensitive keys in:
   - AWS Secrets Manager (recommended)
   - AWS Systems Manager Parameter Store
   - Lambda environment variables (encrypted)

3. **VPC**: If backend requires VPC access, configure Lambda VPC settings

## 🚨 Troubleshooting

### Issue: Timeout

- Increase Lambda timeout (max 900 seconds)
- Optimize agent processing
- Consider async processing with SQS

### Issue: Memory Error

- Increase Lambda memory (up to 10240 MB)
- Monitor CloudWatch metrics

### Issue: Cold Start

- Consider provisioned concurrency
- Optimize container image size
- Use Lambda SnapStart (if supported)

## 📝 Notes

- First invocation (cold start) may take 10-30 seconds
- Subsequent invocations are much faster (~2-5 seconds)
- Container image size should be < 10 GB
- Consider API Gateway integration for REST API

## 🔄 Updates

To update the Lambda function:

```bash
# Rebuild image
docker build -t rentmatrix-triage-lambda .

# Tag and push
docker tag rentmatrix-triage-lambda:latest \
  <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/rentmatrix-triage-lambda:latest
  
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/rentmatrix-triage-lambda:latest

# Update Lambda
aws lambda update-function-code \
  --function-name rentmatrix-triage-processor \
  --image-uri <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/rentmatrix-triage-lambda:latest \
  --region us-west-2
```

## 📞 Support

For issues or questions, refer to the main project documentation.

