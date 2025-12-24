#!/bin/bash
# RentMatrix AI Triage Lambda - Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RentMatrix AI Triage Lambda Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo "Creating .env from template..."
    cp env-template.txt .env
    echo -e "${RED}Please edit .env with your actual credentials before continuing!${NC}"
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-west-2}
ECR_REPOSITORY="rentmatrix-triage-lambda"
LAMBDA_FUNCTION_NAME="rentmatrix-triage-processor"

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "ECR Repository: $ECR_REPOSITORY"
echo "Lambda Function: $LAMBDA_FUNCTION_NAME"
echo

# Step 1: Build Docker image
echo -e "${GREEN}Step 1: Building Docker image...${NC}"
docker build -t $ECR_REPOSITORY:latest .
echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo

# Step 2: Create ECR repository (if doesn't exist)
echo -e "${GREEN}Step 2: Creating ECR repository...${NC}"
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
echo -e "${GREEN}✓ ECR repository ready${NC}"
echo

# Step 3: Authenticate Docker to ECR
echo -e "${GREEN}Step 3: Authenticating Docker to ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
echo -e "${GREEN}✓ Docker authenticated${NC}"
echo

# Step 4: Tag and push image
echo -e "${GREEN}Step 4: Pushing image to ECR...${NC}"
docker tag $ECR_REPOSITORY:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
echo -e "${GREEN}✓ Image pushed to ECR${NC}"
echo

# Step 5: Create or update Lambda function
echo -e "${GREEN}Step 5: Deploying Lambda function...${NC}"

# Check if function exists
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest \
        --region $AWS_REGION
    
    echo "Waiting for update to complete..."
    aws lambda wait function-updated --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION
else
    echo "Creating new Lambda function..."
    echo -e "${YELLOW}Note: You need to provide an IAM role ARN${NC}"
    read -p "Enter IAM Role ARN for Lambda: " IAM_ROLE_ARN
    
    aws lambda create-function \
        --function-name $LAMBDA_FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest \
        --role $IAM_ROLE_ARN \
        --timeout 300 \
        --memory-size 1024 \
        --region $AWS_REGION
fi

echo -e "${GREEN}✓ Lambda function deployed${NC}"
echo

# Step 6: Update environment variables
echo -e "${GREEN}Step 6: Setting environment variables...${NC}"
# Load .env file and create JSON for Lambda
ENV_VARS=$(cat .env | grep -v '^#' | grep '=' | awk -F= '{print "\""$1"\":\""$2"\""}' | paste -sd, -)
aws lambda update-function-configuration \
    --function-name $LAMBDA_FUNCTION_NAME \
    --environment Variables="{$ENV_VARS}" \
    --region $AWS_REGION >/dev/null
echo -e "${GREEN}✓ Environment variables set${NC}"
echo

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "Function Name: $LAMBDA_FUNCTION_NAME"
echo "Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
echo
echo "Test your function:"
echo "  aws lambda invoke \\"
echo "    --function-name $LAMBDA_FUNCTION_NAME \\"
echo "    --payload '{\"maintenanceId\":\"8ec5ee0b-1952-4c66-8773-55baf33faba1\"}' \\"
echo "    --region $AWS_REGION \\"
echo "    response.json"
echo

