"""
Autonomous multi-tool orchestrator - Makes agent truly intelligent
This is the brain that chains multiple tools together based on reasoning
"""
import boto3
import json
from datetime import datetime
from typing import List, Dict, Any
import traceback

lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')

class AutonomousOrchestrator:
    """Agent that autonomously decides which tools to call and in what order"""
    
    def __init__(self):
        self.reasoning_chain = []
        self.actions_taken = []
        self.memory_table = dynamodb.Table('AgentMemory')
    
    def autonomous_analyze_flight(self, callsign: str) -> Dict[str, Any]:
        """
        Agent autonomously chains actions based on flight analysis
        This is TRUE agentic AI - multi-step reasoning without human input
        """
        print(f"🤖 Agent autonomously analyzing {callsign}...")
        
        try:
            # STEP 1: Track flight (primary action)
            flight_data = self._call_tracking_tool('trackFlight', {
                'flight_callsign': callsign
            })
            self.reasoning_chain.append({
                'step': 1,
                'action': 'track_flight',
                'reasoning': f"Tracked {callsign} to assess current status",
                'result': flight_data.get('flight_status', 'UNKNOWN')
            })
            
            # STEP 2: Agent AUTONOMOUSLY DECIDES if geopolitical scan needed
            if self._should_check_geopolitical(flight_data):
                region = flight_data.get('origin_country', 'Unknown Region')
                self.reasoning_chain.append({
                    'step': 2,
                    'action': 'autonomous_decision',
                    'reasoning': f"Flight in high-risk region ({region}) → autonomously scanning geopolitical events",
                    'autonomous': True
                })
                
                geo_risks = self._call_tracking_tool('scanGeopolitical', {
                    'region': region,
                    'event_type': 'all'
                })
                
                self.actions_taken.append({
                    'tool': 'scanGeopolitical',
                    'autonomous': True,
                    'reasoning': 'Proactive geopolitical risk assessment',
                    'result': geo_risks
                })
                
                # STEP 3: If high risk, autonomously simulate disruption
                if geo_risks.get('critical_events', 0) > 0:
                    self.reasoning_chain.append({
                        'step': 3,
                        'action': 'autonomous_decision',
                        'reasoning': 'Critical geopolitical event detected → autonomously simulating disruption impact',
                        'autonomous': True
                    })
                    
                    disruption = self._call_risk_tool('simulateDisruption', {
                        'disruption_type': 'airspace_closure',
                        'location': region,
                        'duration_days': '7',
                        'severity': 'major'
                    })
                    
                    self.actions_taken.append({
                        'tool': 'simulateDisruption',
                        'autonomous': True,
                        'reasoning': 'Modeling worst-case scenario impact',
                        'result': disruption
                    })
            
            # STEP 4: Check for delays and autonomously assess impact
            if self._has_significant_delay(flight_data):
                delay_minutes = flight_data.get('delay_minutes', 0)
                self.reasoning_chain.append({
                    'step': 4,
                    'action': 'autonomous_decision',
                    'reasoning': f"Detected {delay_minutes}min delay → autonomously assessing supply chain impact",
                    'autonomous': True
                })
                
                # Autonomously assess affected suppliers
                suppliers = self._get_likely_suppliers(callsign)
                for supplier in suppliers:
                    supplier_risk = self._call_risk_tool('assessSupplierRisk', {
                        'supplier_name': supplier['name'],
                        'supplier_location': supplier['location'],
                        'product_category': supplier['category']
                    })
                    
                    self.actions_taken.append({
                        'tool': 'assessSupplierRisk',
                        'autonomous': True,
                        'reasoning': f"Proactive supplier risk check: {supplier['name']}",
                        'result': supplier_risk
                    })
            
            # STEP 5: Store learning for future decisions
            self._store_autonomous_learning(callsign, flight_data, self.actions_taken)
            
            return {
                'status': 'SUCCESS',
                'flight_status': flight_data,
                'autonomous_actions_count': len(self.actions_taken),
                'reasoning_chain': self.reasoning_chain,
                'actions_taken': self.actions_taken,
                'agent_decision_depth': len(self.reasoning_chain),
                'human_intervention_required': False,
                'agent_intelligence_score': self._calculate_intelligence_score()
            }
            
        except Exception as e:
            print(f"❌ Error in autonomous orchestration: {str(e)}\n{traceback.format_exc()}")
            return {
                'status': 'ERROR',
                'error': str(e),
                'reasoning_chain': self.reasoning_chain
            }
    
    def _call_tracking_tool(self, function_name: str, params: Dict) -> Dict:
        """Agent autonomously calls tracking tools"""
        payload = {
            'apiPath': f"/{function_name.replace('track', 'track-').replace('scan', 'scan-').lower()}",
            'parameters': [{'name': k, 'value': v} for k, v in params.items()]
        }
        
        response = lambda_client.invoke(
            FunctionName='TrackingExecutor',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        return result.get('body', {})
    
    def _call_risk_tool(self, function_name: str, params: Dict) -> Dict:
        """Agent autonomously calls risk analysis tools"""
        payload = {
            'apiPath': f"/{function_name[0].lower() + function_name[1:].replace('Risk', '-risk').replace('Disruption', '-disruption')}",
            'parameters': [{'name': k, 'value': v} for k, v in params.items()]
        }
        
        response = lambda_client.invoke(
            FunctionName='RiskAnalysisExecutor',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        return result.get('body', {})
    
    def _should_check_geopolitical(self, flight_data: Dict) -> bool:
        """Agent decides if geopolitical scan is needed"""
        high_risk_regions = [
            'Taiwan', 'Ukraine', 'Russia', 'Middle East', 
            'Israel', 'Palestine', 'Yemen', 'Red Sea', 'Iran'
        ]
        
        origin = flight_data.get('origin_country', '').lower()
        route = flight_data.get('route', '').lower()
        
        return any(region.lower() in origin or region.lower() in route 
                   for region in high_risk_regions)
    
    def _has_significant_delay(self, flight_data: Dict) -> bool:
        """Agent decides if delay is significant enough to act"""
        delay = flight_data.get('delay_minutes', 0)
        status = flight_data.get('flight_status', '')
        
        return delay > 60 or status in ['DELAYED', 'DIVERTED', 'CANCELLED']
    
    def _get_likely_suppliers(self, callsign: str) -> List[Dict]:
        """Agent predicts likely suppliers based on flight"""
        # In production, this would query a database
        # For now, return likely suppliers based on carrier
        carrier_map = {
            'FDX': [
                {'name': 'TSMC', 'location': 'Taiwan', 'category': 'semiconductors'},
                {'name': 'Foxconn', 'location': 'China', 'category': 'electronics'}
            ],
            'UPS': [
                {'name': 'Intel', 'location': 'USA', 'category': 'semiconductors'},
                {'name': 'Apple', 'location': 'China', 'category': 'electronics'}
            ],
            'AAL': [
                {'name': 'Boeing', 'location': 'USA', 'category': 'aerospace'},
                {'name': 'GE Aviation', 'location': 'USA', 'category': 'aerospace'}
            ]
        }
        
        carrier_code = callsign[:3].upper()
        return carrier_map.get(carrier_code, [
            {'name': 'Generic Supplier', 'location': 'Unknown', 'category': 'general'}
        ])
    
    def _store_autonomous_learning(self, callsign: str, flight_data: Dict, actions: List):
        """Agent stores decisions for future learning"""
        try:
            self.memory_table.put_item(Item={
                'decision_id': f"{callsign}_{datetime.utcnow().isoformat()}",
                'timestamp': datetime.utcnow().isoformat(),
                'callsign': callsign,
                'flight_status': json.dumps(flight_data),
                'autonomous_actions': json.dumps(actions),
                'action_count': len(actions),
                'reasoning_depth': len(self.reasoning_chain)
            })
        except Exception as e:
            print(f"⚠️ Could not store learning: {e}")
    
    def _calculate_intelligence_score(self) -> int:
        """Calculate agent's intelligence based on autonomous actions"""
        base_score = 50
        action_bonus = len(self.actions_taken) * 10
        reasoning_bonus = len(self.reasoning_chain) * 5
        
        return min(base_score + action_bonus + reasoning_bonus, 100)


def lambda_handler(event, context):
    """
    Lambda handler for autonomous orchestration
    This gets invoked when agent needs multi-step reasoning
    """
    print(f"📥 Autonomous orchestrator invoked: {json.dumps(event)}")
    
    try:
        orchestrator = AutonomousOrchestrator()
        
        # Extract parameters from Bedrock Agent format
        request_body = event.get('requestBody', {}).get('content', {}).get('application/json', {})
        properties = request_body.get('properties', [])
        callsign = next((p['value'] for p in properties if p['name'] == 'flight_callsign'), None)
        
        if not callsign:
            return {
                'messageVersion': '1.0',
                'response': {
                    'actionGroup': event.get('actionGroup'),
                    'apiPath': event.get('apiPath'),
                    'httpMethod': event.get('httpMethod'),
                    'httpStatusCode': 400,
                    'responseBody': {
                        'application/json': {
                            'body': json.dumps({'error': 'flight_callsign parameter required'})
                        }
                    }
                }
            }
        
        result = orchestrator.autonomous_analyze_flight(callsign)
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup'),
                'apiPath': event.get('apiPath'),
                'httpMethod': event.get('httpMethod'),
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
        
    except Exception as e:
        print(f"❌ Error in orchestrator handler: {str(e)}\n{traceback.format_exc()}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup'),
                'apiPath': event.get('apiPath'),
                'httpMethod': event.get('httpMethod'),
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
        }