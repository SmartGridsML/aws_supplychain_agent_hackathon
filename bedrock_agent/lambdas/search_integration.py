# Search API Integration for Supply Chain Intelligence
import json
import requests
import os
from datetime import datetime
from typing import Dict, List, Optional

# Search API Configuration
GOOGLE_SEARCH_API_KEY = os.environ.get('GOOGLE_SEARCH_API_KEY', '')
GOOGLE_SEARCH_ENGINE_ID = os.environ.get('GOOGLE_SEARCH_ENGINE_ID', '')
BING_SEARCH_API_KEY = os.environ.get('BING_SEARCH_API_KEY', '')
SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')

def search_supply_chain_intelligence(query: str, search_type: str = 'general') -> Dict:
    """Enhanced search for supply chain intelligence"""
    
    # Try multiple search APIs in order of preference
    search_apis = [
        ('Google', search_google_custom),
        ('Bing', search_bing),
        ('SerpAPI', search_serpapi),
        ('DuckDuckGo', search_duckduckgo_fallback)
    ]
    
    for api_name, api_func in search_apis:
        try:
            print(f"🔍 Trying {api_name} search...")
            result = api_func(query, search_type)
            if result and result.get('results'):
                print(f"✅ Search success with {api_name}")
                return format_search_response(result, api_name, query)
        except Exception as e:
            print(f"❌ {api_name} search failed: {str(e)}")
            continue
    
    # All searches failed
    return {
        'status': 'ERROR',
        'message': 'All search APIs failed',
        'query': query,
        'results': []
    }

def search_google_custom(query: str, search_type: str) -> Dict:
    """Google Custom Search API"""
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        raise Exception("Google Search API credentials not configured")
    
    # Enhance query based on search type
    enhanced_query = enhance_search_query(query, search_type)
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_SEARCH_API_KEY,
        'cx': GOOGLE_SEARCH_ENGINE_ID,
        'q': enhanced_query,
        'num': 10,
        'dateRestrict': 'm1'  # Last month for recent news
    }
    
    if search_type == 'news':
        params['tbm'] = 'nws'  # News search
    elif search_type == 'supply_chain':
        params['q'] += ' supply chain logistics shipping'
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    return {
        'results': data.get('items', []),
        'total_results': data.get('searchInformation', {}).get('totalResults', 0)
    }

def search_bing(query: str, search_type: str) -> Dict:
    """Bing Search API"""
    if not BING_SEARCH_API_KEY:
        raise Exception("Bing Search API key not configured")
    
    enhanced_query = enhance_search_query(query, search_type)
    
    if search_type == 'news':
        url = "https://api.bing.microsoft.com/v7.0/news/search"
    else:
        url = "https://api.bing.microsoft.com/v7.0/search"
    
    headers = {'Ocp-Apim-Subscription-Key': BING_SEARCH_API_KEY}
    params = {
        'q': enhanced_query,
        'count': 10,
        'mkt': 'en-US'
    }
    
    if search_type == 'supply_chain':
        params['q'] += ' supply chain logistics shipping'
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if search_type == 'news':
        results = data.get('value', [])
    else:
        results = data.get('webPages', {}).get('value', [])
    
    return {
        'results': results,
        'total_results': len(results)
    }

def search_serpapi(query: str, search_type: str) -> Dict:
    """SerpAPI (Google scraping service)"""
    if not SERPAPI_KEY:
        raise Exception("SerpAPI key not configured")
    
    enhanced_query = enhance_search_query(query, search_type)
    
    url = "https://serpapi.com/search"
    params = {
        'api_key': SERPAPI_KEY,
        'engine': 'google',
        'q': enhanced_query,
        'num': 10
    }
    
    if search_type == 'news':
        params['tbm'] = 'nws'
    elif search_type == 'supply_chain':
        params['q'] += ' supply chain logistics shipping'
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    results = data.get('organic_results', []) or data.get('news_results', [])
    
    return {
        'results': results,
        'total_results': len(results)
    }

def search_duckduckgo_fallback(query: str, search_type: str) -> Dict:
    """DuckDuckGo fallback (free, no API key needed)"""
    # DuckDuckGo Instant Answer API (limited but free)
    enhanced_query = enhance_search_query(query, search_type)
    
    url = "https://api.duckduckgo.com/"
    params = {
        'q': enhanced_query,
        'format': 'json',
        'no_html': '1',
        'skip_disambig': '1'
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    # Extract relevant results
    results = []
    
    # Add abstract if available
    if data.get('Abstract'):
        results.append({
            'title': 'DuckDuckGo Summary',
            'snippet': data['Abstract'],
            'link': data.get('AbstractURL', ''),
            'source': 'DuckDuckGo'
        })
    
    # Add related topics
    for topic in data.get('RelatedTopics', [])[:5]:
        if isinstance(topic, dict) and topic.get('Text'):
            results.append({
                'title': topic.get('Text', '')[:100] + '...',
                'snippet': topic.get('Text', ''),
                'link': topic.get('FirstURL', ''),
                'source': 'DuckDuckGo'
            })
    
    return {
        'results': results,
        'total_results': len(results)
    }

def enhance_search_query(query: str, search_type: str) -> str:
    """Enhance search query based on type and context"""
    
    if search_type == 'supply_chain':
        # Add supply chain specific terms
        supply_chain_terms = [
            'supply chain', 'logistics', 'shipping', 'freight', 
            'cargo', 'transportation', 'port', 'maritime'
        ]
        
        # Check if query already contains supply chain terms
        query_lower = query.lower()
        has_supply_terms = any(term in query_lower for term in supply_chain_terms)
        
        if not has_supply_terms:
            query += ' supply chain logistics'
    
    elif search_type == 'news':
        # Add recent news terms
        query += ' news latest updates'
    
    elif search_type == 'vessel':
        # Add maritime specific terms
        query += ' ship vessel maritime AIS tracking'
    
    elif search_type == 'flight':
        # Add aviation specific terms
        query += ' flight aircraft aviation tracking'
    
    elif search_type == 'geopolitical':
        # Add geopolitical terms
        query += ' geopolitical events disruption conflict strike'
    
    return query

def format_search_response(search_result: Dict, api_name: str, original_query: str) -> Dict:
    """Format search results for consistent output"""
    
    results = search_result.get('results', [])
    formatted_results = []
    
    for result in results[:10]:  # Limit to top 10 results
        formatted_result = {
            'title': extract_title(result),
            'snippet': extract_snippet(result),
            'url': extract_url(result),
            'source': extract_source(result),
            'relevance_score': calculate_relevance(result, original_query)
        }
        
        # Add publication date if available
        pub_date = extract_publication_date(result)
        if pub_date:
            formatted_result['published_date'] = pub_date
        
        formatted_results.append(formatted_result)
    
    # Sort by relevance score
    formatted_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    return {
        'status': 'SUCCESS',
        'search_api': api_name,
        'query': original_query,
        'total_results': search_result.get('total_results', len(results)),
        'results_count': len(formatted_results),
        'results': formatted_results,
        'search_timestamp': datetime.utcnow().isoformat(),
        'supply_chain_insights': extract_supply_chain_insights(formatted_results)
    }

def extract_title(result: Dict) -> str:
    """Extract title from search result"""
    return (result.get('title') or 
            result.get('name') or 
            result.get('headline') or 
            'No title available')

def extract_snippet(result: Dict) -> str:
    """Extract snippet/description from search result"""
    return (result.get('snippet') or 
            result.get('description') or 
            result.get('summary') or 
            result.get('abstract') or
            result.get('content', '')[:200] + '...')

def extract_url(result: Dict) -> str:
    """Extract URL from search result"""
    return (result.get('link') or 
            result.get('url') or 
            result.get('displayLink') or 
            result.get('formattedUrl') or 
            '')

def extract_source(result: Dict) -> str:
    """Extract source from search result"""
    return (result.get('source') or 
            result.get('displayLink') or 
            result.get('cite') or 
            'Unknown source')

def extract_publication_date(result: Dict) -> Optional[str]:
    """Extract publication date if available"""
    return (result.get('datePublished') or 
            result.get('publishedAt') or 
            result.get('date'))

def calculate_relevance(result: Dict, query: str) -> float:
    """Calculate relevance score based on query terms"""
    query_terms = query.lower().split()
    
    title = extract_title(result).lower()
    snippet = extract_snippet(result).lower()
    
    score = 0.0
    
    # Check title matches (higher weight)
    for term in query_terms:
        if term in title:
            score += 2.0
        if term in snippet:
            score += 1.0
    
    # Bonus for supply chain related content
    supply_chain_keywords = [
        'supply chain', 'logistics', 'shipping', 'freight', 'cargo',
        'port', 'maritime', 'vessel', 'flight', 'transportation'
    ]
    
    content = (title + ' ' + snippet).lower()
    for keyword in supply_chain_keywords:
        if keyword in content:
            score += 0.5
    
    return score

def extract_supply_chain_insights(results: List[Dict]) -> Dict:
    """Extract supply chain specific insights from search results"""
    
    insights = {
        'disruption_indicators': [],
        'market_trends': [],
        'risk_factors': [],
        'opportunities': []
    }
    
    # Keywords for different categories
    disruption_keywords = ['delay', 'strike', 'closure', 'disruption', 'shortage', 'congestion']
    trend_keywords = ['growth', 'increase', 'decrease', 'trend', 'market', 'demand']
    risk_keywords = ['risk', 'threat', 'warning', 'alert', 'concern', 'issue']
    opportunity_keywords = ['opportunity', 'expansion', 'investment', 'new', 'launch']
    
    for result in results:
        content = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
        
        # Check for disruption indicators
        for keyword in disruption_keywords:
            if keyword in content:
                insights['disruption_indicators'].append({
                    'keyword': keyword,
                    'source': result.get('title', ''),
                    'url': result.get('url', '')
                })
        
        # Check for market trends
        for keyword in trend_keywords:
            if keyword in content:
                insights['market_trends'].append({
                    'keyword': keyword,
                    'source': result.get('title', ''),
                    'url': result.get('url', '')
                })
        
        # Check for risk factors
        for keyword in risk_keywords:
            if keyword in content:
                insights['risk_factors'].append({
                    'keyword': keyword,
                    'source': result.get('title', ''),
                    'url': result.get('url', '')
                })
        
        # Check for opportunities
        for keyword in opportunity_keywords:
            if keyword in content:
                insights['opportunities'].append({
                    'keyword': keyword,
                    'source': result.get('title', ''),
                    'url': result.get('url', '')
                })
    
    # Limit results and remove duplicates
    for category in insights:
        insights[category] = insights[category][:5]  # Top 5 per category
    
    return insights

# Integration with existing tracking executor
def add_search_to_tracking_executor():
    """Add search functionality to existing tracking executor"""
    
    search_functions = {
        '/search-supply-chain': search_supply_chain_general,
        '/search-vessel-news': search_vessel_news,
        '/search-flight-news': search_flight_news,
        '/search-geopolitical': search_geopolitical_events,
        '/search-market-intelligence': search_market_intelligence
    }
    
    return search_functions

def search_supply_chain_general(query: str) -> Dict:
    """General supply chain search"""
    return search_supply_chain_intelligence(query, 'supply_chain')

def search_vessel_news(vessel_identifier: str) -> Dict:
    """Search for news about specific vessel"""
    query = f"{vessel_identifier} vessel ship maritime news"
    return search_supply_chain_intelligence(query, 'news')

def search_flight_news(flight_identifier: str) -> Dict:
    """Search for news about specific flight or airline"""
    query = f"{flight_identifier} flight airline aviation news"
    return search_supply_chain_intelligence(query, 'news')

def search_geopolitical_events(region: str) -> Dict:
    """Search for geopolitical events in specific region"""
    query = f"{region} geopolitical events disruption supply chain"
    return search_supply_chain_intelligence(query, 'geopolitical')

def search_market_intelligence(topic: str) -> Dict:
    """Search for market intelligence and trends"""
    query = f"{topic} market intelligence trends supply chain"
    return search_supply_chain_intelligence(query, 'supply_chain')
