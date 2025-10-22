# SearchExecutor Lambda - Supply Chain Search Intelligence
import json
import requests
import os
from datetime import datetime
from typing import Dict, List, Optional
import traceback

# Search API Configuration
SERPAPI_KEY = os.environ.get('SERPAPI_API_KEY', '')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')

def success_response(api_path: str, body_data: Dict, status_code: int = 200) -> Dict:
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'SearchActionGroup',
            'apiPath': api_path,
            'httpMethod': 'POST',
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(body_data)
                }
            }
        }
    }

def error_response(error_message: str, api_path: str = '', status_code: int = 500) -> Dict:
    print(f"ERROR for {api_path}: {error_message}")
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'SearchActionGroup',
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

def search_supply_chain(query: str, search_type: str = 'supply_chain') -> Dict:
    """Enhanced supply chain search with multiple APIs"""
    print(f"🔍 Searching supply chain: {query} (type: {search_type})")
    
    # Try SerpAPI first, then NewsAPI fallback
    try:
        if SERPAPI_KEY:
            result = search_serpapi(query, search_type)
            if result.get('results'):
                return success_response('/search-supply-chain', result)
    except Exception as e:
        print(f"SerpAPI failed: {str(e)}")
    
    # Fallback to NewsAPI for news searches
    try:
        if NEWS_API_KEY and search_type in ['news', 'supply_chain']:
            result = search_newsapi(query)
            if result.get('results'):
                return success_response('/search-supply-chain', result)
    except Exception as e:
        print(f"NewsAPI failed: {str(e)}")
    
    # Final fallback to demo data
    result = get_demo_search_data(query, search_type)
    return success_response('/search-supply-chain', result)

def search_serpapi(query: str, search_type: str) -> Dict:
    """Search using SerpAPI (Google scraping)"""
    enhanced_query = enhance_query_for_supply_chain(query, search_type)
    
    url = "https://serpapi.com/search"
    params = {
        'api_key': SERPAPI_KEY,
        'engine': 'google',
        'q': enhanced_query,
        'num': 10
    }
    
    if search_type == 'news':
        params['tbm'] = 'nws'  # News search
    
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    
    # Extract results based on search type
    if search_type == 'news':
        results = data.get('news_results', [])
    else:
        results = data.get('organic_results', [])
    
    formatted_results = []
    for result in results[:10]:
        formatted_results.append({
            'title': result.get('title', ''),
            'snippet': result.get('snippet', ''),
            'url': result.get('link', ''),
            'source': result.get('source', ''),
            'date': result.get('date', ''),
            'relevance_score': calculate_relevance(result, query)
        })
    
    return {
        'status': 'SUCCESS',
        'search_api': 'SerpAPI',
        'query': query,
        'search_type': search_type,
        'total_results': len(formatted_results),
        'results': formatted_results,
        'supply_chain_insights': extract_supply_chain_insights(formatted_results),
        'timestamp': datetime.utcnow().isoformat()
    }

def search_newsapi(query: str) -> Dict:
    """Search using NewsAPI for recent news"""
    enhanced_query = enhance_query_for_supply_chain(query, 'news')
    
    url = "https://newsapi.org/v2/everything"
    headers = {'X-API-Key': NEWS_API_KEY}
    params = {
        'q': enhanced_query,
        'sortBy': 'publishedAt',
        'pageSize': 10,
        'language': 'en'
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    articles = data.get('articles', [])
    
    formatted_results = []
    for article in articles:
        formatted_results.append({
            'title': article.get('title', ''),
            'snippet': article.get('description', ''),
            'url': article.get('url', ''),
            'source': article.get('source', {}).get('name', ''),
            'date': article.get('publishedAt', ''),
            'relevance_score': calculate_relevance(article, query)
        })
    
    return {
        'status': 'SUCCESS',
        'search_api': 'NewsAPI',
        'query': query,
        'search_type': 'news',
        'total_results': data.get('totalResults', len(formatted_results)),
        'results': formatted_results,
        'supply_chain_insights': extract_supply_chain_insights(formatted_results),
        'timestamp': datetime.utcnow().isoformat()
    }

def enhance_query_for_supply_chain(query: str, search_type: str) -> str:
    """Enhance search query for supply chain context"""
    
    supply_chain_terms = {
        'supply_chain': ' supply chain logistics shipping freight',
        'news': ' supply chain news latest updates',
        'vessel': ' ship vessel maritime port cargo',
        'flight': ' flight aircraft aviation cargo freight',
        'geopolitical': ' geopolitical disruption conflict strike sanctions'
    }
    
    enhancement = supply_chain_terms.get(search_type, ' supply chain')
    
    # Don't add if already present
    query_lower = query.lower()
    if not any(term.strip() in query_lower for term in enhancement.split()):
        query += enhancement
    
    return query

def calculate_relevance(result: Dict, query: str) -> float:
    """Calculate relevance score"""
    query_terms = query.lower().split()
    
    title = (result.get('title') or '').lower()
    snippet = (result.get('snippet') or result.get('description') or '').lower()
    
    score = 0.0
    
    for term in query_terms:
        if term in title:
            score += 2.0
        if term in snippet:
            score += 1.0
    
    # Bonus for supply chain keywords
    supply_keywords = ['supply chain', 'logistics', 'shipping', 'port', 'cargo', 'freight']
    content = title + ' ' + snippet
    
    for keyword in supply_keywords:
        if keyword in content:
            score += 0.5
    
    return round(score, 2)

def extract_supply_chain_insights(results: List[Dict]) -> Dict:
    """Extract supply chain insights from search results"""
    
    insights = {
        'disruption_indicators': [],
        'market_trends': [],
        'risk_factors': [],
        'opportunities': []
    }
    
    disruption_keywords = ['delay', 'strike', 'closure', 'disruption', 'shortage', 'congestion', 'blocked']
    trend_keywords = ['growth', 'increase', 'decrease', 'trend', 'market', 'demand', 'price']
    risk_keywords = ['risk', 'threat', 'warning', 'alert', 'concern', 'crisis']
    opportunity_keywords = ['opportunity', 'expansion', 'investment', 'new route', 'efficiency']
    
    for result in results[:5]:  # Analyze top 5 results
        content = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
        
        for keyword in disruption_keywords:
            if keyword in content:
                insights['disruption_indicators'].append({
                    'indicator': keyword,
                    'source': result.get('title', ''),
                    'url': result.get('url', ''),
                    'relevance': result.get('relevance_score', 0)
                })
                break
        
        for keyword in trend_keywords:
            if keyword in content:
                insights['market_trends'].append({
                    'trend': keyword,
                    'source': result.get('title', ''),
                    'url': result.get('url', ''),
                    'relevance': result.get('relevance_score', 0)
                })
                break
        
        for keyword in risk_keywords:
            if keyword in content:
                insights['risk_factors'].append({
                    'risk': keyword,
                    'source': result.get('title', ''),
                    'url': result.get('url', ''),
                    'relevance': result.get('relevance_score', 0)
                })
                break
        
        for keyword in opportunity_keywords:
            if keyword in content:
                insights['opportunities'].append({
                    'opportunity': keyword,
                    'source': result.get('title', ''),
                    'url': result.get('url', ''),
                    'relevance': result.get('relevance_score', 0)
                })
                break
    
    return insights

def search_vessel_news(vessel_identifier: str) -> Dict:
    """Search for vessel-specific news"""
    query = f"{vessel_identifier} vessel ship maritime news"
    result = search_supply_chain(query, 'vessel')
    
    # Update response for vessel-specific format
    if result.get('response', {}).get('responseBody', {}).get('application/json', {}).get('body'):
        body = json.loads(result['response']['responseBody']['application/json']['body'])
        body['vessel_identifier'] = vessel_identifier
        result['response']['responseBody']['application/json']['body'] = json.dumps(body)
    
    return result

def search_flight_news(flight_identifier: str) -> Dict:
    """Search for flight-specific news"""
    query = f"{flight_identifier} flight airline aviation news"
    result = search_supply_chain(query, 'flight')
    
    # Update response for flight-specific format
    if result.get('response', {}).get('responseBody', {}).get('application/json', {}).get('body'):
        body = json.loads(result['response']['responseBody']['application/json']['body'])
        body['flight_identifier'] = flight_identifier
        result['response']['responseBody']['application/json']['body'] = json.dumps(body)
    
    return result

def search_geopolitical_events(region: str, event_type: str = 'all') -> Dict:
    """Search for geopolitical events"""
    query = f"{region} geopolitical events disruption supply chain {event_type}"
    result = search_supply_chain(query, 'geopolitical')
    
    # Update response for geopolitical-specific format
    if result.get('response', {}).get('responseBody', {}).get('application/json', {}).get('body'):
        body = json.loads(result['response']['responseBody']['application/json']['body'])
        body['region'] = region
        body['event_type'] = event_type
        result['response']['responseBody']['application/json']['body'] = json.dumps(body)
    
    return result

def search_market_intelligence(topic: str, time_period: str = 'month') -> Dict:
    """Search for market intelligence"""
    query = f"{topic} market intelligence trends {time_period}"
    result = search_supply_chain(query, 'supply_chain')
    
    # Update response for market intelligence format
    if result.get('response', {}).get('responseBody', {}).get('application/json', {}).get('body'):
        body = json.loads(result['response']['responseBody']['application/json']['body'])
        body['topic'] = topic
        body['time_period'] = time_period
        result['response']['responseBody']['application/json']['body'] = json.dumps(body)
    
    return result

def get_demo_search_data(query: str, search_type: str) -> Dict:
    """Generate demo search data when APIs fail"""
    
    demo_results = [
        {
            'title': f'Supply Chain Update: {query}',
            'snippet': f'Latest developments in {query} affecting global supply chains. Market analysis shows potential disruptions and opportunities.',
            'url': 'https://example.com/supply-chain-news',
            'source': 'Supply Chain Intelligence',
            'date': datetime.utcnow().isoformat(),
            'relevance_score': 8.5
        },
        {
            'title': f'Market Analysis: {query} Impact',
            'snippet': f'Industry experts analyze the impact of {query} on logistics and transportation networks worldwide.',
            'url': 'https://example.com/market-analysis',
            'source': 'Logistics Today',
            'date': datetime.utcnow().isoformat(),
            'relevance_score': 7.2
        },
        {
            'title': f'Breaking: {query} Developments',
            'snippet': f'Recent developments in {query} create new challenges and opportunities for supply chain managers.',
            'url': 'https://example.com/breaking-news',
            'source': 'Trade News',
            'date': datetime.utcnow().isoformat(),
            'relevance_score': 6.8
        }
    ]
    
    return {
        'status': 'SUCCESS',
        'search_api': 'Demo Data',
        'query': query,
        'search_type': search_type,
        'total_results': len(demo_results),
        'results': demo_results,
        'supply_chain_insights': {
            'disruption_indicators': [{'indicator': 'potential disruption', 'source': demo_results[0]['title']}],
            'market_trends': [{'trend': 'market volatility', 'source': demo_results[1]['title']}],
            'risk_factors': [{'risk': 'supply chain risk', 'source': demo_results[2]['title']}],
            'opportunities': [{'opportunity': 'optimization potential', 'source': demo_results[0]['title']}]
        },
        'timestamp': datetime.utcnow().isoformat()
    }

def lambda_handler(event, context):
    """Lambda handler for search functionality"""
    print(f"📥 SearchExecutor invoked: {json.dumps(event)}")
    
    try:
        api_path = event.get('apiPath', '')
        request_body = event.get('requestBody', {}).get('content', {}).get('application/json', {})
        properties = request_body.get('properties', [])
        
        # Extract parameters
        params = {p['name']: p['value'] for p in properties}
        
        if api_path == '/search-supply-chain':
            query = params.get('query')
            search_type = params.get('search_type', 'supply_chain')
            
            if not query:
                return error_response("query parameter required", api_path, 400)
            
            return search_supply_chain(query, search_type)
            
        elif api_path == '/search-vessel-news':
            vessel_identifier = params.get('vessel_identifier')
            
            if not vessel_identifier:
                return error_response("vessel_identifier parameter required", api_path, 400)
            
            return search_vessel_news(vessel_identifier)
            
        elif api_path == '/search-flight-news':
            flight_identifier = params.get('flight_identifier')
            
            if not flight_identifier:
                return error_response("flight_identifier parameter required", api_path, 400)
            
            return search_flight_news(flight_identifier)
            
        elif api_path == '/search-geopolitical':
            region = params.get('region')
            event_type = params.get('event_type', 'all')
            
            if not region:
                return error_response("region parameter required", api_path, 400)
            
            return search_geopolitical_events(region, event_type)
            
        elif api_path == '/search-market-intelligence':
            topic = params.get('topic')
            time_period = params.get('time_period', 'month')
            
            if not topic:
                return error_response("topic parameter required", api_path, 400)
            
            return search_market_intelligence(topic, time_period)
            
        else:
            return error_response(f"Unknown API path: {api_path}", api_path, 404)
            
    except Exception as e:
        print(f"❌ SearchExecutor error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return error_response(f"Internal server error: {str(e)}", event.get('apiPath', ''), 500)
