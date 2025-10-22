# Enhanced tracking_executor.py - Robust API integration
import json
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import traceback
import sys
import time
from decimal import Decimal
import re

# API Configuration
AVIATIONSTACK_API_KEY = os.environ.get('AVIATIONSTACK_API_KEY', '')
AISSTREAM_API_KEY = os.environ.get('AISSTREAM_API_KEY', '')
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def success_response(api_path: str, body_data: Dict, status_code: int = 200) -> Dict:
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'TrackingActionGroup',
            'apiPath': api_path,
            'httpMethod': 'POST',
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(body_data, cls=DecimalEncoder)
                }
            }
        }
    }

def error_response(error_message: str, api_path: str = '', status_code: int = 500) -> Dict:
    print(f"ERROR for {api_path}: {error_message}")
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'TrackingActionGroup',
            'apiPath': api_path,
            'httpMethod': 'POST',
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({
                        'status': 'ERROR',
                        'error': error_message,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
            }
        }
    }

# Enhanced Flight Tracking with Multiple APIs
def track_flight_enhanced(flight_callsign: str) -> Dict:
    """Enhanced flight tracking with multiple API fallbacks"""
    api_path = '/track-flight'
    print(f"✈️ Enhanced tracking for: {flight_callsign}")
    
    # Try multiple APIs in order of preference
    apis = [
        ('AviationStack', track_flight_aviationstack),
        ('OpenSky', track_flight_opensky),
        ('FlightAware', track_flight_flightaware_fallback),
        ('Demo', get_demo_flight_data)
    ]
    
    for api_name, api_func in apis:
        try:
            print(f"🔄 Trying {api_name} API...")
            if api_name == 'Demo':
                result = api_func(flight_callsign, f"{api_name} Fallback")
            else:
                result = api_func(flight_callsign)
            
            if result and result.get('response', {}).get('httpStatusCode') == 200:
                print(f"✅ Success with {api_name} API")
                return result
                
        except Exception as e:
            print(f"❌ {api_name} API failed: {str(e)}")
            continue
    
    # All APIs failed
    return error_response(f"All flight tracking APIs failed for {flight_callsign}", api_path, 503)

def track_flight_aviationstack(flight_callsign: str) -> Dict:
    """Primary flight tracking via AviationStack"""
    if not AVIATIONSTACK_API_KEY:
        raise Exception("AviationStack API key not configured")
    
    callsign = flight_callsign.upper().strip()
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': AVIATIONSTACK_API_KEY,
        'flight_iata': callsign,
        'limit': 1
    }
    
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 429:
        raise Exception("Rate limit exceeded")
    
    response.raise_for_status()
    data = response.json()
    flights = data.get('data', [])
    
    if not flights:
        raise Exception("No flights found")
    
    flight = flights[0]
    result = {
        'data_source': 'AviationStack API',
        'flight_number': flight.get('flight', {}).get('iata', callsign),
        'status': flight.get('flight_status', 'unknown').upper(),
        'airline': flight.get('airline', {}).get('name', 'N/A'),
        'departure': extract_airport_info(flight.get('departure', {})),
        'arrival': extract_airport_info(flight.get('arrival', {})),
        'aircraft': extract_aircraft_info(flight.get('aircraft', {})),
        'live_data': extract_live_data(flight.get('live', {})),
        'delay_minutes': calculate_delay_enhanced(flight),
        'supply_chain_impact': assess_supply_chain_impact(flight, callsign)
    }
    
    return success_response('/track-flight', result)

def track_flight_opensky(flight_callsign: str) -> Dict:
    """Fallback flight tracking via OpenSky Network"""
    url = "https://opensky-network.org/api/states/all"
    response = requests.get(url, timeout=15)
    
    if response.status_code == 429:
        raise Exception("OpenSky rate limit exceeded")
    
    response.raise_for_status()
    data = response.json()
    states = data.get('states', [])
    
    callsign_upper = flight_callsign.upper().strip()
    flight_state = None
    
    for state in states:
        current_callsign = (state[1] or "").strip().upper()
        if current_callsign == callsign_upper:
            flight_state = state
            break
    
    if not flight_state:
        raise Exception("Flight not found in OpenSky data")
    
    result = parse_opensky_state(flight_state, flight_callsign)
    return success_response('/track-flight', result)

def track_flight_flightaware_fallback(flight_callsign: str) -> Dict:
    """FlightAware public API fallback (limited data)"""
    # This would use FlightAware's public endpoints
    # For now, simulate with enhanced demo data
    raise Exception("FlightAware API not implemented")

# Enhanced Vessel Tracking
def track_vessel_enhanced(vessel_identifier: str, identifier_type: str = 'auto') -> Dict:
    """Enhanced vessel tracking with multiple data sources"""
    api_path = '/track-vessel'
    print(f"🚢 Enhanced vessel tracking: {vessel_identifier}")
    
    # Auto-detect identifier type
    if identifier_type == 'auto':
        identifier_type = detect_vessel_identifier_type(vessel_identifier)
    
    # Try multiple vessel APIs
    vessel_apis = [
        ('AISStream', track_vessel_aisstream),
        ('MarineTraffic', track_vessel_marinetraffic_fallback),
        ('VesselFinder', track_vessel_vesselfinder_fallback),
        ('Demo', get_demo_vessel_data)
    ]
    
    for api_name, api_func in vessel_apis:
        try:
            print(f"🔄 Trying {api_name} for vessel tracking...")
            if api_name == 'Demo':
                result = api_func(vessel_identifier, identifier_type)
            else:
                result = api_func(vessel_identifier, identifier_type)
            
            if result and result.get('response', {}).get('httpStatusCode') == 200:
                print(f"✅ Vessel tracking success with {api_name}")
                return result
                
        except Exception as e:
            print(f"❌ {api_name} vessel API failed: {str(e)}")
            continue
    
    return error_response(f"All vessel tracking APIs failed for {vessel_identifier}", api_path, 503)

def track_vessel_aisstream(vessel_identifier: str, identifier_type: str) -> Dict:
    """Primary vessel tracking via AISStream"""
    if not AISSTREAM_API_KEY:
        raise Exception("AISStream API key not configured")
    
    # AISStream WebSocket or REST API integration
    # This is a placeholder - implement actual AISStream API calls
    url = f"https://api.aisstream.io/v0/vessels"
    headers = {'Authorization': f'Bearer {AISSTREAM_API_KEY}'}
    
    params = {}
    if identifier_type == 'mmsi':
        params['mmsi'] = vessel_identifier
    elif identifier_type == 'imo':
        params['imo'] = vessel_identifier
    else:
        params['name'] = vessel_identifier
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    if not data.get('vessels'):
        raise Exception("Vessel not found")
    
    vessel = data['vessels'][0]
    result = {
        'data_source': 'AISStream API',
        'vessel_name': vessel.get('name', 'Unknown'),
        'mmsi': vessel.get('mmsi'),
        'imo': vessel.get('imo'),
        'position': {
            'latitude': vessel.get('latitude'),
            'longitude': vessel.get('longitude'),
            'last_update': vessel.get('timestamp')
        },
        'navigation': {
            'speed_knots': vessel.get('speed'),
            'course': vessel.get('course'),
            'heading': vessel.get('heading'),
            'status': vessel.get('nav_status')
        },
        'vessel_info': {
            'type': vessel.get('ship_type'),
            'length': vessel.get('length'),
            'width': vessel.get('width'),
            'draught': vessel.get('draught')
        },
        'destination': vessel.get('destination'),
        'eta': vessel.get('eta'),
        'supply_chain_impact': assess_vessel_impact(vessel)
    }
    
    return success_response('/track-vessel', result)

def track_vessel_marinetraffic_fallback(vessel_identifier: str, identifier_type: str) -> Dict:
    """MarineTraffic API fallback"""
    raise Exception("MarineTraffic API not implemented")

def track_vessel_vesselfinder_fallback(vessel_identifier: str, identifier_type: str) -> Dict:
    """VesselFinder API fallback"""
    raise Exception("VesselFinder API not implemented")

# Enhanced Geopolitical Scanning
def scan_geopolitical_enhanced(region: str, event_type: str = 'all') -> Dict:
    """Enhanced geopolitical event scanning with multiple sources"""
    api_path = '/scan-geopolitical'
    print(f"🌍 Enhanced geopolitical scan: {region} ({event_type})")
    
    # Try multiple news/event APIs
    geo_apis = [
        ('NewsAPI', scan_geopolitical_newsapi),
        ('GDELT', scan_geopolitical_gdelt),
        ('Reuters', scan_geopolitical_reuters_fallback),
        ('Demo', get_demo_geopolitical_data)
    ]
    
    for api_name, api_func in geo_apis:
        try:
            print(f"🔄 Trying {api_name} for geopolitical scanning...")
            if api_name == 'Demo':
                result = api_func(region, event_type)
            else:
                result = api_func(region, event_type)
            
            if result and result.get('response', {}).get('httpStatusCode') == 200:
                print(f"✅ Geopolitical scan success with {api_name}")
                return result
                
        except Exception as e:
            print(f"❌ {api_name} geopolitical API failed: {str(e)}")
            continue
    
    return error_response(f"All geopolitical APIs failed for {region}", api_path, 503)

# Utility Functions
def detect_vessel_identifier_type(identifier: str) -> str:
    """Auto-detect vessel identifier type"""
    identifier = identifier.strip()
    
    if identifier.isdigit():
        if len(identifier) == 9:
            return 'mmsi'
        elif len(identifier) == 7:
            return 'imo'
    
    return 'name'

def extract_airport_info(airport_data: Dict) -> Dict:
    """Extract standardized airport information"""
    return {
        'airport': airport_data.get('airport', 'N/A'),
        'iata': airport_data.get('iata', 'N/A'),
        'icao': airport_data.get('icao', 'N/A'),
        'scheduled': airport_data.get('scheduled', 'N/A'),
        'estimated': airport_data.get('estimated', 'N/A'),
        'actual': airport_data.get('actual', 'N/A'),
        'terminal': airport_data.get('terminal', 'N/A'),
        'gate': airport_data.get('gate', 'N/A')
    }

def extract_aircraft_info(aircraft_data: Dict) -> Dict:
    """Extract standardized aircraft information"""
    return {
        'type': aircraft_data.get('iata', 'N/A'),
        'icao24': aircraft_data.get('icao24', 'N/A'),
        'registration': aircraft_data.get('registration', 'N/A')
    }

def extract_live_data(live_data: Dict) -> Optional[Dict]:
    """Extract live flight position data"""
    if not live_data:
        return None
    
    altitude_m = live_data.get('altitude')
    speed_kmh = live_data.get('speed_horizontal')
    
    return {
        'is_on_ground': live_data.get('is_ground', False),
        'latitude': live_data.get('latitude'),
        'longitude': live_data.get('longitude'),
        'altitude_meters': altitude_m,
        'altitude_feet': int(altitude_m * 3.28084) if altitude_m else None,
        'speed_kmh': speed_kmh,
        'speed_knots': int(speed_kmh * 0.539957) if speed_kmh else None,
        'heading': live_data.get('direction'),
        'updated_utc': live_data.get('updated')
    }

def calculate_delay_enhanced(flight_data: Dict) -> int:
    """Calculate flight delay in minutes"""
    try:
        departure = flight_data.get('departure', {})
        scheduled = departure.get('scheduled')
        actual = departure.get('actual') or departure.get('estimated')
        
        if scheduled and actual:
            scheduled_dt = datetime.fromisoformat(scheduled.replace('Z', '+00:00'))
            actual_dt = datetime.fromisoformat(actual.replace('Z', '+00:00'))
            delay = (actual_dt - scheduled_dt).total_seconds() / 60
            return max(0, int(delay))
    except:
        pass
    
    return 0

def assess_supply_chain_impact(flight_data: Dict, callsign: str) -> Dict:
    """Assess supply chain impact of flight status"""
    status = flight_data.get('flight_status', '').upper()
    delay = calculate_delay_enhanced(flight_data)
    
    # Determine if it's a cargo flight
    is_cargo = any(cargo_code in callsign.upper() for cargo_code in ['FDX', 'UPS', 'DHL', 'CX', 'LH'])
    
    impact_level = 'LOW'
    if delay > 120 or status in ['CANCELLED', 'DIVERTED']:
        impact_level = 'HIGH'
    elif delay > 60 or status == 'DELAYED':
        impact_level = 'MEDIUM'
    
    return {
        'impact_level': impact_level,
        'delay_minutes': delay,
        'is_cargo_flight': is_cargo,
        'status': status,
        'financial_impact_usd': estimate_financial_impact(delay, is_cargo),
        'affected_routes': get_affected_routes(flight_data),
        'recommendations': get_impact_recommendations(impact_level, delay, is_cargo)
    }

def assess_vessel_impact(vessel_data: Dict) -> Dict:
    """Assess supply chain impact of vessel status"""
    return {
        'impact_level': 'MEDIUM',
        'vessel_type': vessel_data.get('ship_type', 'Unknown'),
        'route_disruption': False,
        'port_congestion_risk': 'LOW',
        'recommendations': ['Monitor vessel progress', 'Check alternative routes']
    }

def estimate_financial_impact(delay_minutes: int, is_cargo: bool) -> int:
    """Estimate financial impact in USD"""
    base_cost = 5000 if is_cargo else 1000
    return int(base_cost * (delay_minutes / 60))

def get_affected_routes(flight_data: Dict) -> List[str]:
    """Get potentially affected supply chain routes"""
    departure = flight_data.get('departure', {}).get('iata', '')
    arrival = flight_data.get('arrival', {}).get('iata', '')
    
    if departure and arrival:
        return [f"{departure} → {arrival}"]
    return []

def get_impact_recommendations(impact_level: str, delay: int, is_cargo: bool) -> List[str]:
    """Get recommendations based on impact level"""
    recommendations = []
    
    if impact_level == 'HIGH':
        recommendations.extend([
            'Activate contingency plans',
            'Notify affected customers immediately',
            'Consider alternative transportation'
        ])
    elif impact_level == 'MEDIUM':
        recommendations.extend([
            'Monitor situation closely',
            'Prepare backup options',
            'Update delivery estimates'
        ])
    else:
        recommendations.append('Continue normal monitoring')
    
    if is_cargo and delay > 60:
        recommendations.append('Check perishable cargo priority')
    
    return recommendations

# Demo Data Functions
def get_demo_flight_data(callsign: str, source: str) -> Dict:
    """Generate realistic demo flight data"""
    return {
        'data_source': f'{source} (Demo Data)',
        'flight_number': callsign,
        'status': 'IN_FLIGHT',
        'airline': 'Demo Airlines',
        'departure': {
            'airport': 'John F. Kennedy International Airport',
            'iata': 'JFK',
            'scheduled': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            'actual': (datetime.utcnow() - timedelta(hours=2, minutes=15)).isoformat()
        },
        'arrival': {
            'airport': 'Los Angeles International Airport',
            'iata': 'LAX',
            'scheduled': (datetime.utcnow() + timedelta(hours=3)).isoformat(),
            'estimated': (datetime.utcnow() + timedelta(hours=3, minutes=15)).isoformat()
        },
        'live_data': {
            'latitude': 39.7392,
            'longitude': -104.9903,
            'altitude_feet': 35000,
            'speed_knots': 450,
            'heading': 270
        },
        'delay_minutes': 15,
        'supply_chain_impact': {
            'impact_level': 'LOW',
            'delay_minutes': 15,
            'is_cargo_flight': 'FDX' in callsign.upper(),
            'financial_impact_usd': 1250,
            'recommendations': ['Monitor progress', 'Update ETA estimates']
        }
    }

def get_demo_vessel_data(identifier: str, identifier_type: str) -> Dict:
    """Generate realistic demo vessel data"""
    return success_response('/track-vessel', {
        'data_source': 'Demo Vessel Data',
        'vessel_name': 'VOYAGE' if identifier_type == 'name' else f'Demo Vessel {identifier}',
        'mmsi': '636021482' if identifier_type == 'mmsi' else '123456789',
        'imo': '9907665' if identifier_type == 'imo' else '1234567',
        'position': {
            'latitude': 31.2001,
            'longitude': 29.9187,
            'last_update': datetime.utcnow().isoformat()
        },
        'navigation': {
            'speed_knots': 12.5,
            'course': 045,
            'heading': 047,
            'status': 'Under way using engine'
        },
        'vessel_info': {
            'type': 'Container Ship',
            'length': 274,
            'width': 48,
            'draught': 14.5
        },
        'destination': 'ROTTERDAM',
        'eta': (datetime.utcnow() + timedelta(days=7)).isoformat(),
        'supply_chain_impact': {
            'impact_level': 'MEDIUM',
            'vessel_type': 'Container Ship',
            'route_disruption': False,
            'port_congestion_risk': 'LOW',
            'recommendations': ['Monitor vessel progress', 'Check port schedules']
        }
    })

def get_demo_geopolitical_data(region: str, event_type: str) -> Dict:
    """Generate realistic demo geopolitical data"""
    events = [
        {
            'type': 'labor_strike',
            'location': f'{region} Port Authority',
            'severity': 'MEDIUM',
            'description': 'Dock workers strike affecting container operations',
            'impact': 'Port operations reduced by 40%',
            'duration_estimate': '3-5 days'
        },
        {
            'type': 'weather_disruption',
            'location': f'{region} Shipping Lanes',
            'severity': 'LOW',
            'description': 'Severe weather causing minor delays',
            'impact': 'Average delay of 6-12 hours',
            'duration_estimate': '1-2 days'
        }
    ]
    
    return success_response('/scan-geopolitical', {
        'data_source': 'Demo Geopolitical Data',
        'region': region,
        'event_type': event_type,
        'events_detected': len(events),
        'events': events,
        'risk_level': 'MEDIUM',
        'supply_chain_impact': {
            'affected_routes': [f'{region} → Global'],
            'estimated_delays': '6-48 hours',
            'financial_impact': 'Moderate',
            'recommendations': [
                'Monitor situation closely',
                'Consider alternative routes',
                'Update customer communications'
            ]
        }
    })

# Main Lambda Handler
def lambda_handler(event, context):
    """Enhanced Lambda handler with robust error handling"""
    print(f"📥 Enhanced Tracking Executor invoked: {json.dumps(event)}")
    
    try:
        api_path = event.get('apiPath', '')
        parameters = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
        
        # Extract parameters
        params = {p['name']: p['value'] for p in parameters}
        
        if api_path == '/track-flight':
            flight_callsign = params.get('flight_callsign')
            if not flight_callsign:
                return error_response("flight_callsign parameter required", api_path, 400)
            return track_flight_enhanced(flight_callsign)
            
        elif api_path == '/track-vessel':
            vessel_name = params.get('vessel_name')
            mmsi = params.get('mmsi')
            imo = params.get('imo')
            
            if vessel_name:
                return track_vessel_enhanced(vessel_name, 'name')
            elif mmsi:
                return track_vessel_enhanced(mmsi, 'mmsi')
            elif imo:
                return track_vessel_enhanced(imo, 'imo')
            else:
                return error_response("vessel_name, mmsi, or imo parameter required", api_path, 400)
                
        elif api_path == '/scan-geopolitical':
            region = params.get('region')
            event_type = params.get('event_type', 'all')
            
            if not region:
                return error_response("region parameter required", api_path, 400)
            return scan_geopolitical_enhanced(region, event_type)
            
        else:
            return error_response(f"Unknown API path: {api_path}", api_path, 404)
            
    except Exception as e:
        print(f"❌ Lambda handler error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return error_response(f"Internal server error: {str(e)}", event.get('apiPath', ''), 500)

# Placeholder implementations for missing functions
def parse_opensky_state(state, callsign):
    """Parse OpenSky state vector"""
    return {
        'data_source': 'OpenSky Network',
        'flight_number': callsign,
        'status': 'IN_FLIGHT',
        'live_data': {
            'latitude': state[6],
            'longitude': state[5],
            'altitude_meters': state[7],
            'speed_mps': state[9],
            'heading': state[10]
        }
    }

def scan_geopolitical_newsapi(region, event_type):
    """NewsAPI implementation placeholder"""
    raise Exception("NewsAPI not implemented")

def scan_geopolitical_gdelt(region, event_type):
    """GDELT implementation placeholder"""
    raise Exception("GDELT not implemented")

def scan_geopolitical_reuters_fallback(region, event_type):
    """Reuters API fallback placeholder"""
    raise Exception("Reuters API not implemented")
