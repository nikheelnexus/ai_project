from common_script import common
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
import socket
from urllib.parse import urlparse
import requests
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import sys


def format_website_url(url):
    """Format and validate the website URL"""
    if not url:
        return None

    # Remove whitespace and quotes
    url = url.strip().strip("'\"")

    # Remove any duplicate https:// or http://
    if url.startswith(('https://https://', 'http://http://', 'https://http://', 'http://https://')):
        # Find the second occurrence
        if 'https://' in url[8:]:
            url = 'https://' + url.split('https://', 2)[2]
        elif 'http://' in url[7:]:
            url = 'http://' + url.split('http://', 2)[2]

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    return url


import socket
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import requests
import logging

# Set up logging
logger = logging.getLogger(__name__)

SOCIAL_MEDIA_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com",
    "tiktok.com", "youtube.com", "snapchat.com", "pinterest.com", "reddit.com",
    "tumblr.com", "whatsapp.com", "telegram.org", "discord.com", "twitch.tv",
    "vk.com", "weibo.com", "wechat.com", "line.me", "quora.com",
    "medium.com", "threads.net", "mastodon.social", "bsky.app"
}


def is_social_media(website: str) -> bool:
    if not website:
        return False

    # Clean the URL
    website = website.lower().strip()
    website = website.replace("https://", "").replace("http://", "").replace("www.", "")

    # Extract the domain (remove paths)
    domain = website.split("/")[0]

    return domain in SOCIAL_MEDIA_DOMAINS


def check_link_status(
        url: str,
        timeout: int = 15,
        verify_ssl: bool = True,
        follow_redirects: bool = True,
        retry_attempts: int = 2,
        custom_headers: Optional[Dict] = None,
        try_alternatives: bool = True,
        max_redirects: int = 10,
        check_soft_404: bool = True,
        adaptive_timeout: bool = True,
        min_timeout: int = 10,
        max_timeout: int = 30,
        slow_response_threshold: int = 5,
        progress_callback: Optional[callable] = None,
        verbose: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Comprehensive link checking function with progress reporting
    """

    def report_progress(step: str, details: dict = None):
        """Report progress through callback"""
        if progress_callback:
            progress_callback({
                'step': step,
                'url': url,
                'timestamp': datetime.now(),
                'details': details or {}
            })
        if verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {step}: {url} - {details if details else ''}")

    # Helper function to format URLs if needed
    def format_website_url(url_str: str) -> str:
        """Basic URL formatting"""
        url_str = url_str.strip()
        if url_str.startswith('http://'):
            url_str = url_str[7:]
        elif url_str.startswith('https://'):
            url_str = url_str[8:]
        if url_str.startswith('www.'):
            url_str = url_str[4:]
        return url_str.strip('/')

    # Report initial step
    report_progress('starting', {'original_url': url})

    url = format_website_url(url)
    original_url = url

    # Ensure URL has scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    result = {
        'url': url,
        'original_url': original_url,
        'status': 'unknown',
        'code': None,
        'message': '',
        'response_time': None,
        'final_url': None,
        'error': None,
        'is_working': False,
        'retry_count': 0,
        'content_type': None,
        'content_length': None,
        'redirect_history': [],
        'headers': None,
        'is_alternative': False,
        'alternatives_tried': [],
        'adaptive_timeout_used': False,
        'timeout_adjusted_to': None,
        'ssl_bypassed': False,  # Track if SSL was bypassed
        'ssl_warning': None  # Store SSL warning message
    }

    # Basic URL validation
    report_progress('validating_url')
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            result.update({
                'status': 'invalid',
                'message': 'Invalid URL format',
                'is_working': False
            })
            report_progress('validation_failed', {'error': 'Invalid URL format'})
            return False, result
    except Exception as e:
        result.update({
            'status': 'invalid',
            'message': f'Invalid URL format: {str(e)[:100]}',
            'error': str(e),
            'is_working': False
        })
        report_progress('validation_failed', {'error': str(e)})
        return False, result

    # DNS resolution check with retry
    report_progress('dns_resolution', {'domain': parsed.netloc})
    dns_resolved = False
    resolved_domain = parsed.netloc

    try:
        socket.setdefaulttimeout(5)
        socket.gethostbyname(resolved_domain)
        dns_resolved = True
        report_progress('dns_resolved', {'domain': resolved_domain})
    except socket.gaierror:
        if resolved_domain.startswith('www.'):
            try:
                socket.gethostbyname(resolved_domain[4:])
                resolved_domain = resolved_domain[4:]
                dns_resolved = True
                url = f"{parsed.scheme}://{resolved_domain}{parsed.path}"
                parsed = urlparse(url)
                report_progress('dns_resolved_alt', {'domain': resolved_domain})
            except socket.gaierror:
                pass
    except socket.timeout:
        result.update({
            'status': 'dns_timeout',
            'message': 'DNS resolution timed out',
            'is_working': False
        })
        report_progress('dns_timeout', {'domain': resolved_domain})
        return False, result
    finally:
        socket.setdefaulttimeout(None)

    if not dns_resolved:
        result.update({
            'status': 'broken',
            'message': 'DNS resolution failed - domain does not exist',
            'is_working': False
        })
        report_progress('dns_failed', {'domain': resolved_domain})
        return False, result

    # Enhanced headers for modern websites
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    if custom_headers:
        default_headers.update(custom_headers)

    # Generate alternative URL formats
    alternative_urls = []
    if try_alternatives:
        report_progress('generating_alternatives')
        parsed = urlparse(url)
        base_domain = parsed.netloc
        path = parsed.path if parsed.path else '/'
        query = f"?{parsed.query}" if parsed.query else ''
        fragment = f"#{parsed.fragment}" if parsed.fragment else ''

        alternatives = []

        # 1. Try with/without trailing slash
        if not path.endswith('/'):
            alternatives.append(f"{parsed.scheme}://{base_domain}{path}/{query}{fragment}")
        else:
            alternatives.append(f"{parsed.scheme}://{base_domain}{path.rstrip('/')}{query}{fragment}")

        # 2. Try with/without www prefix
        if base_domain.startswith('www.'):
            alternatives.append(f"{parsed.scheme}://{base_domain[4:]}{path}{query}{fragment}")
            if not path.endswith('/'):
                alternatives.append(f"{parsed.scheme}://{base_domain[4:]}{path}/{query}{fragment}")
        else:
            if '.' in base_domain and not base_domain[0].isdigit():
                alternatives.append(f"{parsed.scheme}://www.{base_domain}{path}{query}{fragment}")
                if not path.endswith('/'):
                    alternatives.append(f"{parsed.scheme}://www.{base_domain}{path}/{query}{fragment}")

        # 3. Try HTTP/HTTPS switching
        if parsed.scheme == 'https':
            alternatives.append(f"http://{base_domain}{path}{query}{fragment}")
            if not path.endswith('/'):
                alternatives.append(f"http://{base_domain}{path}/{query}{fragment}")
        elif parsed.scheme == 'http':
            alternatives.append(f"https://{base_domain}{path}{query}{fragment}")
            if not path.endswith('/'):
                alternatives.append(f"https://{base_domain}{path}/{query}{fragment}")

        # 4. Try index.html variations
        if path in ['/', '']:
            alternatives.append(f"{parsed.scheme}://{base_domain}/index.html{query}{fragment}")
            alternatives.append(f"{parsed.scheme}://{base_domain}/index.php{query}{fragment}")

        # Remove duplicates and the original URL
        alternative_urls = []
        seen = set()
        for alt in alternatives:
            if alt != url and alt not in seen:
                alternative_urls.append(alt)
                seen.add(alt)

        report_progress('alternatives_generated', {'count': len(alternative_urls)})

    all_urls_to_try = [url] + alternative_urls
    result['alternatives_tried'] = []

    # Track timeouts for adaptive behavior
    timeouts_tried = {}

    # Track SSL verification state for each attempt
    current_verify_ssl = verify_ssl

    # Try each URL with progress tracking
    for url_index, url_to_try in enumerate(all_urls_to_try):
        is_alternative = url_to_try != url
        result['is_alternative'] = is_alternative

        if is_alternative:
            result['alternatives_tried'].append(url_to_try)
            report_progress('trying_alternative', {'url': url_to_try, 'index': url_index})
            # Add delay between alternative attempts to avoid rate limiting
            if url_index > 0:
                time.sleep(1)
                report_progress('rate_limit_delay', {'delay': 1})

        # Retry logic for each URL
        for attempt in range(retry_attempts + 1):
            result['retry_count'] = attempt

            if attempt > 0:
                report_progress('retrying', {'attempt': attempt + 1, 'max_retries': retry_attempts + 1})

            if is_alternative and attempt > 0 and len(alternative_urls) > 2:
                break

            # Adaptive timeout logic
            current_timeout = timeout
            if adaptive_timeout:
                if attempt > 0:
                    current_timeout = min(timeout * (attempt + 1), max_timeout)
                    report_progress('adjusting_timeout', {'timeout': current_timeout, 'attempt': attempt + 1})

                url_key = f"{url_to_try}_{attempt}"
                if timeouts_tried.get(url_key):
                    current_timeout = max(current_timeout, timeouts_tried[url_key] + 5)
                    current_timeout = min(current_timeout, max_timeout)

            # Make the request with progress tracking
            report_progress('making_request', {
                'url': url_to_try,
                'timeout': current_timeout,
                'attempt': attempt + 1,
                'verify_ssl': current_verify_ssl
            })

            try:
                start_time = time.time()
                session = requests.Session()
                session.max_redirects = max_redirects

                response = session.get(
                    url_to_try,
                    timeout=current_timeout,
                    verify=current_verify_ssl,
                    allow_redirects=follow_redirects,
                    headers=default_headers,
                    stream=True
                )
                response_time = round(time.time() - start_time, 2)

                report_progress('request_completed', {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'final_url': response.url
                })

                # Get response details
                content_type = response.headers.get('content-type', '').lower()
                content_length_str = response.headers.get('content-length')
                content_length = None
                if content_length_str:
                    try:
                        content_length = int(content_length_str)
                    except (ValueError, TypeError):
                        try:
                            content_length = len(response.content)
                        except:
                            pass

                # Read minimal content for slow sites
                if response_time > slow_response_threshold and adaptive_timeout:
                    report_progress('slow_response_handling', {'response_time': response_time})
                    try:
                        next(response.iter_content(chunk_size=1))
                    except (StopIteration, Exception):
                        pass
                else:
                    try:
                        for chunk in response.iter_content(chunk_size=512, decode_unicode=False):
                            if chunk:
                                break
                    except (StopIteration, Exception):
                        pass

                # Store redirect history
                redirect_history = []
                if response.history:
                    for resp in response.history:
                        redirect_history.append({
                            'url': resp.url,
                            'status_code': resp.status_code,
                            'headers': dict(resp.headers)
                        })
                    report_progress('redirects_followed', {'count': len(redirect_history)})

                # Update result with response details
                result.update({
                    'url': url_to_try,
                    'response_time': response_time,
                    'final_url': response.url,
                    'code': response.status_code,
                    'content_type': content_type,
                    'content_length': content_length,
                    'redirect_history': redirect_history,
                    'headers': dict(response.headers),
                    'error': None,
                    'adaptive_timeout_used': adaptive_timeout and current_timeout != timeout,
                    'timeout_adjusted_to': current_timeout if adaptive_timeout and current_timeout != timeout else None
                })

                # Check for slow response
                if response_time > slow_response_threshold:
                    result['slow_response'] = True
                    report_progress('slow_response_detected', {'time': response_time})

                # Enhanced status determination
                if 200 <= response.status_code < 300:
                    if content_length == 0:
                        result.update({
                            'status': 'empty_response',
                            'message': 'Server returned empty response (0 bytes)',
                            'is_working': False
                        })
                        report_progress('empty_response', {})
                        if is_alternative and url_index < len(all_urls_to_try) - 1:
                            continue
                        return False, result

                    # Check for soft 404
                    soft_404_detected = False
                    if check_soft_404 and response.status_code == 200:
                        if 'text/html' in content_type:
                            if content_length is not None and content_length < 1024:
                                try:
                                    content_sample = response.text[:500].lower()
                                    error_phrases = ['404', 'not found', 'page not found', 'error', 'does not exist']
                                    if any(phrase in content_sample for phrase in error_phrases):
                                        soft_404_detected = True
                                        result['soft_404'] = True
                                        report_progress('soft_404_detected', {})
                                except:
                                    pass

                    if soft_404_detected:
                        result.update({
                            'status': 'soft_404',
                            'message': 'Page appears to be a custom 404 page',
                            'is_working': False
                        })
                        if is_alternative and try_alternatives:
                            continue
                        return False, result

                    # Valid working page
                    status_msg = f'Link is working correctly (HTTP {response.status_code})'
                    if response_time > slow_response_threshold:
                        status_msg += f' (slow: {response_time}s)'
                    if is_alternative:
                        status_msg += ' - using alternative URL'
                    if result.get('ssl_bypassed'):
                        status_msg += ' (SSL certificate verification bypassed)'

                    result.update({
                        'status': 'working',
                        'message': status_msg,
                        'is_working': True
                    })
                    report_progress('success', {'status_code': response.status_code})
                    return True, result

                # Handle rate limiting specially (429)
                elif response.status_code == 429:
                    result.update({
                        'status': 'rate_limited',
                        'message': 'Server is rate limiting requests (HTTP 429) - website is working but too many requests. Try with fewer retries or longer delays.',
                        'is_working': True,  # Website is actually working!
                        'code': 429,
                        'rate_limited': True
                    })
                    report_progress('rate_limited',
                                    {'message': 'Server returned 429 - site is working but rate limited'})

                    # Don't continue trying alternatives if rate limited
                    # Return True because the website exists and responds
                    return True, result

                # Handle other status codes (401, 403, 404, 500, etc.)
                elif 400 <= response.status_code < 600:
                    # For 4xx/5xx errors that aren't 429
                    if response.status_code == 401:
                        status_msg = f'Authentication required (HTTP 401) - website exists but needs login'
                        is_working = True  # Site exists, just needs auth
                    elif response.status_code == 403:
                        status_msg = f'Access forbidden (HTTP 403) - website exists but access denied'
                        is_working = True  # Site exists, just blocked
                    elif response.status_code == 404:
                        status_msg = 'Page not found (404) - the domain works but this specific page doesn\'t exist'
                        is_working = False  # Page doesn't exist
                    elif 500 <= response.status_code < 600:
                        status_msg = f'Server error (HTTP {response.status_code}) - website exists but has server issues'
                        is_working = True  # Site exists, just having issues
                    else:
                        status_msg = f'HTTP {response.status_code}'
                        is_working = False

                    result.update({
                        'status': 'error',
                        'message': status_msg,
                        'is_working': is_working,
                        'code': response.status_code
                    })

                    # For 401/403/500, the domain exists
                    # Return the appropriate status
                    return is_working, result

                # Handle redirects that weren't followed
                elif 300 <= response.status_code < 400:
                    result.update({
                        'status': 'redirect',
                        'message': f'Redirect ({response.status_code}) but redirects not followed',
                        'is_working': True,
                        'code': response.status_code
                    })
                    return True, result

            except requests.exceptions.SSLError as e:
                report_progress('ssl_error', {'error': str(e)[:100]})

                # Check if it's a certificate error vs other SSL issues
                if "CERTIFICATE_VERIFY_FAILED" in str(e):
                    # This is a cert issue - maybe acceptable for some sites
                    if attempt == retry_attempts:
                        # Last attempt, try without verification but log it
                        result['ssl_bypassed'] = True
                        result['ssl_warning'] = f"SSL certificate verification failed: {str(e)[:200]}"
                        current_verify_ssl = False
                        report_progress('ssl_bypassed', {'warning': result['ssl_warning']})
                        continue
                    else:
                        # Try with proper SSL first on next retry
                        report_progress('ssl_retry_with_verification', {'attempt': attempt + 1})
                        continue
                else:
                    # Other SSL errors are more serious (protocol mismatch, etc.)
                    result.update({
                        'status': 'ssl_error',
                        'message': f'SSL Error: {str(e)[:100]}',
                        'error': str(e),
                        'is_working': False
                    })
                    return False, result

            except requests.exceptions.Timeout:
                timeouts_tried[f"{url_to_try}_{attempt}"] = current_timeout
                report_progress('timeout', {'timeout': current_timeout, 'attempt': attempt + 1})

                if attempt == retry_attempts:
                    if is_alternative and url_index < len(all_urls_to_try) - 1:
                        error_msg = f'Timeout on alternative URL, trying next alternative'
                        continue
                    else:
                        result.update({
                            'status': 'timeout',
                            'message': f'Request timed out after {current_timeout} seconds on all attempts',
                            'error': 'Timeout',
                            'is_working': False
                        })
                        return False, result
                else:
                    continue

            except requests.exceptions.ConnectionError as e:
                report_progress('connection_error', {'error': str(e)[:100]})
                if attempt == retry_attempts:
                    if is_alternative and url_index < len(all_urls_to_try) - 1:
                        continue
                    else:
                        result.update({
                            'status': 'connection_error',
                            'message': f'Connection error: {str(e)[:100]}',
                            'error': str(e),
                            'is_working': False
                        })
                        return False, result
                else:
                    time.sleep(1)
                    continue

            except Exception as e:
                report_progress('error', {'error': str(e)[:100]})
                if attempt == retry_attempts:
                    if is_alternative and url_index < len(all_urls_to_try) - 1:
                        continue
                    else:
                        result.update({
                            'status': 'error',
                            'message': f'Unexpected error: {str(e)[:100]}',
                            'error': str(e),
                            'is_working': False
                        })
                        return False, result
                else:
                    continue

    # If all attempts failed
    report_progress('all_attempts_failed', {})
    result.update({
        'status': 'all_failed',
        'message': 'All URL attempts failed, including alternatives',
        'is_working': False
    })
    return False, result


def get_all_extractable_links(url, same_domain_only=False, exclude_extensions=None):
    """
    Extract all links that can be used for data extraction

    Args:
        url: The URL to extract links from
        same_domain_only: If True, only return links from the same domain
        exclude_extensions: List of file extensions to exclude (e.g., ['.pdf', '.jpg', '.png', '.mp4'])

    Returns:
        List of unique URLs
    """
    try:
        from urllib.parse import urlparse

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        response = session.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        all_urls = []
        base_domain = urlparse(url).netloc

        # Comprehensive elements to extract
        elements_to_extract = [
            ('a', 'href'),  # Standard links
            ('img', 'src'),  # Images
            ('script', 'src'),  # JavaScript files
            ('link', 'href'),  # CSS, canonical, etc.
            ('source', 'src'),  # Video/audio sources
            ('iframe', 'src'),  # Embedded content
            ('embed', 'src'),  # Embedded plugins
            ('video', 'src'),  # Video files
            ('audio', 'src'),  # Audio files
            ('form', 'action'),  # Form submissions
            ('area', 'href')  # Image map links
        ]

        for tag, attr in elements_to_extract:
            for element in soup.find_all(tag, {attr: True}):
                full_url = urljoin(url, element[attr])

                # Apply domain filter if specified
                if same_domain_only:
                    parsed = urlparse(full_url)
                    if parsed.netloc and parsed.netloc != base_domain:
                        continue

                # Apply extension filter if specified
                if exclude_extensions:
                    if any(full_url.lower().endswith(ext) for ext in exclude_extensions):
                        continue

                all_urls.append(full_url)

        # Extract meta refresh URLs
        for meta in soup.find_all('meta', attrs={'http-equiv': 'refresh'}):
            content = meta.get('content', '')
            if 'url=' in content.lower():
                refresh_url = content.split('url=')[-1]
                full_url = urljoin(url, refresh_url)
                if not (exclude_extensions and any(full_url.lower().endswith(ext) for ext in exclude_extensions)):
                    all_urls.append(full_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in all_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    except requests.RequestException as e:
        print(f"Request error for {url}: {e}")
        return []
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")
        return []


def is_company_social_profile(link):
    """
    Determine if a social media link is likely a company profile
    vs a generic social media homepage
    """
    # List of generic social media homepages to remove
    generic_social_homepages = [
        'https://www.facebook.com',
        'https://facebook.com',
        'http://www.facebook.com',
        'http://facebook.com',
        'https://www.twitter.com',
        'https://twitter.com',
        'http://www.twitter.com',
        'http://twitter.com',
        'https://twiiter.com',
        'http://twiiter.com',
        'https://www.linkedin.com',
        'https://linkedin.com',
        'http://www.linkedin.com',
        'http://linkedin.com',
        'https://www.youtube.com',
        'https://youtube.com',
        'http://www.youtube.com',
        'http://youtube.com',
        'https://www.instagram.com',
        'https://instagram.com',
        'http://www.instagram.com',
        'http://instagram.com',
        'https://www.google.com',
        'https://google.com',
        'http://www.google.com',
        'http://google.com'
    ]

    # Remove trailing slashes for comparison
    clean_link = link.rstrip('/')

    # If it's a generic social media homepage, remove it
    if clean_link in generic_social_homepages:
        return False

    # Patterns for company-specific social media profiles
    social_patterns = {
        'facebook': [
            r'facebook\.com/[^/?]+',  # facebook.com/username
            r'facebook\.com/pages/',  # facebook.com/pages/pagename
            r'facebook\.com/groups/',  # facebook.com/groups/groupname
        ],
        'twitter': [
            r'twitter\.com/[^/?]+',  # twitter.com/username
        ],
        'linkedin': [
            r'linkedin\.com/company/',  # linkedin.com/company/companyname
            r'linkedin\.com/in/',  # linkedin.com/in/username
        ],
        'youtube': [
            r'youtube\.com/c/',  # youtube.com/c/channelname
            r'youtube\.com/channel/',  # youtube.com/channel/channelid
            r'youtube\.com/user/',  # youtube.com/user/username
        ],
        'instagram': [
            r'instagram\.com/[^/?]+',  # instagram.com/username
        ]
    }

    # Check if it's a social media domain
    for platform, patterns in social_patterns.items():
        if platform in link.lower():
            # Check if it matches any company profile pattern
            for pattern in patterns:
                if re.search(pattern, link, re.IGNORECASE):
                    return True
            # If it's a social domain but doesn't match profile patterns, it's generic
            return False

    # If it's not a social media domain, keep it
    return True


def get_all_link(url):
    """
    Get links with intelligent social media filtering
    """
    all_links = get_all_extractable_links(url)

    # Skip media file extensions (no sub-links to extract)
    media_extensions = [
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',  # Video
        '.mp3', '.wav', '.aac', '.flac', '.ogg',  # Audio
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',  # Images
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',  # Documents
        '.zip', '.rar', '.tar', '.gz',  # Archives
        '.exe', '.msi', '.dmg'  # Executables
    ]

    # First filter: must be company social profile
    filtered_links = [link for link in all_links if is_company_social_profile(link)]

    # Second filter: skip direct media file links
    filtered_links = [
        link for link in filtered_links
        if not any(link.lower().endswith(ext) for ext in media_extensions)
    ]

    return filtered_links


def website_data_selenium(url, value=20, remove_duplicate=False):
    try:
        if '.pdf' in url.lower():
            about_sections = common.read_pdf_from_url(url)
            if remove_duplicate:
                about_sections = common.remove_duplicate_words(about_sections)
            return about_sections if about_sections else False

        # ✅ Headless Chrome setup
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(5)

        # 🔄 Scroll to bottom (lazy loading)
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(0, scroll_height, 500):
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.2)

        # 🖱️ Fixed: Handle "Read More" buttons with stale element protection
        expand_keywords = ["read more", "show more", "load more", "expand", "view more"]

        for keyword in expand_keywords:
            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                try:
                    # Find fresh elements each retry
                    buttons = driver.find_elements(By.XPATH,
                                                   f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")

                    if not buttons:
                        break  # No buttons found for this keyword

                    # Try to click the first button only
                    try:
                        driver.execute_script("arguments[0].click();", buttons[0])
                        time.sleep(2)  # Wait for page to update
                        break  # Success, move to next keyword
                    except Exception:
                        retry_count += 1
                        time.sleep(1)

                except Exception:
                    retry_count += 1
                    time.sleep(1)

        # 🖼️ Handle iframes (improved)
        page_content = driver.page_source
        frames = driver.find_elements(By.TAG_NAME, "iframe")

        for frame in frames:
            try:
                driver.switch_to.frame(frame)
                page_content += driver.page_source
                driver.switch_to.default_content()
            except:
                try:
                    driver.switch_to.default_content()
                except:
                    pass

        driver.quit()

        # 📄 Parse HTML for visible text
        soup = BeautifulSoup(page_content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        about_sections = ''
        possible_tags = ["main", "section", "div", "article", "header", "footer", "aside", "nav", "span", "p", "h1",
                         "h2", "h3"]

        for tag in possible_tags:
            elements = soup.find_all(tag)
            for elem in elements:
                text = elem.get_text(separator=" ", strip=True)
                if len(text.strip()) > value:
                    about_sections += '\n' + text

        if about_sections:
            if remove_duplicate:
                about_sections = common.remove_duplicate_words(about_sections)
            return about_sections
        else:
            return None  # No print statement

    except Exception as e:
        return None  # No print statement
