import json
import boto3
import uuid
from datetime import datetime

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Your Bedrock Agent details
AGENT_ID = "CXLLJNZOCS"
AGENT_ALIAS_ID = "TSTALIASID"

def lambda_handler(event, context):
    """
    API Gateway wrapper for Bedrock Agent Runtime
    """
    
    # CORS headers
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    }
    
    # Handle OPTIONS preflight request
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': ''
        }
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '')
        session_id = body.get('sessionId', f'session-{uuid.uuid4()}')
        
        if not query:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Query parameter is required'})
            }
        
        print(f"🤖 Invoking Bedrock Agent: {AGENT_ID}")
        print(f"📝 Query: {query}")
        print(f"🔑 Session: {session_id}")
        
        start_time = datetime.utcnow()
        
        # Invoke Bedrock Agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=query
        )
        
        # Stream and aggregate response
        full_response = ""
        tools_called = []
        event_stream = response['completion']
        
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    full_response += chunk['bytes'].decode('utf-8')
            
            # Extract trace information
            if 'trace' in event:
                trace = event['trace'].get('trace', {})
                if 'orchestrationTrace' in trace:
                    orch = trace['orchestrationTrace']
                    if 'invocationInput' in orch:
                        action = orch['invocationInput'].get('actionGroupInvocationInput', {})
                        if action:
                            tools_called.append({
                                'tool_name': action.get('actionGroupName', 'Unknown'),
                                'function': action.get('function', 'Unknown'),
                                'parameters': action.get('parameters', [])
                            })
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        print(f"✅ Agent response received ({duration_ms}ms)")
        print(f"🔧 Tools called: {len(tools_called)}")
        
        # Extract autonomous decision traces
        autonomous_traces = []
        for event_data in event_stream:
            if 'trace' in event_data:
                trace = event_data['trace'].get('trace', {})
                orchestration = trace.get('orchestrationTrace', {})
                
                # Extract reasoning steps
                if 'rationale' in orchestration:
                    rationale = orchestration['rationale']
                    autonomous_traces.append({
                        'type': 'agent_reasoning',
                        'text': rationale.get('text', ''),
                        'trace_id': rationale.get('traceId', '')
                    })
                
                # Extract tool invocations
                if 'invocationInput' in orchestration:
                    invocation = orchestration['invocationInput']
                    if 'actionGroupInvocationInput' in invocation:
                        action_group = invocation['actionGroupInvocationInput']
                        autonomous_traces.append({
                            'type': 'autonomous_tool_call',
                            'action_group': action_group.get('actionGroupName', ''),
                            'function': action_group.get('function', ''),
                            'autonomous': True
                        })
        
        result = {
            'response': full_response,
            'tools_called': tools_called,
            'autonomous_traces': autonomous_traces,
            'autonomous_actions': len([t for t in autonomous_traces if t.get('autonomous')]),
            'agent_intelligence_score': calculate_intelligence_score(tools_called, autonomous_traces),
            'duration_ms': duration_ms
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }



def calculate_intelligence_score(tools_called, autonomous_traces):
    """Calculate how intelligent the agent's response was"""
    base_score = 50
    tool_bonus = len(tools_called) * 10
    autonomous_bonus = len([t for t in autonomous_traces if t.get('autonomous')]) * 15
    reasoning_bonus = len([t for t in autonomous_traces if t['type'] == 'agent_reasoning']) * 5
    
    return min(base_score + tool_bonus + autonomous_bonus + reasoning_bonus, 100)
