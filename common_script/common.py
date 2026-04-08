import pdfplumber
import requests
from io import BytesIO
from urllib.parse import urlparse
import os
import chardet
#from company_ai_project_old import saved_data
# from company_ai_project.database_old import company_database_new
#from company_ai_project_old.database_old.company_database import company_db

import webbrowser


def download_pdf(url):
    """Download PDF from URL and return as BytesIO object."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading PDF from {url}: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error downloading PDF: {e}")
        return None


def read_pdf_file(pdf_file):
    """
    Extract text from PDF file - handles both file paths and file-like objects.

    Args:
        pdf_file: File path (string) or file-like object (BytesIO, file object)

    Returns:
        dict: {page_number: text} or None if error
    """
    try:
        # Handle file-like objects by resetting position
        if hasattr(pdf_file, 'seek'):
            pdf_file.seek(0)

        with pdfplumber.open(pdf_file) as pdf:
            text_by_page = {
                page_num: page.extract_text() or ""
                for page_num, page in enumerate(pdf.pages, start=1)
            }

            # Return None if all pages are empty
            return text_by_page if any(text_by_page.values()) else None

    except pdfplumber.PDFSyntaxError as e:
        print(f"❌ PDF syntax error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return None


def read_pdf_from_url(url):
    """Extract text from PDF URL using pdfplumber."""
    pdf_file = download_pdf(url)
    return read_pdf_file(pdf_file) if pdf_file else None


def remove_duplicate_words(text):
    """Remove duplicate words while preserving sentence structure."""
    words = text.split()
    seen_words = set()
    result_words = []

    for word in words:
        # Clean word from punctuation for comparison
        clean_word = word.strip('.,!?;:"“”‘\'()[]{}')

        if clean_word and clean_word.lower() not in seen_words:
            seen_words.add(clean_word.lower())
            result_words.append(word)
        elif not clean_word:  # Keep punctuation-only "words"
            result_words.append(word)

    return ' '.join(result_words)


def split_text_by_words(text, words_per_chunk=40000):
    """Split text into chunks with specified number of words."""
    words = text.split()
    return [
        ' '.join(words[i:i + words_per_chunk])
        for i in range(0, len(words), words_per_chunk)
    ]


def is_same_domain(url1, url2):
    """
    Check if two URLs belong to the same domain.

    Args:
        url1: First URL
        url2: Second URL

    Returns:
        bool: True if same domain, False otherwise
    """
    try:
        domain1 = urlparse(url1).netloc.lower()
        domain2 = urlparse(url2).netloc.lower()
        return domain1 == domain2
    except Exception:
        return False


def find_matching_company(website_url, company_list):
    """
    Find company in list that matches the website URL.

    Args:
        website_url: URL to check
        company_list: List of company dictionaries with 'website' field

    Returns:
        dict: Matching company dictionary or None
    """
    return next(
        (company for company in company_list
         if is_same_domain(website_url, company.get('website', ''))),
        None
    )


def read_text_file_advanced(filename, mode='all', fallback_encoding='utf-8'):
    """
    Robust text file reader with encoding detection and multiple reading modes.

    Args:
        filename: Path to text file
        mode: 'all', 'lines', 'first', or 'last'
        fallback_encoding: Encoding to use if detection fails

    Returns:
        str/list: File content based on mode, or error message
    """
    # Validate mode
    valid_modes = {'all', 'lines', 'first', 'last'}
    if mode not in valid_modes:
        return f"Error: Invalid mode '{mode}'. Use: {', '.join(valid_modes)}"

    try:
        # Read file in binary mode for encoding detection
        with open(filename, 'rb') as file:
            raw_data = file.read()

        # Detect encoding
        encoding_info = chardet.detect(raw_data)
        detected_encoding = encoding_info['encoding']
        confidence = encoding_info['confidence']

        # Choose encoding based on confidence
        encoding = (
            detected_encoding
            if detected_encoding and confidence > 0.6
            else fallback_encoding
        )

        print(f"📖 Detected encoding: {detected_encoding} (confidence: {confidence:.2f})")
        if encoding != detected_encoding:
            print(f"🔄 Using encoding: {encoding}")

        # Decode content
        content = raw_data.decode(encoding, errors='replace')

        # Process based on mode
        if mode == 'all':
            return content
        elif mode == 'lines':
            return content.splitlines()
        elif mode == 'first':
            return '\n'.join(content.splitlines()[:10])
        elif mode == 'last':
            return '\n'.join(content.splitlines()[-10:])

    except FileNotFoundError:
        return f"Error: File '{filename}' not found"
    except PermissionError:
        return f"Error: Permission denied accessing '{filename}'"
    except Exception as e:
        return f"Error reading file: {e}"


def _extract_domain(url):
    """
    Extract domain from URL.

    Args:
        url: Website URL

    Returns:
        str: Extracted domain or original URL if parsing fails
    """
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


def _combine_value(items, value=10):
    """Combine items into chunks of specified size."""
    if not items:
        return []

    return [
        ' '.join(map(str, items[i:i + value]))
        for i in range(0, len(items), value)
    ]


def combine_value(items, value=10):
    """Combine every 10 items into one string"""
    combined = []
    for i in range(0, len(items), value):
        chunk = items[i:i + value]
        combined_string = ' '.join(str(item) for item in chunk)
        combined.append(combined_string)
    return combined


def get_create_database(data, media_flag=False):
    """
    Create and return database_old path and media directory for a website.

    Args:
        data: Dictionary containing 'website' key with URL
        media_flag: If True, creates and returns media directory

    Returns:
        tuple: (database_path, media_dir_path)
    """
    _database_dir = os.path.join(
        os.path.abspath(os.path.dirname(saved_data.__file__)),
        'temp_databases'
    )
    os.makedirs(_database_dir, exist_ok=True)

    # Clean website name for use in filename
    website = data.get('website', '')
    if not website:
        raise ValueError("Website URL is required in data dictionary")
    database_sample_name = website.replace('https://', '').replace('http://', '').replace('/', '_')

    media_dir = ''
    if media_flag:
        media_dir = os.path.join(_database_dir, database_sample_name)
        os.makedirs(media_dir, exist_ok=True)

    database_name = f"{database_sample_name}.db"
    _database = os.path.join(_database_dir, database_name)
    _database = company_db.CompanyDB(db_path=_database)

    return _database, media_dir


def open_website(url):
    """Open website in default browser"""
    try:
        # Ensure URL has http:// or https://
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        webbrowser.open(url)
        print(f"🌐 Opening website: {url}")

    except Exception as e:
        print(f"❌ Error opening website: {e}")


def format_website_url(url):
    """Format and validate the website URL"""
    if not url:
        return None

    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    return url
