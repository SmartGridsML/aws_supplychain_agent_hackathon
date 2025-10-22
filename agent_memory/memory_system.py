"""
Agent memory and learning system - Makes agent remember and improve
"""
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

class AgentMemory:
    """Persistent memory for agent learning"""
    
    def __init__(self):
        # Create tables if they don't exist
        self.memory_table = self._get_or_create_table('AgentMemory')
        self.prediction_table = self._get_or_create_table('AgentPredictions')
        self.pattern_table = self._get_or_create_table('FlightPatterns')
    
    def _get_or_create_table(self, table_name: str):
        """Get existing table or return mock for now"""
        try:
            return dynamodb.Table(table_name)
        except:
            print(f"⚠️ Table {table_name} not found - using mock")
            return None
    
    def remember_flight_pattern(self, callsign: str, delay_minutes: int, reason: str):
        """Agent stores flight delay patterns for learning"""
        if not self.pattern_table:
            return
        
        try:
            self.pattern_table.put_item(Item={
                'flight_callsign': callsign,
                'timestamp': datetime.utcnow().isoformat(),
                'delay_minutes': Decimal(str(delay_minutes)),
                'delay_reason': reason,
                'day_of_week': datetime.utcnow().strftime('%A'),
                'month': datetime.utcnow().strftime('%B')
            })
            print(f"💾 Stored pattern for {callsign}: {delay_minutes}min delay")
        except Exception as e:
            print(f"⚠️ Could not store pattern: {e}")
    
    def recall_flight_history(self, callsign: str, days: int = 30) -> List[Dict]:
        """Agent recalls past behavior to inform current decisions"""
        if not self.pattern_table:
            return self._get_mock_history(callsign)
        
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            response = self.pattern_table.query(
                KeyConditionExpression='flight_callsign = :callsign AND timestamp > :cutoff',
                ExpressionAttributeValues={
                    ':callsign': callsign,
                    ':cutoff': cutoff_date
                }
            )
            
            return response.get('Items', [])
        except Exception as e:
            print(f"⚠️ Could not recall history: {e}")
            return self._get_mock_history(callsign)
    
    def predict_delay_probability(self, callsign: str, current_conditions: Dict) -> float:
        """Agent uses learned patterns to predict delays"""
        history = self.recall_flight_history(callsign)
        
        if not history:
            return 0.1  # Base probability
        
        # Calculate historical delay rate
        total_flights = len(history)
        delayed_flights = sum(1 for f in history if float(f.get('delay_minutes', 0)) > 30)
        base_probability = delayed_flights / total_flights if total_flights > 0 else 0.1
        
        # Adjust for current conditions
        weather_factor = 1.5 if current_conditions.get('weather') == 'SEVERE' else 1.0
        geo_factor = 1.8 if current_conditions.get('geopolitical_risk') == 'HIGH' else 1.0
        time_factor = 1.3 if datetime.utcnow().hour in [7, 8, 17, 18] else 1.0  # Rush hours
        
        adjusted_probability = base_probability * weather_factor * geo_factor * time_factor
        
        return min(adjusted_probability, 1.0)
    
    def store_autonomous_decision(self, decision: Dict):
        """Agent stores its autonomous decisions for learning"""
        if not self.memory_table:
            return
        
        try:
            self.memory_table.put_item(Item={
                'decision_id': f"{decision['callsign']}_{datetime.utcnow().isoformat()}",
                'timestamp': datetime.utcnow().isoformat(),
                'callsign': decision['callsign'],
                'decision_type': decision['type'],
                'reasoning': decision['reasoning'],
                'actions_taken': json.dumps(decision['actions']),
                'outcome': 'PENDING'
            })
            print(f"💾 Stored autonomous decision: {decision['type']}")
        except Exception as e:
            print(f"⚠️ Could not store decision: {e}")
    
    def learn_from_outcome(self, decision_id: str, actual_outcome: str, success: bool):
        """Agent learns from whether its predictions were correct"""
        if not self.memory_table:
            return
        
        try:
            self.memory_table.update_item(
                Key={'decision_id': decision_id},
                UpdateExpression='SET outcome = :outcome, success = :success, learned_at = :timestamp',
                ExpressionAttributeValues={
                    ':outcome': actual_outcome,
                    ':success': success,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            print(f"🧠 Agent learned from outcome: {'SUCCESS' if success else 'FAILURE'}")
        except Exception as e:
            print(f"⚠️ Could not update learning: {e}")
    
    def _get_mock_history(self, callsign: str) -> List[Dict]:
        """Mock historical data for testing"""
        return [
            {'delay_minutes': Decimal('45'), 'delay_reason': 'weather', 'timestamp': '2025-10-15T10:00:00'},
            {'delay_minutes': Decimal('90'), 'delay_reason': 'mechanical', 'timestamp': '2025-10-12T14:00:00'},
            {'delay_minutes': Decimal('0'), 'delay_reason': 'none', 'timestamp': '2025-10-10T09:00:00'},
        ]


def lambda_handler(event, context):
    """Lambda handler for memory operations"""
    memory = AgentMemory()
    
    operation = event.get('operation')
    
    if operation == 'remember':
        memory.remember_flight_pattern(
            callsign=event['callsign'],
            delay_minutes=event['delay_minutes'],
            reason=event['reason']
        )
        return {'status': 'REMEMBERED'}
    
    elif operation == 'recall':
        history = memory.recall_flight_history(event['callsign'])
        return {'status': 'RECALLED', 'history': history}
    
    elif operation == 'predict':
        probability = memory.predict_delay_probability(
            event['callsign'],
            event.get('conditions', {})
        )
        return {'status': 'PREDICTED', 'delay_probability': probability}
    
    else:
        return {'status': 'ERROR', 'message': 'Unknown operation'}