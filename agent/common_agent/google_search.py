import requests
import json
from urllib.parse import quote
from bs4 import BeautifulSoup
import re
import os
import json
from agent.common_agent import common_agent
from agent.agents import company_agent_template
from agent.common_agent import tokanize, api_key
from agent.agents import text_util_agent, company_agent

import os
import json
from datetime import datetime

import tldextract
from urllib.parse import urlparse


def score_company_website(url):
    """
    Score a URL based on how likely it is to be a main company website
    """
    score = 0
    parsed = urlparse(url)
    domain_info = tldextract.extract(url)

    domain = domain_info.domain.lower()
    subdomain = domain_info.subdomain.lower()
    suffix = domain_info.suffix

    # Negative indicators (penalize heavily)
    negative_indicators = {
        'social_media': ['facebook', 'twitter', 'linkedin', 'instagram'],
        'directories': ['yellowpages', 'yelp', 'angieslist', 'houzz'],
        'job_sites': ['glassdoor', 'indeed', 'monster'],
        'financial': ['crunchbase', 'bloomberg', 'reuters'],
        'forums': ['bbs', 'forum', 'community'],
        'events': ['anuga', 'exhibitor', 'expo', 'trade-show'],
        'other': ['wikipedia', 'amazon', 'ebay', 'alibaba']
    }

    for category, indicators in negative_indicators.items():
        for indicator in indicators:
            if indicator in domain or indicator in subdomain:
                score -= 100  # Heavy penalty

    # Path analysis
    path = parsed.path.lower()
    if any(word in path for word in ['exhibitor', 'exhibitors', 'directory', 'list', 'company']):
        score -= 50

    # Positive indicators
    if suffix in ['com', 'org', 'net']:
        score += 10

    if not subdomain or subdomain in ['www', '']:
        score += 5

    if len(path) <= 1 or path == '/':
        score += 20  # Homepage bonus

    if not parsed.query:
        score += 10  # No query parameters

    # Domain length (shorter domains are often better)
    if len(domain) < 15:
        score += 5

    return score


def find_best_company_website(urls):
    """
    Find the best company website from a list using multi-criteria scoring
    """
    if not urls:
        return None

    scored_urls = [(score_company_website(url), url) for url in urls]
    scored_urls.sort(reverse=True)

    # Return the highest scored URL, but only if score is positive
    best_score, best_url = scored_urls[0]

    if best_score > 0:
        return best_url
    else:
        # If all scores are negative, return the simplest URL
        return min(urls, key=lambda x: len(urlparse(x).path))







def google_search_single(query, api_token=api_key.SERPAPI_API_KEY, country="us", language="en"):
    """
    Perform a single Google search and return results

    Args:
        query (str): Search term
        api_token (str): Your Bright Data Bearer token
        country (str): Country code
        language (str): Language code

    Returns:
        dict: Search results with parsed data
    """

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    encoded_query = quote(query)

    data = {
        "zone": "serp_api_1",
        "url": f"https://www.google.com/search?q={encoded_query}&hl={language}&gl={country}",
        "format": "raw"
    }

    try:
        print(f"🔍 Searching for: {query}")
        response = requests.post(
            "https://api.brightdata.com/request",
            json=data,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}

        html_content = response.text

        # Create organized folder structure
        base_folder = "search_results"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = query.replace(' ', '_').replace('/', '_')[:50]  # Safe filename

        # Main search results folder
        os.makedirs(base_folder, exist_ok=True)

        # Query-specific folder
        query_folder = os.path.join(base_folder, safe_query)
        os.makedirs(query_folder, exist_ok=True)

        # Timestamp-specific subfolder for multiple searches of same query
        timestamp_folder = os.path.join(query_folder, timestamp)
        os.makedirs(timestamp_folder, exist_ok=True)

        # Save raw HTML in timestamp folder
        html_filename = f"raw_results_{safe_query}.html"
        html_file_path = os.path.join(timestamp_folder, html_filename)

        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        #print(f"📁 Raw HTML saved to: {html_file_path}")

        # Parse the HTML
        parsed_results = parse_google_results(html_content, query)

        # Save parsed results to JSON in timestamp folder
        json_filename = f"parsed_results_{safe_query}.json"
        json_file_path = os.path.join(timestamp_folder, json_filename)

        results = {
            "success": True,
            "query": query,
            "timestamp": timestamp,
            "country": country,
            "language": language,
            "raw_html_path": html_file_path,
            "parsed_results": parsed_results
        }

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        #print(f"💾 Parsed results saved to: {json_file_path}")

        # Also save a summary in the main query folder (overwrites previous summary)
        summary_file_path = os.path.join(query_folder, f"latest_results_{safe_query}.json")
        with open(summary_file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        #print(f"📋 Latest results summary saved to: {summary_file_path}")

        return results

    except Exception as e:
        return {"success": False, "error": str(e)}


def parse_google_results(html_content, query):
    """Parse Google search results from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')

    results = {
        "query": query,
        "total_results": "",
        "organic_results": [],
        "knowledge_graph": {},
        "related_searches": []
    }

    # Extract total results count
    result_stats = soup.find('div', {'id': 'result-stats'})
    if result_stats:
        results["total_results"] = result_stats.get_text().strip()

    # Extract organic results
    organic_results = []

    # Look for main result containers
    result_containers = soup.find_all('div', class_='g')

    for i, container in enumerate(result_containers[:10]):
        result_data = extract_single_result(container)
        if result_data:
            result_data["rank"] = i + 1
            organic_results.append(result_data)

    # Alternative selectors if first method doesn't work
    if not organic_results:
        alternative_containers = soup.find_all('div', class_=re.compile('MjjYud|tF2Cxc'))
        for i, container in enumerate(alternative_containers[:10]):
            result_data = extract_single_result(container)
            if result_data:
                result_data["rank"] = i + 1
                organic_results.append(result_data)

    results["organic_results"] = organic_results

    return results


def extract_single_result(container):
    """Extract data from a single search result container"""
    try:
        # Title
        title_elem = container.find('h3') or container.find('a')
        title = title_elem.get_text().strip() if title_elem else ""

        # URL
        link_elem = container.find('a')
        url = link_elem.get('href', '') if link_elem else ""
        # Clean Google redirect URL
        if url.startswith('/url?q='):
            url = url.split('/url?q=')[1].split('&')[0]

        # Description
        desc_elem = container.find('span', class_=re.compile('aCOpRe|LL4CDc|VwiC3b'))
        description = desc_elem.get_text().strip() if desc_elem else ""

        if title and url:
            return {
                "title": title,
                "url": url,
                "description": description
            }
    except Exception as e:
        print(f"Error extracting result: {e}")

    return None


def print_search_results(results):
    """Print formatted search results"""
    if not results["success"]:
        print(f"❌ Search failed: {results['error']}")
        return

    parsed = results["parsed_results"]

    print(f"\n✅ Search successful!")
    print(f"📊 Query: {parsed['query']}")
    print(f"📈 Total results: {parsed['total_results']}")
    print(f"🔢 Found {len(parsed['organic_results'])} organic results")

    print(f"\n🏆 TOP RESULTS:")
    print("=" * 80)

    for i, res in enumerate(parsed['organic_results'][:5]):
        print(f"\n{i + 1}. {res['title']}")
        print(f"   🔗 URL: {res['url']}")
        if res['description']:
            print(f"   📝 {res['description'][:150]}...")
        print("-" * 80)


