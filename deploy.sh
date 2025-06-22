#!/bin/bash
# deploy.sh - One command AWS deployment

set -e

echo "🚀 Starting AWS deployment..."

# Variables (UPDATE THESE)
BUCKET_NAME="nsf-ai-documents-$(date +%s)"
DB_PASSWORD="NSFSecure123!"
OPENAI_API_KEY="your-openai-api-key-here"  # UPDATE THIS
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"

echo "📦 Creating S3 bucket..."
aws s3 mb s3://$BUCKET_NAME --region $REGION

echo "🗄️  Creating RDS database..."
DB_IDENTIFIER="nsf-ai-db-$(date +%s)"
aws rds create-db-instance \
    --db-instance-identifier $DB_IDENTIFIER \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username nsfadmin \
    --master-user-password $DB_PASSWORD \
    --allocated-storage 20 \
    --publicly-accessible \
    --region $REGION

echo "⏳ Waiting for database (this takes 5-8 minutes)..."
aws rds wait db-instance-available --db-instance-identifier $DB_IDENTIFIER --region $REGION

DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_IDENTIFIER \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text \
    --region $REGION)

echo "✅ Database ready: $DB_ENDPOINT"

echo "🐳 Building and deploying container..."

# Create ECR repository
aws ecr create-repository --repository-name nsf-ai-app --region $REGION || true

# Build and tag image
docker build -t nsf-ai-app .
docker tag nsf-ai-app:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/nsf-ai-app:latest

# Push to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/nsf-ai-app:latest

echo "🚀 Creating App Runner service..."

# Create App Runner service
cat > apprunner-config.json << EOF
{
    "ServiceName": "nsf-ai-app",
    "SourceConfiguration": {
        "ImageRepository": {
            "ImageIdentifier": "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/nsf-ai-app:latest",
            "ImageConfiguration": {
                "Port": "8080",
                "RuntimeEnvironmentVariables": {
                    "DATABASE_URL": "postgresql://nsfadmin:$DB_PASSWORD@$DB_ENDPOINT:5432/postgres",
                    "SECRET_KEY": "super-secret-key-$(date +%s)",
                    "OPENAI_API_KEY": "$OPENAI_API_KEY",
                    "S3_BUCKET_NAME": "$BUCKET_NAME",
                    "AWS_REGION": "$REGION",
                    "GRAPHRAG_WORKING_DIR": "/app/nsf_graphrag_knowledge"
                }
            },
            "ImageRepositoryType": "ECR"
        },
        "AutoDeploymentsEnabled": false
    },
    "InstanceConfiguration": {
        "Cpu": "0.25 vCPU",
        "Memory": "0.5 GB"
    }
}
EOF

SERVICE_ARN=$(aws apprunner create-service --cli-input-json file://apprunner-config.json --query 'Service.ServiceArn' --output text --region $REGION)

echo "⏳ Waiting for service to be ready (2-3 minutes)..."
aws apprunner wait service-running --service-arn $SERVICE_ARN --region $REGION

SERVICE_URL=$(aws apprunner describe-service --service-arn $SERVICE_ARN --query 'Service.ServiceUrl' --output text --region $REGION)

# Clean up temp file
rm apprunner-config.json

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "================================"
echo "🌐 Your app is live at: https://$SERVICE_URL"
echo "💾 Database: $DB_ENDPOINT"
echo "📁 S3 Bucket: $BUCKET_NAME"
echo "💰 Estimated cost: ~$40/month"
echo ""
echo "Next steps:"
echo "1. Visit your app URL above"
echo "2. Login with your admin credentials"
echo "3. Upload documents and start chatting!"
echo ""
echo "To setup your admin user, you can connect to the database at:"
echo "postgresql://nsfadmin:$DB_PASSWORD@$DB_ENDPOINT:5432/postgres"