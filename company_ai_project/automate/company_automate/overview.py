import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from company_ai_project.automate.company_automate import add_all_link, link_rewrite

from common_script import website_script, common
from agent.agents import company_agent_template, text_util_agent, company_agent
from company_ai_project.database.company_database import company_name_link, link, overview

# ──────────────────────────────────────────────
#  Print utilities
# ──────────────────────────────────────────────

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
    PROGRESS = "📊"
    OVERVIEW = "📝"
    SUMMARY = "📋"
    FILTER = "🔎"


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


def log_progress(msg): safe_print(msg, "cyan", Icons.PROGRESS)


def log_overview(msg): safe_print(msg, "blue", Icons.OVERVIEW)


def log_summary(msg): safe_print(msg, "green", Icons.SUMMARY)


def log_filter(msg): safe_print(msg, "yellow", Icons.FILTER)


def print_separator(char: str = "─", length: int = 60):
    safe_print(char * length, color="gray")


def print_header(title: str):
    """Print a formatted header."""
    print_separator("═", 70)
    safe_print(f" {title} ", color="bold")
    print_separator("═", 70)


def print_section(title: str):
    """Print a section header."""
    print_separator("─", 60)
    safe_print(f" {title} ", color="white")
    print_separator("─", 60)


# Database instances
company_name_link_db = company_name_link.CompanyNameLink()
link_db = link.LinkTable()
filter_link_db = link.FilterLinkTable()
overview_db = overview.OverviewTable()
summary_db = overview.SummaryTable()

all_company =  company_name_link_db.get_companies_by_date()



def set_overview(company, replace=False):
    unique_name = company["unique_name"]

    print_section(f"Setting Overview for: {unique_name}")
    log_info(f"Starting overview generation for {unique_name}")

    total_string = ''

    # Filter rewrite
    log_filter(f"Running filter rewrite for {unique_name}")
    link_rewrite.filter_rewrite(company=company)
    log_success(f"Filter rewrite completed for {unique_name}")

    # Get filter links
    filter_link = filter_link_db.get_filter_links_by_unique_name(unique_name=unique_name)
    log_info(f"Found {len(filter_link)} filter links for {unique_name}")

    # Process each link
    link_count = 0
    for each in filter_link:
        link_count += 1
        link_url = each["link"]
        log_link(f"Processing link {link_count}/{len(filter_link)}: {link_url[:80]}...")

        link_data = link_db._get_link_by_unique_name_and_link(
            unique_name=unique_name,
            link=link_url
        )
        overview = link_data.get('link_overview')
        if overview:
            total_string += overview + '\n'
            log_success(f"  ✓ Added overview from: {link_url[:60]}...")
        else:
            log_warning(f"  ⚠️ No overview found for: {link_url[:60]}...")

    if total_string:
        # Generate ultra detailed analyzer
        log_overview(f"Generating ultra detailed analyzer for {unique_name}")
        __overview = text_util_agent.get_ultra_detailed_analyzer(
            str(total_string),
            combine_analyzer=True
        )
        log_success(f"Ultra detailed analyzer completed for {unique_name}")

        # Generate small overview
        log_overview(f"Generating small overview for {unique_name}")
        small_overview = company_agent.get_company_small_overview(__overview)
        log_success(f"Small overview generated for {unique_name}")

        # Insert overview
        log_db(f"Saving overview to database for {unique_name}")
        overview_db.insert_overview(unique_name=unique_name,
                                    overview=__overview,
                                    small_overview=small_overview,
                                    replace=replace)
        log_success(f"Overview saved for {unique_name}")

        # Generate summary
        generate_company_summery(company=company, replace=replace)

        print_section(f"Completed: {unique_name}")
        log_success(f"✅ Successfully set overview for {unique_name}")
        print_separator()

def generate_company_summery(company, replace=False):
    unique_name = company["unique_name"]
    __overview = overview_db.get_overview(unique_name=unique_name)
    overview = __overview.get('overview') if __overview else None
    if not overview:
        log_warning(f"No overview found for {unique_name}")
        return

    log_summary(f"Generating company summary for {unique_name}")
    summery = company_agent.get_company_summery(__overview)
    log_success(f"Company summary generated for {unique_name}")

    # Insert summary
    log_db(f"Saving summary to database for {unique_name}")
    summary_db.insert_summary(unique_name=unique_name,
                              summary=summery,
                              replace=replace)
    log_success(f"Summary saved for {unique_name}")
    return


def process_single_company(company_data):
    """Process a single company for overview generation."""
    unique_name = company_data["unique_name"]

    try:
        # Check if overview already exists
        overview = overview_db.get_overview(unique_name=unique_name)

        if overview:
            log_skip(f"Overview already exists for {unique_name}")
            return {"unique_name": unique_name, "status": "skipped", "error": None}

        # Check for filter links
        filter_link = filter_link_db.get_filter_links_by_unique_name(unique_name=unique_name)

        if not filter_link:
            log_warning(f"No filter links found for {unique_name}")
            log_info(f"Fetching all links for {unique_name}")

            all_link = link_db.get_links_by_unique_name(unique_name=unique_name)
            log_info(f"Found {len(all_link) if all_link else 0} links for {unique_name}")

            log_info(f"Running process_company for {unique_name}")
            add_all_link.process_company(company_data)
            log_success(f"Process company completed for {unique_name}")

        # Set overview
        set_overview(company=company_data)
        return {"unique_name": unique_name, "status": "success", "error": None}

    except Exception as e:
        log_error(f"❌ Failed to process {unique_name}: {str(e)}")
        return {"unique_name": unique_name, "status": "failed", "error": str(e)}


def all_overview(max_workers=3):
    """Run overview generation with parallel processing."""
    total_companies = len(all_company)

    print_header(" OVERVIEW GENERATION PROCESS ")
    log_info(f"Starting overview generation for {total_companies} companies with {max_workers} workers")
    print_separator()

    processed = 0
    skipped = 0
    failed = 0

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_company = {
            executor.submit(process_single_company, company): company
            for company in all_company
        }

        # Process completed tasks as they finish
        for idx, future in enumerate(as_completed(future_to_company), 1):
            company = future_to_company[future]
            unique_name = company["unique_name"]

            try:
                result = future.result()

                if result["status"] == "success":
                    processed += 1
                    log_success(f"✅ Successfully processed {unique_name}")
                elif result["status"] == "skipped":
                    skipped += 1
                    log_skip(f"⏭️ Skipped {unique_name} (already exists)")
                else:
                    failed += 1
                    log_error(f"❌ Failed to process {unique_name}")

                # Show progress
                log_progress(
                    f"Progress: {idx}/{total_companies} "
                    f"(✅ Success: {processed}, ⏭️ Skipped: {skipped}, ❌ Failed: {failed})"
                )

            except Exception as e:
                failed += 1
                log_error(f"❌ Unexpected error for {unique_name}: {str(e)}")

            print_separator()

    # Final summary
    print_header(" OVERVIEW GENERATION COMPLETE ")
    log_success(f"🎉 Processing completed for {total_companies} companies")
    print_separator()
    log_progress(f"📊 Final Statistics:")
    log_progress(f"   • Total companies: {total_companies}")
    log_progress(f"   • Successfully processed: {processed} ✅")
    log_progress(f"   • Skipped (already existed): {skipped} ⏭️")
    log_progress(f"   • Failed: {failed} ❌")
    log_progress(f"   • Success rate: {(processed / total_companies * 100):.1f}%")
    print_separator("═", 70)


def all_summery(max_workers=3):
    """
    Generate summaries for all companies that don't have one yet.

    :param max_workers: Number of concurrent workers
    :return: None
    """
    total_companies = len(all_company)

    print_header(" SUMMARY GENERATION PROCESS ")
    log_info(f"Starting summary generation for {total_companies} companies with {max_workers} workers")
    print_separator()

    processed = 0
    skipped = 0
    failed = 0

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_company = {}

        for company in all_company:
            unique_name = company["unique_name"]
            __summary = summary_db.get_summary(unique_name=unique_name)

            if __summary:
                log_skip(f"Summary already exists for {unique_name}")
                skipped += 1
            else:
                future = executor.submit(generate_company_summery, company=company, replace=False)
                future_to_company[future] = company

        # Process completed tasks as they finish
        for idx, future in enumerate(as_completed(future_to_company), 1):
            company = future_to_company[future]
            unique_name = company["unique_name"]

            try:
                future.result()  # Wait for the task to complete
                processed += 1
                log_success(f"✅ Successfully generated summary for {unique_name}")

            except Exception as e:
                failed += 1
                log_error(f"❌ Failed to generate summary for {unique_name}: {str(e)}")

            # Show progress
            total_attempted = processed + failed
            log_progress(
                f"Progress: {total_attempted}/{total_companies - skipped} "
                f"(✅ Success: {processed}, ❌ Failed: {failed})"
            )
            print_separator()

    # Final summary
    print_header(" SUMMARY GENERATION COMPLETE ")
    log_success(f"🎉 Processing completed")
    print_separator()
    log_progress(f"📊 Final Statistics:")
    log_progress(f"   • Total companies: {total_companies}")
    log_progress(f"   • Successfully generated: {processed} ✅")
    log_progress(f"   • Skipped (already existed): {skipped} ⏭️")
    log_progress(f"   • Failed: {failed} ❌")
    if total_companies - skipped > 0:
        log_progress(f"   • Success rate: {(processed / (total_companies - skipped) * 100):.1f}%")
    print_separator("═", 70)




if __name__ == "__main__":
    # Run with 3 concurrent workers
    all_overview(max_workers=3)