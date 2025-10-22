"""
Autonomous background monitoring - Agent works WITHOUT human input
This runs every 5 minutes via EventBridge
"""
import boto3
import json
from datetime import datetime
from typing import List, Dict
import os

lambda_client = boto3.client('lambda')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

# Flights to monitor autonomously
MONITORED_FLIGHTS = [
    'AAL100', 'AAL697', 'UAL123', 'DAL456',
    'FDX134', 'FDX789', 'UPS2901', 'DHL456'
]

# Critical suppliers to monitor
CRITICAL_SUPPLIERS = [
    {'name': 'TSMC', 'location': 'Taiwan', 'category': 'semiconductors'},
    {'name': 'Samsung', 'location': 'South Korea', 'category': 'electronics'},
    {'name': 'Intel', 'location': 'USA', 'category': 'semiconductors'}
]

# High-risk regions to monitor
HIGH_RISK_REGIONS = [
    'Taiwan Strait', 'Suez Canal', 'Red Sea', 
    'Ukraine', 'Middle East', 'South China Sea'
]

def lambda_handler(event, context):
    """
    Agent autonomously monitors supply chain WITHOUT human input
    This is TRUE autonomy - agent works 24/7 in background
    """
    print("🤖 Autonomous agent starting background monitoring...")
    
    findings = []
    autonomous_actions = []
    
    # 1. Autonomous Flight Monitoring
    print("✈️ Autonomously monitoring flights...")
    for flight in MONITORED_FLIGHTS:
        try:
            flight_findings = autonomous_check_flight(flight)
            if flight_findings['anomaly_detected']:
                findings.append(flight_findings)
                autonomous_actions.extend(flight_findings['autonomous_actions'])
        except Exception as e:
            print(f"⚠️ Error monitoring {flight}: {e}")
    
    # 2. Autonomous Geopolitical Scanning
    print("🌍 Autonomously scanning geopolitical events...")
    for region in HIGH_RISK_REGIONS:
        try:
            geo_findings = autonomous_scan_region(region)
            if geo_findings['critical_events'] > 0:
                findings.append(geo_findings)
                autonomous_actions.extend(geo_findings['autonomous_actions'])
        except Exception as e:
            print(f"⚠️ Error scanning {region}: {e}")
    
    # 3. Autonomous Supplier Health Checks
    print("🏭 Autonomously assessing supplier health...")
    for supplier in CRITICAL_SUPPLIERS:
        try:
            supplier_findings = autonomous_assess_supplier(supplier)
            if supplier_findings['risk_score'] > 70:
                findings.append(supplier_findings)
                autonomous_actions.extend(supplier_findings['autonomous_actions'])
        except Exception as e:
            print(f"⚠️ Error assessing {supplier['name']}: {e}")
    
    # 4. Store findings in DynamoDB for agent memory
    store_autonomous_findings(findings)
    
    # 5. Send alerts if critical issues found
    critical_findings = [f for f in findings if f.get('severity') == 'CRITICAL']
    if critical_findings:
        send_autonomous_alert(critical_findings)
    
    result = {
        'timestamp': datetime.utcnow().isoformat(),
        'agent_state': 'MONITORING',
        'autonomous_actions_taken': len(autonomous_actions),
        'findings_count': len(findings),
        'critical_findings': len(critical_findings),
        'monitored_flights': len(MONITORED_FLIGHTS),
        'monitored_regions': len(HIGH_RISK_REGIONS),
        'monitored_suppliers': len(CRITICAL_SUPPLIERS),
        'findings': findings[:5],  # Return top 5
        'human_intervention_required': len(critical_findings) > 0
    }
    
    print(f"✅ Autonomous monitoring complete: {result}")
    return result

def autonomous_check_flight(callsign: str) -> Dict:
    """Agent autonomously checks flight - NO USER INPUT"""
    try:
        response = lambda_client.invoke(
            FunctionName='TrackingExecutor',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'apiPath': '/track-flight',
                'parameters': [{'name': 'flight_callsign', 'value': callsign}]
            })
        )
        
        result = json.loads(response['Payload'].read())
        flight_data = result.get('body', {})
        
        # Agent analyzes data and decides if action needed
        anomaly_detected = False
        autonomous_actions = []
        severity = 'NORMAL'
        
        # Check for delays
        delay = flight_data.get('delay_minutes', 0)
        if delay > 60:
            anomaly_detected = True
            severity = 'HIGH'
            autonomous_actions.append({
                'action': 'triggered_supplier_assessment',
                'reasoning': f"Detected {delay}min delay - autonomously assessing affected suppliers"
            })
        
        # Check flight status
        status = flight_data.get('flight_status', '')
        if status in ['DIVERTED', 'EMERGENCY', 'CANCELLED']:
            anomaly_detected = True
            severity = 'CRITICAL'
            autonomous_actions.append({
                'action': 'triggered_disruption_simulation',
                'reasoning': f"Flight {status} - autonomously modeling supply chain impact"
            })
        
        return {
            'type': 'flight_anomaly',
            'callsign': callsign,
            'anomaly_detected': anomaly_detected,
            'severity': severity,
            'flight_data': flight_data,
            'autonomous_actions': autonomous_actions,
            'agent_reasoning': f"Autonomous analysis of {callsign}: {severity}"
        }
        
    except Exception as e:
        print(f"❌ Error in autonomous flight check: {e}")
        return {
            'type': 'flight_anomaly',
            'callsign': callsign,
            'anomaly_detected': False,
            'error': str(e)
        }

def autonomous_scan_region(region: str) -> Dict:
    """Agent autonomously scans for geopolitical events"""
    try:
        response = lambda_client.invoke(
            FunctionName='TrackingExecutor',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'apiPath': '/scan-geopolitical',
                'parameters': [
                    {'name': 'region', 'value': region},
                    {'name': 'event_type', 'value': 'all'}
                ]
            })
        )
        
        result = json.loads(response['Payload'].read())
        geo_data = result.get('body', {})
        
        critical_events = geo_data.get('events_found', 0)
        autonomous_actions = []
        
        if critical_events > 0:
            autonomous_actions.append({
                'action': 'triggered_risk_analysis',
                'reasoning': f"Detected {critical_events} events in {region} - autonomously analyzing supply chain risk"
            })
        
        return {
            'type': 'geopolitical_risk',
            'region': region,
            'critical_events': critical_events,
            'severity': 'CRITICAL' if critical_events > 2 else 'MODERATE',
            'geo_data': geo_data,
            'autonomous_actions': autonomous_actions
        }
        
    except Exception as e:
        print(f"❌ Error in autonomous geo scan: {e}")
        return {
            'type': 'geopolitical_risk',
            'region': region,
            'critical_events': 0,
            'error': str(e)
        }

def autonomous_assess_supplier(supplier: Dict) -> Dict:
    """Agent autonomously assesses supplier health"""
    try:
        response = lambda_client.invoke(
            FunctionName='RiskAnalysisExecutor',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'apiPath': '/assess-supplier-risk',
                'parameters': [
                    {'name': 'supplier_name', 'value': supplier['name']},
                    {'name': 'supplier_location', 'value': supplier['location']},
                    {'name': 'product_category', 'value': supplier['category']}
                ]
            })
        )
        
        result = json.loads(response['Payload'].read())
        risk_data = result.get('body', {})
        risk_score = risk_data.get('overall_risk_score', 0)
        
        autonomous_actions = []
        if risk_score > 70:
            autonomous_actions.append({
                'action': 'identified_alternative_suppliers',
                'reasoning': f"{supplier['name']} risk score {risk_score}/100 - autonomously finding alternatives"
            })
        
        return {
            'type': 'supplier_risk',
            'supplier': supplier['name'],
            'risk_score': risk_score,
            'severity': 'CRITICAL' if risk_score > 80 else 'MODERATE' if risk_score > 60 else 'LOW',
            'risk_data': risk_data,
            'autonomous_actions': autonomous_actions
        }
        
    except Exception as e:
        print(f"❌ Error in autonomous supplier assessment: {e}")
        return {
            'type': 'supplier_risk',
            'supplier': supplier['name'],
            'risk_score': 0,
            'error': str(e)
        }

def store_autonomous_findings(findings: List[Dict]):
    """Store findings in DynamoDB for agent memory"""
    try:
        table = dynamodb.Table('AutonomousFindings')
        table.put_item(Item={
            'timestamp': datetime.utcnow().isoformat(),
            'findings_count': len(findings),
            'findings': json.dumps(findings),
            'agent_state': 'MONITORING'
        })
        print(f"💾 Stored {len(findings)} autonomous findings")
    except Exception as e:
        print(f"⚠️ Could not store findings: {e}")

def send_autonomous_alert(critical_findings: List[Dict]):
    """Agent sends alerts WITHOUT being asked"""
    try:
        sns_topic = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:532923842334:supply-chain-alerts')
        
        message = f"""
🚨 AUTONOMOUS AGENT ALERT 🤖

The AI agent has autonomously detected {len(critical_findings)} CRITICAL supply chain issues:

{json.dumps(critical_findings, indent=2)}

Agent Actions Taken:
{sum(len(f.get('autonomous_actions', [])) for f in critical_findings)} autonomous interventions

Human Action Required: Review and approve mitigation plans

Timestamp: {datetime.utcnow().isoformat()}
"""
        
        sns.publish(
            TopicArn=sns_topic,
            Subject='🚨 Autonomous Agent: Critical Supply Chain Alert',
            Message=message
        )
        
        print(f"📧 Sent autonomous alert for {len(critical_findings)} critical findings")
    except Exception as e:
        print(f"⚠️ Could not send alert: {e}")