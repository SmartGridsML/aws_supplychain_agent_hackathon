#!/bin/bash
# Schedule autonomous monitor to run every 5 minutes

echo "⏰ Setting up EventBridge scheduling..."

# Create rule
aws events put-rule \
    --name AutonomousMonitoringSchedule \
    --schedule-expression "rate(5 minutes)" \
    --description "Runs autonomous agent monitoring every 5 minutes" \
    --region us-east-1

# Add Lambda target
aws events put-targets \
    --rule AutonomousMonitoringSchedule \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:532923842334:function:AutonomousMonitor" \
    --region us-east-1

# Grant permission
aws lambda add-permission \
    --function-name AutonomousMonitor \
    --statement-id AllowEventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:532923842334:rule/AutonomousMonitoringSchedule \
    --region us-east-1

echo "✅ EventBridge scheduling configured"
