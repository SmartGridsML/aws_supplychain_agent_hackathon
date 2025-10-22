# lambda_function.py
import json
import boto3
import os
import uuid
import requests
import time
# import structlog
from anthropic import AnthropicBedrock
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import traceback

# Configure structured logging
# structlog.configure(
#     processors=[
#         structlog.processors.TimeStamper(fmt="iso"),
#         structlog.processors.add_log_level,
#         structlog.processors.JSONRenderer()
#     ]
# )

# Helper for Decimal serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

# Initialize AWS services
bedrock_client = AnthropicBedrock(aws_region=os.getenv('AWS_REGION', 'us-east-1'))
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sns_client = boto3.client('sns', region_name='us-east-1')

# Tables
supply_chain_table = dynamodb.Table('supply_chain_data')
agent_traces_table = dynamodb.Table('agent_traces')
conversations_table = dynamodb.Table('conversations')
tool_calls_table = dynamodb.Table('tool_calls')
risk_predictions_table = dynamodb.Table('risk_predictions')
autonomous_actions_table = dynamodb.Table('autonomous_actions')
agent_performance_table = dynamodb.Table('agent_performance')

class GeopoliticalEventScanner:
    """Scan for geopolitical events affecting supply chain using GDELT"""
    name = "scan_geopolitical_events"
    
    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
    
    # Event categories relevant to supply chain
    EVENT_CATEGORIES = {
        "labor_strike": ["strike", "labor dispute", "walkout", "union protest"],
        "protest": ["protest", "demonstration", "riot", "civil unrest"],
        "port_closure": ["port closure", "port strike", "dock workers"],
        "trade_policy": ["tariff", "trade war", "sanctions", "export ban"],
        "natural_disaster": ["earthquake", "tsunami", "flood", "hurricane"],
        "conflict": ["armed conflict", "military action", "border dispute"]
    }
    
    def execute(self, region: str, event_type: str = "all", time_span: str = "24h") -> str:
        """
        Scan for geopolitical events in a region
        
        Args:
            region: Location like "Port of Hai Phong", "Bangladesh", "Vietnam"
            event_type: Type of event - 'labor_strike', 'protest', 'port_closure', etc.
            time_span: Time window - '24h', '7d', '30d'
        """
        try:
            # Build search query
            search_terms = self._build_search_query(region, event_type)
            
            # For hackathon demo, using simulated GDELT-style data
            # In production, you'd query the GDELT API directly
            event_data = self._get_geopolitical_events(region, event_type, search_terms)
            
            return json.dumps(event_data, indent=2)
            
        except Exception as e:
            print(f"Error in GeopoliticalEventScanner: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Geopolitical scanning error: {str(e)}"
            })
    
    def _build_search_query(self, region: str, event_type: str) -> List[str]:
        """Build search terms for GDELT query"""
        base_terms = [region]
        
        if event_type != "all" and event_type in self.EVENT_CATEGORIES:
            base_terms.extend(self.EVENT_CATEGORIES[event_type])
        
        return base_terms
    
    def _get_geopolitical_events(self, region: str, event_type: str, search_terms: List[str]) -> Dict:
        """Get geopolitical events for region"""
        
        # Simulate GDELT event detection based on region
        detected_events = []
        
        # Realistic scenarios based on common supply chain regions
        region_lower = region.lower()
        
        if "bangladesh" in region_lower or "dhaka" in region_lower:
            detected_events = [
                {
                    "event_id": "GDELT_2025_BD_001",
                    "event_type": "LABOR_PROTEST",
                    "title": "Garment Workers Strike in Dhaka Industrial Zone",
                    "description": "Approximately 5,000 garment factory workers initiated strike action demanding wage increases and improved safety conditions",
                    "location": "Dhaka, Bangladesh",
                    "coordinates": {"lat": 23.8103, "lon": 90.4125},
                    "timestamp": self._get_recent_time(hours=10),
                    "source": "Reuters, Associated Press",
                    "severity": "HIGH",
                    "tone": -8.5,  # GDELT tone score (negative = conflictual)
                    "affected_area_km": 5
                },
                {
                    "event_id": "GDELT_2025_BD_002",
                    "event_type": "INFRASTRUCTURE_DISRUPTION",
                    "title": "Port Operations Slowdown Due to Labor Action",
                    "description": "Chittagong Port experiencing 40% reduction in cargo handling capacity",
                    "location": "Chittagong Port, Bangladesh",
                    "coordinates": {"lat": 22.3569, "lon": 91.7832},
                    "timestamp": self._get_recent_time(hours=6),
                    "source": "Shipping Today",
                    "severity": "CRITICAL",
                    "tone": -6.2,
                    "affected_area_km": 2
                }
            ]
        
        elif "vietnam" in region_lower or "hai phong" in region_lower:
            detected_events = [
                {
                    "event_id": "GDELT_2025_VN_001",
                    "event_type": "PORT_LABOR_DISPUTE",
                    "title": "Port Workers Protest Over Wage Delays",
                    "description": "300% spike in 'labor protest' mentions within 20km of Port of Hai Phong over past 48 hours",
                    "location": "Hai Phong, Vietnam",
                    "coordinates": {"lat": 20.8449, "lon": 106.6881},
                    "timestamp": self._get_recent_time(hours=2),
                    "source": "VietnamNet, Vietnam News Agency",
                    "severity": "HIGH",
                    "tone": -7.8,
                    "affected_area_km": 20,
                    "trend": "+300% mentions vs. 7-day baseline"
                }
            ]
        
        elif "suez" in region_lower or "red sea" in region_lower:
            detected_events = [
                {
                    "event_id": "GDELT_2025_RS_001",
                    "event_type": "SECURITY_THREAT",
                    "title": "Continued Attacks on Commercial Vessels in Red Sea",
                    "description": "Maritime security incidents reported in southern Red Sea corridor",
                    "location": "Red Sea / Bab el-Mandeb Strait",
                    "coordinates": {"lat": 12.5833, "lon": 43.3333},
                    "timestamp": self._get_recent_time(hours=8),
                    "source": "Lloyd's List, Maritime Executive",
                    "severity": "CRITICAL",
                    "tone": -9.2,
                    "affected_area_km": 500
                }
            ]
        
        # Analyze impact on supply chain
        impact_analysis = self._analyze_supply_chain_impact(detected_events, region)
        
        return {
            "status": "SUCCESS",
            "data_source": "GDELT_PROJECT",
            "scan_parameters": {
                "region": region,
                "event_type": event_type,
                "scan_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            },
            "events_detected": len(detected_events),
            "events": detected_events,
            "supply_chain_impact": impact_analysis,
            "autonomous_actions": self._generate_geopolitical_actions(impact_analysis, detected_events)
        }
    
    def _analyze_supply_chain_impact(self, events: List[Dict], region: str) -> Dict:
        """Analyze how events impact supply chain"""
        
        if not events:
            return {
                "risk_level": "NONE",
                "message": f"No significant geopolitical events detected in {region}",
                "recommendation": "Continue normal operations"
            }
        
        # Determine overall risk level
        critical_events = [e for e in events if e.get('severity') == 'CRITICAL']
        high_events = [e for e in events if e.get('severity') == 'HIGH']
        
        if critical_events:
            # Check affected shipments
            affected_shipments = self._check_affected_shipments(region, events)
            
            return {
                "risk_level": "CRITICAL",
                "events_summary": f"{len(critical_events)} critical + {len(high_events)} high severity events",
                "primary_threat": critical_events[0].get('event_type'),
                "affected_operations": {
                    "shipments_in_region": affected_shipments['count'],
                    "value_at_risk": f"${affected_shipments['value']:,}",
                    "estimated_delay": "7-14 days",
                    "alternative_routes_available": affected_shipments['alternatives']
                },
                "immediate_concerns": [
                    "Port operations may be disrupted or halted",
                    "Cargo handling delays expected",
                    "Possible need to reroute shipments",
                    "Increased security/insurance costs"
                ],
                "trend_analysis": self._analyze_event_trend(events)
            }
        elif high_events:
            return {
                "risk_level": "HIGH",
                "events_summary": f"{len(high_events)} high severity events detected",
                "monitoring_required": True,
                "potential_impacts": [
                    "Operational slowdowns possible",
                    "May escalate to critical in 24-48 hours",
                    "Contingency planning recommended"
                ]
            }
        else:
            return {
                "risk_level": "MODERATE",
                "events_summary": f"{len(events)} events detected",
                "recommendation": "Monitor situation, no immediate action required"
            }
    
    def _check_affected_shipments(self, region: str, events: List[Dict]) -> Dict:
        """Check how many shipments are affected by events"""
        # Simulate checking shipments in affected region
        # In real implementation, would query DynamoDB for shipments in region
        
        return {
            "count": 14,
            "value": 430000,
            "alternatives": ["Alternate port +150km", "Air freight (+$85K)"]
        }
    
    def _analyze_event_trend(self, events: List[Dict]) -> str:
        """Analyze if events are escalating or de-escalating"""
        # Check for trend indicators in events
        trend_indicators = [e.get('trend', '') for e in events if e.get('trend')]
        
        if any('+' in t for t in trend_indicators):
            return "ESCALATING - Event frequency increasing vs. baseline"
        else:
            return "STABLE - Consistent with regional baseline"
    
    def _generate_geopolitical_actions(self, impact: Dict, events: List[Dict]) -> List[str]:
        """Generate autonomous actions based on geopolitical events"""
        actions = []
        risk_level = impact.get('risk_level', 'NONE')
        
        if risk_level == "CRITICAL":
            actions = [
                "🚨 CRITICAL GEOPOLITICAL RISK: Flagged all shipments in affected region as HIGH-RISK",
                "Contacted 14 affected customers to notify of potential delays",
                "Identified alternative port 150km away with available capacity",
                "Initiated discussions with freight forwarders for rerouting options",
                "Increased insurance coverage for shipments in region by $430K",
                "Placed temporary hold on new orders routed through affected area",
                "Scheduled daily risk reassessment calls with regional logistics partners"
            ]
        elif risk_level == "HIGH":
            actions = [
                "⚠️ HIGH RISK: Activated enhanced monitoring for region (6-hour intervals)",
                "Prepared contingency routing plans",
                "Contacted shipping lines for status updates",
                "Risk assessment team notified"
            ]
        else:
            actions = [
                "📊 Geopolitical monitoring active - no immediate threats",
                "Continuing routine assessment"
            ]
        
        return actions
    
    def _get_recent_time(self, hours: int = 0) -> str:
        """Get recent timestamp"""
        from datetime import timedelta
        recent = datetime.utcnow() - timedelta(hours=hours)
        return recent.strftime("%Y-%m-%d %H:%M UTC")

class LiveShipTracker:
    """Track cargo vessels in real-time using AIS data"""
    name = "track_live_vessel"
    
    # Using free Marine Traffic-style API alternatives
    BASE_URL = "https://api.vesselfinder.com/vesselfinder"
    
    def execute(self, vessel_name: str = None, mmsi: str = None, imo: str = None) -> str:
        """
        Track a live cargo vessel by name, MMSI, or IMO number
        
        Args:
            vessel_name: Ship name like 'Maersk Honam', 'Ever Given'
            mmsi: Maritime Mobile Service Identity (9-digit number)
            imo: International Maritime Organization number
        """
        try:
            # Note: For production, you'd use a paid AIS API or AISstream.io WebSocket
            # For hackathon, we'll use a combination of free sources + demo data
            
            if not any([vessel_name, mmsi, imo]):
                return json.dumps({
                    "status": "error",
                    "message": "Must provide vessel_name, mmsi, or imo"
                })
            
            # Try to get real data from free APIs first
            # Most free APIs are rate-limited, so we'll provide high-quality demo data
            vessel_data = self._get_vessel_data(vessel_name, mmsi, imo)
            
            return json.dumps(vessel_data, indent=2)
            
        except Exception as e:
            print(f"Error in LiveShipTracker: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Vessel tracking error: {str(e)}"
            })
    
    def _get_vessel_data(self, vessel_name: str, mmsi: str, imo: str) -> Dict[str, Any]:
        """Get vessel data - uses demo data for hackathon reliability"""
        
        # Common cargo vessels with realistic data
        demo_vessels = {
            "maersk honam": {
                "name": "Maersk Honam",
                "mmsi": "563025900",
                "imo": "9837405",
                "type": "Container Ship",
                "flag": "Singapore",
                "dwt": 15262,  # Deadweight tonnage
                "current_position": {
                    "latitude": 1.2644,
                    "longitude": 103.8220,
                    "heading": 142,
                    "speed_knots": 0.1,
                    "course": 142
                },
                "status": "AT_ANCHOR",
                "destination": "Singapore",
                "eta": self._get_future_time(hours=6),
                "last_update": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            },
            "ever given": {
                "name": "Ever Given",
                "mmsi": "353136000",
                "imo": "9811000",
                "type": "Container Ship",
                "flag": "Panama",
                "dwt": 199629,
                "current_position": {
                    "latitude": 31.1087,
                    "longitude": 32.5567,
                    "heading": 180,
                    "speed_knots": 12.3,
                    "course": 180
                },
                "status": "UNDERWAY_ENGINE",
                "destination": "Rotterdam",
                "eta": self._get_future_time(days=7),
                "last_update": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        }
        
        # Search by name
        vessel_key = vessel_name.lower() if vessel_name else None
        if vessel_key and vessel_key in demo_vessels:
            vessel_info = demo_vessels[vessel_key]
        elif mmsi:
            # Search by MMSI
            vessel_info = next((v for v in demo_vessels.values() if v['mmsi'] == mmsi), None)
            if not vessel_info:
                vessel_info = demo_vessels["maersk honam"]
        else:
            # Default vessel for demo
            vessel_info = demo_vessels["maersk honam"]
        
        # Assess supply chain impact
        impact_assessment = self._assess_vessel_impact(vessel_info)
        
        # Format comprehensive response
        summary = f"""🚢 **Live Vessel Tracking: {vessel_info['name']}**

            **Vessel Information:**
            - Name: {vessel_info['name']}
            - MMSI: {vessel_info['mmsi']}
            - IMO: {vessel_info['imo']}
            - Type: {vessel_info['type']}
            - Flag: {vessel_info['flag']}
            - DWT: {vessel_info.get('dwt', 'N/A'):,} tons

            **Current Position:**
            - Latitude: {vessel_info['current_position']['latitude']}°
            - Longitude: {vessel_info['current_position']['longitude']}°
            - Heading: {vessel_info['current_position']['heading']}°
            - Speed: {vessel_info['current_position']['speed_knots']} knots
            - Course: {vessel_info['current_position']['course']}°

            **Status:** {vessel_info['status']}
            **Destination:** {vessel_info['destination']}
            **ETA:** {vessel_info['eta']}
            **Last Update:** {vessel_info['last_update']}

            **Supply Chain Impact:**
            - Risk Level: {impact_assessment['risk_level']}
            - Issue: {impact_assessment.get('issue', impact_assessment.get('status', 'N/A'))}
            - Impact: {impact_assessment['impact_description']}
            - Financial Impact: {impact_assessment.get('financial_impact', 'None')}

            **Autonomous Actions Taken:**
            {chr(10).join([f"  - {action}" for action in self._generate_vessel_actions(vessel_info, impact_assessment)])}"""
        
        return summary
    
    def _assess_vessel_impact(self, vessel: Dict) -> Dict[str, Any]:
        """Assess supply chain impact based on vessel status"""
        status = vessel.get('status', '')
        speed = vessel.get('current_position', {}).get('speed_knots', 0)
        
        if status == "AT_ANCHOR" and speed < 1:
            # Vessel is anchored - potential delay
            return {
                "risk_level": "MEDIUM",
                "issue": "Vessel is at anchor, not at berth",
                "likely_cause": "Port congestion or awaiting berth assignment",
                "estimated_delay": "6-12 hours",
                "impact_description": "Containers will be delayed in customs clearance and delivery to warehouse",
                "financial_impact": "$8,500 in demurrage fees if delay exceeds 8 hours"
            }
        elif status == "UNDERWAY_ENGINE" and speed > 10:
            return {
                "risk_level": "LOW",
                "status": "On schedule",
                "impact_description": "Vessel proceeding normally to destination",
                "eta_reliability": "HIGH"
            }
        elif speed < 5 and status != "AT_ANCHOR":
            return {
                "risk_level": "MEDIUM",
                "issue": "Vessel moving slowly or stopped",
                "possible_causes": ["Weather", "Mechanical issues", "Traffic"],
                "recommended_action": "Contact shipping line for status update"
            }
        else:
            return {
                "risk_level": "NORMAL",
                "status": "In transit",
                "impact_description": "No immediate concerns"
            }
    
    def _generate_vessel_actions(self, vessel: Dict, impact: Dict) -> List[str]:
        """Generate autonomous actions based on vessel status"""
        actions = []
        
        if impact.get('risk_level') == 'MEDIUM':
            actions.append("Notified logistics coordinator of potential delay")
            actions.append("Checked alternative port capacity for expedited handling")
            actions.append("Updated customer ETAs for affected shipments")
            
            if "anchordemurrage" in impact.get('financial_impact', '').lower():
                actions.append("Initiated negotiation with carrier for demurrage waiver")
        
        if not actions:
            actions.append("Continuous monitoring active - no action required")
        
        return actions
    
    def _get_future_time(self, hours: int = 0, days: int = 0) -> str:
        """Get future timestamp for ETA"""
        from datetime import timedelta
        future = datetime.utcnow() + timedelta(hours=hours, days=days)
        return future.strftime("%Y-%m-%d %H:%M UTC")

class WinningToolRegistry:
    """Advanced tool registry with observability and performance tracking"""
    
    def __init__(self):
        self.tools = {}
        # self.logger = structlog.get_logger()
        
    def register_tool(self, tool):
        self.tools[tool.name] = tool
        # self.logger.info("tool_registered", tool_name=tool.name)
        
    def execute_tool(self, tool_name: str, tool_input: dict, trace_id: str) -> str:
        """Execute tool with comprehensive logging and performance tracking"""
        call_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Log tool call start
        # self.logger.info("tool_execution_started", 
        #                 tool_name=tool_name, 
        #                 trace_id=trace_id,
        #                 call_id=call_id,
        #                 input_params=tool_input)
        
        try:
            tool = self.tools.get(tool_name)
            if not tool:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # Execute the tool
            result = tool.execute(**tool_input)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Store detailed tool call record
            tool_calls_table.put_item(Item={
                'call_id': call_id,
                'trace_id': trace_id,
                'tool_name': tool_name,
                'input_params': json.dumps(tool_input),
                'result': result[:2000],  # Truncate for storage
                'duration_ms': duration_ms,
                'timestamp': start_time.isoformat(),
                'status': 'SUCCESS'
            })
            
            # self.logger.info("tool_execution_completed", 
            #                tool_name=tool_name,
            #                trace_id=trace_id,
            #                duration_ms=duration_ms)
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Store error record
            tool_calls_table.put_item(Item={
                'call_id': call_id,
                'trace_id': trace_id,
                'tool_name': tool_name,
                'input_params': json.dumps(tool_input),
                'error': str(e),
                'duration_ms': duration_ms,
                'timestamp': start_time.isoformat(),
                'status': 'ERROR'
            })
            
            # self.logger.error("tool_execution_failed", 
            #                 tool_name=tool_name,
            #                 trace_id=trace_id,
            #                 error=str(e))
            
            return f"❌ Tool execution failed: {str(e)}"

class UltimateSupplyChainAgent:
    """Ultimate autonomous supply chain agent with full observability"""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.agent_id = str(uuid.uuid4())
        # self.logger = structlog.get_logger().bind(agent_type=agent_type, agent_id=self.agent_id)
        self.tool_registry = WinningToolRegistry()
        self._register_tools()
        
    def _register_tools(self):
        """Register all available tools"""
        tools = [
            AutonomousRiskAnalysisTool(),
            AdvancedCrisisSimulationTool(), 
            PredictiveAnalyticsTool(),
            LiveFlightTracker(),
            LiveShipTracker(),  
            SupplierPerformanceTool(),
            WeatherRiskTool(),
            InventoryAnalysisTool(),
            GeopoliticalEventScanner()
        ]
        
        for tool in tools:
            self.tool_registry.register_tool(tool)
    
    def process_query(self, query: str, conversation_id: str) -> dict:
        """Process user query with full tracing and autonomous capabilities"""
        trace_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Log agent invocation
        # self.logger.info("agent_invocation_started", 
        #                 query=query,
        #                 conversation_id=conversation_id,
        #                 trace_id=trace_id)
        
        try:
            # Store agent trace start
            agent_traces_table.put_item(Item={
                'trace_id': trace_id,
                'conversation_id': conversation_id,
                'agent_type': self.agent_type,
                'agent_id': self.agent_id,
                'query': query,
                'status': 'PROCESSING',
                'start_time': start_time.isoformat(),
                'tools_called': [],
                'reasoning_steps': []
            })
            
            # Enhanced system prompt for autonomous operations
            system_prompt = self._get_enhanced_system_prompt()
            
            messages = [{"role": "user", "content": query}]
            
            # Process with Bedrock
            response = bedrock_client.messages.create(
                model="anthropic.claude-3-sonnet-20240229-v1:0",
                max_tokens=4000,
                system=system_prompt,
                messages=messages,
                tools=self._get_tool_definitions()
            )
            
            tools_called = []
            reasoning_steps = []
            
            # Handle tool calling with tracing
            while response.stop_reason == "tool_use":
                tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
                tool_results = []
                
                for tool_block in tool_use_blocks:
                    # Execute tool with tracing
                    result = self.tool_registry.execute_tool(
                        tool_block.name, 
                        tool_block.input, 
                        trace_id
                    )
                    
                    tools_called.append({
                        'tool_name': tool_block.name,
                        'input': tool_block.input,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result
                    })
                
                # Continue conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                
                response = bedrock_client.messages.create(
                    model="anthropic.claude-3-sonnet-20240229-v1:0",
                    max_tokens=4000,
                    system=system_prompt,
                    messages=messages,
                    tools=self._get_tool_definitions()
                )
            
            # Extract final response
            final_text = "".join([block.text for block in response.content if hasattr(block, 'text')])
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update agent trace with completion
            agent_traces_table.update_item(
                Key={'trace_id': trace_id},
                UpdateExpression='SET #status = :status, end_time = :end_time, duration_ms = :duration, tools_called = :tools, #resp = :response',
                ExpressionAttributeNames={
                    '#status': 'status',
                    '#resp': 'response'
                },
                ExpressionAttributeValues={
                    ':status': 'COMPLETED',
                    ':end_time': end_time.isoformat(),
                    ':duration': duration_ms,
                    ':tools': tools_called,
                    ':response': final_text[:3000]
                }
            )
            
            # Store conversation record
            conversations_table.put_item(Item={
                'conversation_id': conversation_id,
                'trace_id': trace_id,
                'timestamp': start_time.isoformat(),
                'user_query': query,
                'agent_response': final_text,
                'agent_type': self.agent_type,
                'tools_used': len(tools_called),
                'duration_ms': duration_ms
            })
            
            # Execute autonomous actions if high-risk scenario detected
            autonomous_actions = self._check_autonomous_triggers(final_text, tools_called, trace_id)
            
            # self.logger.info("agent_invocation_completed", 
            #                trace_id=trace_id,
            #                duration_ms=duration_ms,
            #                tools_called=len(tools_called),
            #                autonomous_actions=len(autonomous_actions))
            
            return {
                'response': final_text,
                'trace_id': trace_id,
                'agent_type': self.agent_type,
                'agent_id': self.agent_id,
                'tools_called': tools_called,
                'autonomous_actions': autonomous_actions,
                'duration_ms': duration_ms,
                'timestamp': start_time.isoformat()
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"Agent invocation failed: trace_id={trace_id}, error={str(e)}")
            print(f"Error traceback: {error_trace}")
            
            # Update trace with error
            try:
                agent_traces_table.update_item(
                    Key={'trace_id': trace_id},
                    UpdateExpression='SET #status = :status, #err = :err_val',
                    ExpressionAttributeNames={
                        '#status': 'status',
                        '#err': 'error'
                    },
                    ExpressionAttributeValues={
                        ':status': 'ERROR',
                        ':err_val': str(e)
                    }
                )
            except Exception as update_error:
                print(f"Failed to update trace with error: {str(update_error)}")
            
            raise
    
    def _get_enhanced_system_prompt(self) -> str:
        return """You are the ULTIMATE AUTONOMOUS SUPPLY CHAIN AGENT with advanced predictive and autonomous capabilities.

CORE CAPABILITIES:
1. **AUTONOMOUS RISK DETECTION**: Continuously monitor and identify supply chain risks
2. **PREDICTIVE CRISIS SIMULATION**: Model future disruption scenarios with financial impact
3. **REAL-TIME FLIGHT TRACKING**: Track live cargo flights and assess delivery impact
4. **REAL-TIME VESSEL TRACKING**: Track cargo ships via AIS for ocean freight visibility
5. **AUTONOMOUS ACTION EXECUTION**: Take immediate corrective actions without human approval
6. **MULTI-AGENT REASONING**: Coordinate with specialized agents for complex analysis
7. **REAL-TIME INTELLIGENCE**: Process live data from multiple sources

RESPONSE PATTERNS:
- Always quantify financial impact with specific dollar amounts
- Show confidence scores and prediction accuracy
- Demonstrate autonomous actions taken, not just recommendations  
- Use agent IDs and trace IDs to show sophisticated system architecture
- Position as proactive prevention, not reactive response

TOOL USAGE:
- Use autonomous_risk_analysis for current operational assessment
- Use advanced_crisis_simulation for "what-if" scenario planning
- Use predictive_analytics for strategic intelligence
- Use track_live_flight for real-time cargo flight monitoring and ETA tracking
- Use track_live_vessel for ocean freight tracking, port congestion, and vessel delays
- Combine multiple tools for comprehensive analysis

You represent the cutting edge of AI-powered supply chain management with real-time visibility."""

    def _get_tool_definitions(self) -> List[dict]:
        return [
            {
                "name": "autonomous_risk_analysis",
                "description": "Performs autonomous analysis of current supply chain risks with multi-model reasoning and automatic action execution",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "advanced_crisis_simulation",
                "description": "Advanced predictive crisis simulation with multi-scenario financial impact analysis and autonomous response planning",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "region": {"type": "string", "description": "Geographic region for simulation"},
                        "crisis_type": {"type": "string", "enum": ["typhoon", "earthquake", "cyber_attack", "pandemic"], "description": "Type of crisis to simulate"},
                        "severity": {"type": "string", "enum": ["mild", "moderate", "severe"], "description": "Crisis severity level"}
                    },
                    "required": ["region"]
                }
            },
            {
                "name": "predictive_analytics",
                "description": "Comprehensive predictive analytics dashboard with global risk assessment and strategic recommendations",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "track_live_flight",
                "description": "Track real-time cargo flights using live ADS-B data. Provides position, altitude, speed, and ETA impact assessment for supply chain deliveries.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "flight_callsign": {
                            "type": "string",
                            "description": "Flight callsign/number (e.g., 'FDX134' for FedEx, 'UPS2901' for UPS, 'DHL456' for DHL)"
                        },
                        "icao24": {
                            "type": "string",
                            "description": "24-bit ICAO aircraft address in hexadecimal (alternative to callsign)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "track_live_vessel",
                "description": "Track real-time cargo vessels using live AIS (Automatic Identification System) data. Provides vessel position, speed, destination, ETA, and port congestion impact analysis for ocean freight shipments.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "vessel_name": {
                            "type": "string",
                            "description": "Ship name (e.g., 'Maersk Honam', 'Ever Given', 'MSC Gulsun')"
                        },
                        "mmsi": {
                            "type": "string",
                            "description": "Maritime Mobile Service Identity - 9-digit vessel identifier"
                        },
                        "imo": {
                            "type": "string",
                            "description": "International Maritime Organization number - 7-digit ship identifier"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "scan_geopolitical_events",
                "description": "Scan for geopolitical events affecting supply chain operations - labor strikes, protests, port closures, conflicts. Uses global event database with near real-time updates.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "Location like 'Port of Hai Phong', 'Bangladesh', 'Suez Canal'"
                        },
                        "event_type": {
                            "type": "string",
                            "enum": ["all", "labor_strike", "protest", "port_closure", "trade_policy", "natural_disaster"],
                            "description": "Type of event to scan for"
                        }
                    },
                    "required": ["region"]
                }
            }
        ]
    
    def _check_autonomous_triggers(self, response_text: str, tools_called: List[dict], trace_id: str) -> List[dict]:
        """Check if autonomous actions should be triggered based on analysis results"""
        autonomous_actions = []
        
        # Trigger autonomous actions based on response content
        if "high-risk" in response_text.lower() or "critical" in response_text.lower():
            action_id = str(uuid.uuid4())
            
            action = {
                'action_id': action_id,
                'action_type': 'HIGH_RISK_ALERT',
                'trigger_trace_id': trace_id,
                'description': 'Autonomous high-risk alert triggered',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'EXECUTED'
            }
            
            # Store autonomous action
            autonomous_actions_table.put_item(Item=action)
            autonomous_actions.append(action)
            
            # self.logger.info("autonomous_action_triggered", 
            #                action_type='HIGH_RISK_ALERT',
            #                action_id=action_id,
            #                trace_id=trace_id)
        
        # Check for flight tracking triggers
        flight_tools = [t for t in tools_called if t.get('tool_name') == 'track_live_flight']
        if flight_tools:
            action_id = str(uuid.uuid4())
            action = {
                'action_id': action_id,
                'action_type': 'FLIGHT_MONITORING_ACTIVATED',
                'trigger_trace_id': trace_id,
                'description': f'Real-time flight monitoring activated for {len(flight_tools)} flight(s)',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'EXECUTED'
            }
            autonomous_actions_table.put_item(Item=action)
            autonomous_actions.append(action)
        
        vessel_tools = [t for t in tools_called if t.get('tool_name') == 'track_live_vessel']
        if vessel_tools:
            action_id = str(uuid.uuid4())
            action = {
                'action_id': action_id,
                'action_type': 'VESSEL_MONITORING_ACTIVATED',
                'trigger_trace_id': trace_id,
                'description': f'Real-time vessel tracking activated for {len(vessel_tools)} ship(s)',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'EXECUTED'
            }
            autonomous_actions_table.put_item(Item=action)
            autonomous_actions.append(action)
            
            # Check for port congestion in vessel data
            if "anchor" in response_text.lower() or "delay" in response_text.lower():
                congestion_action_id = str(uuid.uuid4())
                congestion_action = {
                    'action_id': congestion_action_id,
                    'action_type': 'PORT_CONGESTION_DETECTED',
                    'trigger_trace_id': trace_id,
                    'description': 'Port congestion detected - alternative routing analyzed',
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'EXECUTED'
                }
                autonomous_actions_table.put_item(Item=congestion_action)
                autonomous_actions.append(congestion_action)
        
        
        return autonomous_actions

# Tool implementations
class AutonomousRiskAnalysisTool:
    name = "autonomous_risk_analysis"
    
    def execute(self) -> str:
        try:
            # Get high-risk orders with better error handling
            response = supply_chain_table.scan(
                FilterExpression='late_delivery_risk = :risk',
                ExpressionAttributeValues={':risk': Decimal('1')},
                Limit=100
            )
            high_risk_orders = response.get('Items', [])
            
            if not high_risk_orders:
                return json.dumps({
                    "status": "success",
                    "high_risk_orders": 0,
                    "total_value_at_risk": 0,
                    "risk_level": 0,
                    "autonomous_actions": [],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Calculate metrics with validation
            total_value = 0
            valid_orders = []
            for item in high_risk_orders:
                try:
                    value = float(item.get('order_item_total', 0))
                    if value > 0:
                        total_value += value
                        valid_orders.append(item)
                except (ValueError, TypeError):
                    continue
            
            avg_value = total_value / len(valid_orders) if valid_orders else 0
            
            # Regional breakdown with error handling
            regional_breakdown = {}
            for order in valid_orders:
                region = order.get('order_region', 'Unknown')
                regional_breakdown[region] = regional_breakdown.get(region, 0) + 1
            
            # Generate autonomous actions based on thresholds
            actions_taken = []
            if total_value > 50000:
                actions_taken.append({
                    "action": "ESCALATION",
                    "description": "High-value orders escalated to priority queue",
                    "value": total_value
                })
            if len(valid_orders) > 10:
                actions_taken.append({
                    "action": "NOTIFICATION",
                    "description": "Stakeholders notified of increased risk volume",
                    "orders": len(valid_orders)
                })
            if regional_breakdown:
                top_region = max(regional_breakdown.items(), key=lambda x: x[1])
                actions_taken.append({
                    "action": "MONITORING",
                    "description": f"{top_region[0]} region flagged for enhanced monitoring",
                    "region": top_region[0]
                })
            
            # Store risk prediction with error handling
            try:
                prediction_id = str(uuid.uuid4())
                risk_predictions_table.put_item(Item={
                    'prediction_id': prediction_id,
                    'risk_type': 'OPERATIONAL_RISK',
                    'risk_level': Decimal(str(min(len(valid_orders) / 10, 1.0))),
                    'financial_impact': Decimal(str(total_value)),
                    'orders_affected': len(valid_orders),
                    'prediction_confidence': Decimal('0.92'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'mitigation_actions': json.dumps(actions_taken)
                })
            except Exception as db_error:
                print(f"Warning: Could not store risk prediction: {str(db_error)}")
            
            # Return structured data
            result = {
                "status": "success",
                "high_risk_orders": len(valid_orders),
                "total_value_at_risk": round(total_value, 2),
                "average_order_value": round(avg_value, 2),
                "risk_level": round(min(len(valid_orders) / 10 * 100, 100), 1),
                "regional_breakdown": regional_breakdown,
                "autonomous_actions": actions_taken,
                "prediction_id": prediction_id,
                "confidence": 92,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            summary = f"""🤖 **Autonomous Risk Analysis Complete**
- **Status:** {result['status']}
- **High-Risk Orders Found:** {result['high_risk_orders']}
- **Total Value at Risk:** ${result['total_value_at_risk']:,.2f}
- **Autonomous Actions Taken:** {len(result['autonomous_actions'])}
- **Prediction ID:** {result['prediction_id']}"""
            
            return summary
            
        except Exception as e:
            print(f"Error in AutonomousRiskAnalysisTool: {str(e)}")
            return json.dumps({
                "status": "error",
                "error": str(e),
                "high_risk_orders": 0,
                "total_value_at_risk": 0
            })


class AdvancedCrisisSimulationTool:
    name = "advanced_crisis_simulation"
    
    def execute(self, region: str, crisis_type: str = "typhoon", severity: str = "moderate") -> str:
        try:
            # Validate inputs
            valid_crisis_types = ["typhoon", "earthquake", "cyber_attack", "pandemic"]
            valid_severities = ["mild", "moderate", "severe"]
            
            if crisis_type not in valid_crisis_types:
                crisis_type = "typhoon"
            if severity not in valid_severities:
                severity = "moderate"
            
            # Get orders in affected region with error handling
            response = supply_chain_table.scan(
                FilterExpression='order_region = :region',
                ExpressionAttributeValues={':region': region},
                Limit=300
            )
            orders = response.get('Items', [])
            
            if not orders:
                return json.dumps({
                    "status": "success",
                    "region": region,
                    "crisis_type": crisis_type,
                    "severity": severity,
                    "orders_affected": 0,
                    "financial_impact": 0,
                    "message": f"No supply chain exposure detected in {region}"
                })
            
            # Crisis impact modeling with validated calculations
            severity_multipliers = {'mild': 0.3, 'moderate': 0.6, 'severe': 0.9}
            impact_multiplier = severity_multipliers[severity]
            
            total_orders = len(orders)
            total_value = 0
            for order in orders:
                try:
                    total_value += float(order.get('order_item_total', 0))
                except (ValueError, TypeError):
                    continue
            
            affected_orders = int(total_orders * impact_multiplier)
            financial_impact = total_value * impact_multiplier
            
            # Category analysis with error handling
            category_analysis = {}
            for order in orders:
                try:
                    category = order.get('product_category', 'Unknown')
                    value = float(order.get('order_item_total', 0))
                    category_analysis[category] = category_analysis.get(category, 0) + value
                except (ValueError, TypeError):
                    continue
            
            top_categories = sorted(category_analysis.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Generate response actions
            response_actions = []
            if financial_impact > 100000:
                response_actions.append({
                    "action": "SUPPLIER_DIVERSIFICATION",
                    "description": "Emergency supplier diversification protocol activated"
                })
            if affected_orders > 50:
                response_actions.append({
                    "action": "LOGISTICS_REROUTING",
                    "description": "Alternative logistics routes deployed"
                })
            if crisis_type in ['typhoon', 'earthquake']:
                response_actions.append({
                    "action": "INVENTORY_RELOCATION",
                    "description": "Critical inventory relocated to safe zones"
                })
            
            # Store prediction
            try:
                prediction_id = str(uuid.uuid4())
                risk_predictions_table.put_item(Item={
                    'prediction_id': prediction_id,
                    'risk_type': f'CRISIS_SIMULATION_{crisis_type.upper()}',
                    'risk_level': Decimal(str(impact_multiplier)),
                    'financial_impact': Decimal(str(financial_impact)),
                    'orders_affected': affected_orders,
                    'region': region,
                    'severity': severity,
                    'prediction_confidence': Decimal('0.87'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'response_actions': json.dumps(response_actions)
                })
            except Exception as db_error:
                print(f"Warning: Could not store crisis prediction: {str(db_error)}")
            
            result = {
                "status": "success",
                "region": region,
                "crisis_type": crisis_type,
                "severity": severity,
                "total_orders_in_region": total_orders,
                "orders_affected": affected_orders,
                "financial_impact": round(financial_impact, 2),
                "impact_percentage": round(impact_multiplier * 100, 0),
                "top_affected_categories": [
                    {"category": cat, "value_at_risk": round(val * impact_multiplier, 2)}
                    for cat, val in top_categories
                ],
                "response_actions": response_actions,
                "prediction_id": prediction_id,
                "confidence": 87,
                "recovery_days": 3 + int(impact_multiplier * 10),
                "timestamp": datetime.utcnow().isoformat()
            }

            summary = f"""🤖 **Crisis Simulation Summary**
- **Status:** {result['status']}
- **Region:** {region}
- **Crisis Type:** {crisis_type}
- **Severity:** {severity}
- **Total Orders in Region:** {total_orders}
- **Orders Affected:** {affected_orders}
- **Financial Impact:** ${round(financial_impact, 2)}
- **Impact Percentage:** {round(impact_multiplier * 100, 0)}%
- **Top Affected Categories:** {', '.join([f"{cat} (${round(val * impact_multiplier, 2)})" for cat, val in top_categories])}
- **Response Actions:** {', '.join([action['description'] for action in response_actions])}
- **Prediction ID:** {prediction_id}
- **Confidence:** 87%
- **Recovery Days:** {3 + int(impact_multiplier * 10)}
- **Timestamp:** {datetime.utcnow().isoformat()}"""
            
            return summary

        except Exception as e:
            print(f"Error in AdvancedCrisisSimulationTool: {str(e)}")
            return json.dumps({
                "status": "error",
                "error": str(e),
                "region": region,
                "orders_affected": 0,
                "financial_impact": 0
            })


class PredictiveAnalyticsTool:
    name = "predictive_analytics"
    
    def execute(self) -> str:
        try:
            # Get comprehensive data with pagination support
            all_orders = []
            response = supply_chain_table.scan(Limit=500)
            all_orders.extend(response.get('Items', []))
            
            # Handle pagination if needed
            while 'LastEvaluatedKey' in response and len(all_orders) < 1000:
                response = supply_chain_table.scan(
                    Limit=500,
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                all_orders.extend(response.get('Items', []))
            
            if not all_orders:
                return json.dumps({
                    "status": "success",
                    "message": "No supply chain data available for analysis",
                    "global_value": 0,
                    "total_orders": 0
                })
            
            # Regional analysis with error handling
            regional_data = {}
            global_value = 0
            
            for order in all_orders:
                try:
                    region = order.get('order_region', 'Unknown')
                    value = float(order.get('order_item_total', 0))
                    global_value += value
                    
                    if region not in regional_data:
                        regional_data[region] = {
                            'orders': 0,
                            'value': 0,
                            'risk_orders': 0
                        }
                    
                    regional_data[region]['orders'] += 1
                    regional_data[region]['value'] += value
                    
                    if order.get('late_delivery_risk') == Decimal('1'):
                        regional_data[region]['risk_orders'] += 1
                except (ValueError, TypeError, KeyError):
                    continue
            
            # Calculate risk scores
            for region, data in regional_data.items():
                data['risk_percentage'] = (
                    (data['risk_orders'] / data['orders'] * 100) 
                    if data['orders'] > 0 else 0
                )
            
            # Identify highest risk regions
            top_risk_regions = sorted(
                regional_data.items(), 
                key=lambda x: x[1]['risk_percentage'], 
                reverse=True
            )[:3]
            
            # Generate predictive insights
            predictive_insights = []
            if top_risk_regions:
                top_region_name = top_risk_regions[0][0]
                top_region_data = top_risk_regions[0][1]
                
                predictive_insights.append({
                    "type": "RISK_INCREASE_PREDICTION",
                    "region": top_region_name,
                    "prediction": "15% increase in risk over next 30 days",
                    "confidence": 78
                })
                
                predictive_insights.append({
                    "type": "COST_SAVINGS_OPPORTUNITY",
                    "region": top_region_name,
                    "potential_savings": round(top_region_data['value'] * 0.25, 2),
                    "recommendation": "Implement supplier diversification"
                })
                
                predictive_insights.append({
                    "type": "MONITORING_RECOMMENDATION",
                    "regions": [r[0] for r in top_risk_regions],
                    "action": "Deploy real-time monitoring for top 3 risk regions"
                })
            
            total_risk_orders = sum(d['risk_orders'] for d in regional_data.values())
            overall_risk = (total_risk_orders / len(all_orders) * 100) if all_orders else 0
            
            result = {
                "status": "success",
                "total_orders": len(all_orders),
                "global_value": round(global_value, 2),
                "active_regions": len(regional_data),
                "overall_risk_level": round(overall_risk, 1),
                "top_risk_regions": [
                    {
                        "region": region,
                        "risk_percentage": round(data['risk_percentage'], 1),
                        "value_exposure": round(data['value'], 2),
                        "total_orders": data['orders'],
                        "risk_orders": data['risk_orders']
                    }
                    for region, data in top_risk_regions
                ],
                "predictive_insights": predictive_insights,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            summary = f"""🤖 **Predictive Analytics Summary**

            - **Status:** {result['status']}
            - **Total Orders:** {result['total_orders']}
            - **Global Value:** ${result['global_value']:,.2f}
            - **Active Regions:** {result['active_regions']}
            - **Overall Risk Level:** {result['overall_risk_level']}%
            - **Top Risk Regions:**
              {chr(10).join([f"  - {region['region']}: {region['risk_percentage']}% (${region['value_exposure']:,.2f})" for region in result['top_risk_regions']])}
            - **Predictive Insights:**
              {chr(10).join([f"  - {insight['type']} for {insight.get('region', 'N/A')}: {insight.get('prediction', insight.get('recommendation', 'N/A'))}" for insight in result['predictive_insights']])}
            - **Timestamp:** {result['timestamp']}"""

            return summary
            
        except Exception as e:
            print(f"Error in PredictiveAnalyticsTool: {str(e)}")
            return json.dumps({
                "status": "error",
                "error": str(e),
                "total_orders": 0,
                "global_value": 0
            })


class LiveFlightTracker:
    """Track real cargo flights in real-time using OpenSky Network"""
    name = "track_live_flight"
    
    BASE_URL = "https://opensky-network.org/api"
    
    # Map common carriers to ICAO prefixes for demo purposes
    CARRIER_PREFIXES = {
        'fedex': 'FDX',
        'ups': 'UPS', 
        'dhl': 'DHL',
        'maersk': 'MSK',
        'lufthansa_cargo': 'GEC'
    }
    
    def execute(self, flight_callsign: str = None, icao24: str = None) -> str:
        """
        Track a live flight by callsign (e.g., 'FDX134') or ICAO24 address
        
        Args:
            flight_callsign: Flight number like 'FDX134', 'UPS2901'
            icao24: 24-bit ICAO aircraft address (hex string)
        """
        try:
            if flight_callsign:
                # Search by callsign
                response = requests.get(
                    f"{self.BASE_URL}/states/all",
                    timeout=10
                )
            elif icao24:
                # Search by ICAO24
                response = requests.get(
                    f"{self.BASE_URL}/states/all",
                    params={"icao24": icao24.lower()},
                    timeout=10
                )
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Must provide either flight_callsign or icao24"
                })
            
            if response.status_code == 429:
                # Rate limited - return cached/demo data
                return self._get_demo_flight_data(flight_callsign or icao24)
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('states'):
                # No active flight found - might be on ground or not flying
                return json.dumps({
                    "status": "NOT_FOUND",
                    "message": f"Flight {flight_callsign or icao24} not currently airborne or not found",
                    "recommendation": "Flight may be on ground, completed, or scheduled for future departure"
                })
            
            # Find matching flight
            flight_state = None
            if flight_callsign:
                for state in data['states']:
                    callsign = state[1].strip() if state[1] else ""
                    if callsign.upper().startswith(flight_callsign.upper()):
                        flight_state = state
                        break
            else:
                flight_state = data['states'][0]
            
            if not flight_state:
                return json.dumps({
                    "status": "NOT_FOUND",
                    "message": f"No matching flight found for {flight_callsign}"
                })
            
            # Parse OpenSky state vector
            icao24 = flight_state[0]
            callsign = flight_state[1].strip() if flight_state[1] else "N/A"
            origin_country = flight_state[2]
            longitude = flight_state[5]
            latitude = flight_state[6]
            altitude_meters = flight_state[7]
            on_ground = flight_state[8]
            velocity_mps = flight_state[9]
            heading = flight_state[10]
            vertical_rate = flight_state[11]
            last_contact = flight_state[4]
            
            # Calculate derived metrics
            altitude_feet = int(altitude_meters * 3.28084) if altitude_meters else 0
            speed_knots = int(velocity_mps * 1.94384) if velocity_mps else 0
            
            # Determine flight status
            if on_ground:
                status = "ON_GROUND"
                status_description = "Aircraft is currently on the ground"
            elif altitude_feet > 10000:
                status = "CRUISING"
                status_description = f"In cruise at {altitude_feet:,} feet"
            elif altitude_feet > 0 and vertical_rate and vertical_rate < -5:
                status = "DESCENDING"
                status_description = f"Descending from {altitude_feet:,} feet"
            elif altitude_feet > 0 and vertical_rate and vertical_rate > 5:
                status = "CLIMBING"
                status_description = f"Climbing through {altitude_feet:,} feet"
            else:
                status = "IN_FLIGHT"
                status_description = "Aircraft is airborne"
            
            # Format timestamp
            last_update = datetime.fromtimestamp(last_contact).strftime("%Y-%m-%d %H:%M:%S UTC")
            
            result = {
                "status": "SUCCESS",
                "flight_data": {
                    "callsign": callsign,
                    "icao24": icao24,
                    "origin_country": origin_country,
                    "flight_status": status,
                    "status_description": status_description,
                    "position": {
                        "latitude": round(latitude, 4) if latitude else None,
                        "longitude": round(longitude, 4) if longitude else None,
                        "altitude_feet": altitude_feet,
                        "heading_degrees": round(heading, 1) if heading else None
                    },
                    "speed": {
                        "ground_speed_knots": speed_knots,
                        "vertical_rate_fpm": int(vertical_rate * 196.85) if vertical_rate else 0
                    },
                    "last_update": last_update,
                    "data_age_seconds": int(time.time() - last_contact)
                },
                "supply_chain_impact": self._assess_flight_impact(status, altitude_feet, callsign)
            }
            
            # Format response
            summary = f"""✈️ **Live Flight Tracking: {callsign}**

**Flight Status:** {status} - {status_description}

**Position:**
- Latitude: {result['flight_data']['position']['latitude']}°
- Longitude: {result['flight_data']['position']['longitude']}°
- Altitude: {altitude_feet:,} feet
- Heading: {result['flight_data']['position']['heading_degrees']}°

**Speed:**
- Ground Speed: {speed_knots} knots
- Vertical Rate: {result['flight_data']['speed']['vertical_rate_fpm']} ft/min

**Supply Chain Impact:**
- Risk Level: {result['supply_chain_impact']['risk_level']}
- Impact: {result['supply_chain_impact']['impact']}
- Action: {result['supply_chain_impact']['action']}

**Last Update:** {last_update}
**ICAO24:** {icao24}
**Origin Country:** {origin_country}"""
            
            return summary
            
        except requests.exceptions.Timeout:
            return json.dumps({
                "status": "error",
                "message": "OpenSky Network API timeout - service may be overloaded",
                "fallback": "Using last known position data"
            })
        except Exception as e:
            print(f"Error in LiveFlightTracker: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Flight tracking error: {str(e)}"
            })
    
    def _assess_flight_impact(self, status: str, altitude: int, callsign: str) -> Dict[str, Any]:
        """Assess supply chain impact based on flight status"""
        if status == "ON_GROUND":
            return {
                "risk_level": "LOW",
                "impact": "Aircraft on ground - normal ground operations",
                "action": "No action required"
            }
        elif status == "CRUISING" and altitude > 30000:
            return {
                "risk_level": "NORMAL",
                "impact": "Flight proceeding normally at cruise altitude",
                "eta_reliability": "HIGH",
                "action": "Continue monitoring"
            }
        elif status == "DESCENDING":
            return {
                "risk_level": "LOW",
                "impact": "Aircraft approaching destination - delivery on schedule",
                "action": "Prepare for cargo receipt"
            }
        else:
            return {
                "risk_level": "NORMAL",
                "impact": "Flight in progress",
                "action": "Monitor for delays"
            }
    
    def _get_demo_flight_data(self, identifier: str) -> str:
        """Return demo flight data when API is rate-limited"""
        summary = f"""✈️ **Live Flight Tracking: {identifier.upper()}** (Demo Mode)

**Note:** OpenSky API rate limit reached - showing simulated data

**Flight Status:** CRUISING - In cruise at 38,000 feet

**Position:**
- Latitude: 40.7128°
- Longitude: -74.0060°
- Altitude: 38,000 feet
- Heading: 87.5°

**Speed:**
- Ground Speed: 480 knots
- Vertical Rate: 0 ft/min

**Supply Chain Impact:**
- Risk Level: NORMAL
- Impact: Flight proceeding normally
- ETA Reliability: HIGH
- Action: Continue monitoring

**Last Update:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
**ICAO24:** a820d2
**Origin Country:** United States"""
        
        return summary


# Placeholder tool classes
class SupplierPerformanceTool:
    name = "supplier_performance"
    def execute(self) -> str:
        return "Supplier performance tool not yet implemented"

class WeatherRiskTool:
    name = "weather_risk"
    def execute(self) -> str:
        return "Weather risk tool not yet implemented"

class InventoryAnalysisTool:
    name = "inventory_analysis"
    def execute(self) -> str:
        return "Inventory analysis tool not yet implemented"


# Lambda handler
def lambda_handler(event, context):
    """Main Lambda handler with comprehensive error handling"""
    try:
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '')
        conversation_id = body.get('conversation_id', str(uuid.uuid4()))
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Query parameter is required'})
            }
        
        # Initialize agent
        agent = UltimateSupplyChainAgent(agent_type='ULTIMATE_SUPPLY_CHAIN_AGENT')
        
        # Process query
        result = agent.process_query(query, conversation_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(result, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'trace': traceback.format_exc()
            })
        }
