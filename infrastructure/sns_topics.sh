#!/bin/bash
# Create SNS topics for autonomous alerts

echo "📧 Creating SNS topics..."

aws sns create-topic \
    --name supply-chain-alerts \
    --region us-east-1

# Subscribe email (replace with your email)
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:532923842334:supply-chain-alerts \
    --protocol email \
    --notification-endpoint your-email@example.com \
    --region us-east-1

echo "✅ SNS topics created (check email for confirmation)"