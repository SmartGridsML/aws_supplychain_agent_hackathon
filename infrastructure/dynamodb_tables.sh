#!/bin/bash
# Create DynamoDB tables for agent memory

echo "📊 Creating DynamoDB tables..."

# AgentMemory table
aws dynamodb create-table \
    --table-name AgentMemory \
    --attribute-definitions \
        AttributeName=decision_id,AttributeType=S \
    --key-schema \
        AttributeName=decision_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# FlightPatterns table
aws dynamodb create-table \
    --table-name FlightPatterns \
    --attribute-definitions \
        AttributeName=flight_callsign,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=flight_callsign,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# AutonomousFindings table
aws dynamodb create-table \
    --table-name AutonomousFindings \
    --attribute-definitions \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=timestamp,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

echo "✅ DynamoDB tables created"
