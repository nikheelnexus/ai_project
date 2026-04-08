import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Any

from agent.agents import company_agent_template, text_util_agent, company_agent
from common_script import website_script, common
from company_ai_project.database.company_database import company_name_link, link

# Database connections
company_name_link_db = company_name_link.CompanyNameLink()
link_db = link.LinkTable()
filter_link_db = link.FilterLinkTable()
all_companies = company_name_link_db.get_all_companies()

# Thread-safe logging setup
print_lock = threading.Lock()

COLORS = {
    "gray": "\033[90m",
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}


class Icons:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    DATABASE = "💾"
    LINK = "🔗"
    SEARCH = "🔍"
    TRASH = "🗑️"
    UPDATE = "🔄"
    SKIP = "⏭️"
    WORKER = "🧵"
    FILTER = "🔎"
    REWRITE = "✍️"
    PROGRESS = "📊"


def safe_print(message: str, color: str = "", icon: str = ""):
    """Thread-safe print with timestamp, optional color and icon."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = f"{icon} " if icon else ""
    line = f"[{timestamp}] {prefix}{message}"
    with print_lock:
        if color and color in COLORS:
            print(f"{COLORS[color]}{line}{COLORS['reset']}")
        else:
            print(line)


# Convenience wrappers
def log_info(msg): safe_print(msg, "cyan", Icons.INFO)


def log_success(msg): safe_print(msg, "green", Icons.SUCCESS)


def log_error(msg): safe_print(msg, "red", Icons.ERROR)


def log_warning(msg): safe_print(msg, "yellow", Icons.WARNING)


def log_link(msg): safe_print(msg, "blue", Icons.LINK)


def log_skip(msg): safe_print(msg, "gray", Icons.SKIP)


def log_db(msg): safe_print(msg, "magenta", Icons.DATABASE)


def log_worker(msg): safe_print(msg, "white", Icons.WORKER)


def log_rewrite(msg): safe_print(msg, "yellow", Icons.REWRITE)


def log_progress(msg): safe_print(msg, "cyan", Icons.PROGRESS)


def print_separator(char: str = "─", length: int = 60):
    """Print a separator line."""
    safe_print(char * length, color="gray")


def print_header(title: str):
    """Print a formatted header."""
    print_separator("=", 70)
    safe_print(f" {title} ", color="bold")
    print_separator("=", 70)


def process_single_link(unique_name: str, link_url: str, idx: int, total: int) -> Tuple[bool, str, str]:
    """Process a single link: fetch data and rewrite content."""
    try:
        log_rewrite(f"[{idx}/{total}] Processing: {link_url[:80]}...")

        # Check if link overview already exists
        link_data = link_db._get_link_by_unique_name_and_link(
            unique_name=unique_name,
            link=link_url
        )

        if link_data and link_data.get('link_overview'):
            log_skip(f"[{idx}/{total}] Overview exists, skipping: {link_url[:80]}...")
            return True, link_url, "skipped"

        # Fetch data from website
        #log_info(f"[{idx}/{total}] Fetching data from: {link_url[:80]}...")
        all_text = website_script.website_data_selenium(link_url)

        # Rewrite text
        #log_rewrite(f"[{idx}/{total}] Rewriting content...")
        rewritten_text = text_util_agent.rewrite_text(str(all_text))

        # Save to database
        link_db.insert_link(
            unique_name=unique_name,
            link=link_url,
            link_overview=rewritten_text
        )

        #log_success(f"[{idx}/{total}] Successfully processed: {link_url[:80]}...")
        return True, link_url, "processed"

    except Exception as e:
        log_error(f"[{idx}/{total}] Error processing {link_url[:80]}...: {str(e)}")
        return False, link_url, str(e)


def filter_rewrite(company: Dict, max_workers=3):
    """Process filter links for a company with 3 concurrent workers."""
    unique_name = company.get('unique_name')

    log_info(f"\n{'=' * 60}")
    log_info(f"Processing company: {unique_name}")
    log_info(f"{'=' * 60}")

    # Get all filter links for this company
    all_filter = filter_link_db.get_filter_links_by_unique_name(unique_name=unique_name)

    if not all_filter:
        log_warning(f"No filter links found for {unique_name}")
        return

    total_links = len(all_filter)
    log_info(f"Found {total_links} filter links to process")

    processed = 0
    skipped = 0
    failed = 0

    # Process links with 3 concurrent workers
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"Worker-{unique_name[:10]}") as executor:
        # Submit all tasks
        futures = {
            executor.submit(process_single_link, unique_name, each_filter.get('link'), idx, total_links): each_filter
            for idx, each_filter in enumerate(all_filter, 1)
        }

        # Process completed tasks
        for future in as_completed(futures):
            try:
                success, link_url, status = future.result()

                if success:
                    if status == "processed":
                        processed += 1
                    elif status == "skipped":
                        skipped += 1
                else:
                    failed += 1

                # Show progress
                current_total = processed + skipped + failed
                log_progress(f"Progress: {current_total}/{total_links} (✅:{processed} ⏭️:{skipped} ❌:{failed})")

            except Exception as e:
                failed += 1
                log_error(f"Unexpected error: {str(e)}")

    # Print summary for this company
    log_info(f"\n{'─' * 60}")
    log_success(f"Company {unique_name} completed!")
    log_info(f"  ✅ Processed: {processed}")
    log_info(f"  ⏭️ Skipped: {skipped}")
    log_info(f"  ❌ Failed: {failed}")
    log_info(f"  📊 Total: {total_links}")
    log_info(f"{'─' * 60}\n")


def process_all_companies(max_workers: int = 3):
    """Process all companies with concurrent workers."""
    total_companies = len(all_companies)

    print_header(" FILTER REWRITE PROCESSING ")
    log_info(f"Starting to process {total_companies} companies")
    log_info(f"Using {max_workers} concurrent workers")
    print_separator()

    start_time = datetime.now()
    completed = 0
    failed_companies = []

    # Process companies concurrently
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Company") as executor:
        futures = {
            executor.submit(filter_rewrite, company): company
            for company in all_companies
        }

        for future in as_completed(futures):
            company = futures[future]
            company_name = company.get('unique_name')

            try:
                future.result()
                completed += 1
                log_success(f"✅ Company {completed}/{total_companies}: {company_name} completed")
            except Exception as e:
                completed += 1
                failed_companies.append(company_name)
                log_error(f"❌ Company {completed}/{total_companies}: {company_name} failed - {str(e)}")

            # Show overall progress
            log_progress(f"Overall progress: {completed}/{total_companies} ({completed / total_companies * 100:.1f}%)")
            print_separator()

    # Final summary
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()

    print_header(" PROCESSING COMPLETE ")
    log_success(f"✅ Successfully processed: {completed - len(failed_companies)} companies")

    if failed_companies:
        log_warning(f"❌ Failed companies: {len(failed_companies)}")
        for name in failed_companies:
            log_error(f"   • {name}")

    log_info(f"⏱️ Total time: {total_time:.1f} seconds")
    log_info(f"📊 Average time per company: {total_time / total_companies:.1f} seconds")
    print_separator("=", 70)


