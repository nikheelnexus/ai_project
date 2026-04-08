import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from common_script import website_script, common
from agent.agents import company_agent
from company_ai_project.database.company_database import company_name_link, link


# ──────────────────────────────────────────────
#  Print utilities
# ──────────────────────────────────────────────

print_lock = threading.Lock()

COLORS = {
    "gray":    "\033[90m",
    "green":   "\033[92m",
    "red":     "\033[91m",
    "yellow":  "\033[93m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
}

class Icons:
    SUCCESS  = "✅"
    ERROR    = "❌"
    WARNING  = "⚠️ "
    INFO     = "ℹ️ "
    DATABASE = "💾"
    LINK     = "🔗"
    SEARCH   = "🔍"
    TRASH    = "🗑️ "
    UPDATE   = "🔄"
    SKIP     = "⏭️ "
    WORKER   = "🧵"


def safe_print(message: str, color: str = "", icon: str = ""):
    """Thread-safe print with timestamp, optional color and icon."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix    = f"{icon} " if icon else ""
    line      = f"[{timestamp}] {prefix}{message}"
    with print_lock:
        if color and color in COLORS:
            print(f"{COLORS[color]}{line}\033[0m")
        else:
            print(line)

# Convenience wrappers
def log_info   (msg): safe_print(msg, "cyan",    Icons.INFO)
def log_success(msg): safe_print(msg, "green",   Icons.SUCCESS)
def log_error  (msg): safe_print(msg, "red",     Icons.ERROR)
def log_warning(msg): safe_print(msg, "yellow",  Icons.WARNING)
def log_link   (msg): safe_print(msg, "blue",    Icons.LINK)
def log_skip   (msg): safe_print(msg, "gray",    Icons.SKIP)
def log_db     (msg): safe_print(msg, "magenta", Icons.DATABASE)
def log_worker (msg): safe_print(msg, "white",   Icons.WORKER)

def print_separator(): safe_print("─" * 60, color="gray")

link_db = link.LinkTable()

# ──────────────────────────────────────────────
#  Task 1 — Crawl & collect all links
# ──────────────────────────────────────────────

def process_company(company: dict, replace=False) -> None:
    """Crawl one company and persist all discovered links."""
    unique_name = company.get("unique_name")
    url = company.get("website")
    thread_name = threading.current_thread().name

    log_worker(f"[{thread_name}] Processing → {unique_name}  ({url})")

    # If replace is False, check if links already exist
    if not replace:
        if link_db.get_links_by_unique_name(unique_name):
            log_skip(f"[{thread_name}] Already has links, skipping: {unique_name}")
            return
    else:
        # Replace mode - log that we're running fresh crawl
        log_info(f"[{thread_name}] Replace mode enabled - crawling fresh for: {unique_name}")

    # Skip social-media URLs
    if website_script.is_social_media(url):
        log_skip(f"[{thread_name}] Social media URL, skipping: {url}")
        return

    # ── Depth-1 crawl with concurrent depth-2 ──────────────────────────
    log_info(f"[{thread_name}] Fetching top-level links from: {url}")
    top_links = website_script.get_all_link(url)
    top_links.append(url)

    if not top_links:
        log_warning(f"[{thread_name}] No links found at: {url}")
        return

    collected: set[str] = set()
    log_info(f'Total top-level links: {len(top_links)}')

    def process_link(link_url: str) -> set[str]:
        """Process a single top-level link and its sub-links"""
        result = set()
        try:
            formatted = website_script.format_website_url(link_url)
            result.add(formatted)
            log_link(f"  [L1] {formatted}")

            # ── Depth-2 crawl ──────────────────────
            sub_links = website_script.get_all_link(link_url)
            if sub_links:
                for sub_url in sub_links:
                    sub_formatted = website_script.format_website_url(sub_url)
                    result.add(sub_formatted)
                    #log_link(f"    [L2] {sub_formatted}")
        except Exception as e:
            log_error(f"Error processing {link_url}: {e}")

        return result

    # Process top_links concurrently
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="LinkCrawler") as executor:
        # Submit all top-level link processing tasks
        future_to_link = {
            executor.submit(process_link, link_url): link_url
            for link_url in top_links
        }

        # Collect results as they complete
        for future in as_completed(future_to_link):
            link_url = future_to_link[future]
            try:
                links_set = future.result()
                collected.update(links_set)
                log_info(f"[{thread_name}] Completed processing: {link_url} (found {len(links_set)} links)")
            except Exception as e:
                log_error(f"[{thread_name}] Failed to process {link_url}: {e}")

    # ── Persist ────────────────────────────────
    if collected:
        log_db(f"[{thread_name}] Saving {len(collected)} links for: {unique_name}")

        # If replace mode, you might want to delete existing links first
        if replace:
            log_info(f"[{thread_name}] Replace mode - will insert {len(collected)} links")

        # Insert links concurrently with 4 workers
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def insert_single_link(link_url: str, idx: int, total: int):
            """Insert a single link into database"""
            try:
                link_db.insert_link(unique_name=unique_name, link=link_url, replace=replace)
                return True, link_url, idx, None
            except Exception as e:
                return False, link_url, idx, str(e)

        links_list = list(collected)
        total_links = len(links_list)
        inserted_count = 0
        failed_count = 0

        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="InsertWorker") as executor:
            # Submit all insert tasks
            future_to_link = {
                executor.submit(insert_single_link, link_url, idx, total_links): link_url
                for idx, link_url in enumerate(links_list, 1)
            }

            # Process completed inserts
            for future in as_completed(future_to_link):
                success, link_url, idx, error = future.result()
                if success:
                    inserted_count += 1
                    log_db(f"[{thread_name}] ✓ Inserted ({idx}/{total_links}): {link_url}")
                else:
                    failed_count += 1
                    log_error(f"[{thread_name}] ✗ Failed to insert ({idx}/{total_links}): {link_url} - {error}")

        log_success(
            f"[{thread_name}] Done → {unique_name}  "
            f"({inserted_count}/{total_links} links saved, {failed_count} failed)"
        )
    else:
        log_warning(f"[{thread_name}] No links collected for: {unique_name}")

    # Pass the replace parameter to filter function
    process_filter_company(company, replace=replace)

def add_all_link(all_companies: list, max_workers=3) -> None:
    """Step 1 — Crawl all company websites and store raw links."""
    total   = len(all_companies)

    safe_print(
        f"[STEP 1] Crawling {total} companies — 3 workers",
        color="cyan", icon=Icons.SEARCH,
    )
    print_separator()

    completed = failed = 0

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Crawler") as executor:
        futures = {
            executor.submit(process_company, company): company
            for company in all_companies
        }

        for future in as_completed(futures):
            company = futures[future]
            try:
                future.result()
                completed += 1
            except Exception as exc:
                failed += 1
                log_error(f"Company '{company.get('unique_name')}' raised an error: {exc}")

            safe_print(
                f"Progress: {completed + failed}/{total}  ✅ {completed}  ❌ {failed}",
                color="white",
            )

    print_separator()
    safe_print(
        f"[STEP 1] Finished — {completed} succeeded, {failed} failed out of {total}",
        color="green" if failed == 0 else "yellow",
        icon=Icons.SUCCESS if failed == 0 else Icons.WARNING,
    )


# ──────────────────────────────────────────────
#  Task 2 — Filter links via AI agent
# ──────────────────────────────────────────────

def process_filter_company(company: dict, maximum=10, replace=False, batch_size=1000) -> None:
    """Run AI filter on a single company's links and persist results."""
    unique_name = company.get("unique_name")
    thread_name = threading.current_thread().name

    # Per-thread DB handles — avoids shared-state issues
    link_db = link.LinkTable()
    filter_link_db = link.FilterLinkTable()

    log_worker(f"[{thread_name}] Filtering → {unique_name}")

    # If replace is False, check existing links
    if not replace:
        existing_filter_links = filter_link_db.get_filter_links_by_unique_name(unique_name)

        # Skip if already have enough filtered links (maximum or more)
        if existing_filter_links and len(existing_filter_links) >= maximum:
            log_skip(
                f"[{thread_name}] Already has {len(existing_filter_links)} filtered links (>= {maximum}), skipping: {unique_name}")
            return

        # Continue if we have some but less than maximum
        if existing_filter_links:
            log_info(
                f"[{thread_name}] Already has {len(existing_filter_links)} filtered links, need {maximum - len(existing_filter_links)} more")
    else:
        # Replace mode - just log that we're running fresh
        log_info(f"[{thread_name}] Replace mode enabled - running fresh filter")
        existing_filter_links = None

    get_links = link_db.get_links_by_unique_name(unique_name)
    if not get_links:
        log_warning(f"[{thread_name}] No raw links found for: {unique_name}")
        return

    link_list = [each.get("link") for each in get_links]
    log_info(f"[{thread_name}] Running AI filter on {len(link_list)} links...")

    # CHUNKING LOGIC: Split link_list into batches
    all_filtered_links = []
    total_links = len(link_list)

    # Calculate number of batches
    num_batches = (total_links + batch_size - 1) // batch_size
    if num_batches > 1:
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_links)
            batch_links = link_list[start_idx:end_idx]

            log_info(f"[{thread_name}] Processing batch {batch_idx + 1}/{num_batches} ({len(batch_links)} links)")

            # Process this batch through AI filter
            batch_filtered = company_agent.get_filter_link(batch_links, maximum=maximum)

            # Extend the overall list with results from this batch
            if batch_filtered:
                all_filtered_links.extend(batch_filtered)
                log_info(f"[{thread_name}] Batch {batch_idx + 1} returned {len(batch_filtered)} filtered links")
            else:
                log_info(f"[{thread_name}] Batch {batch_idx + 1} returned no filtered links")

        filter_link = company_agent.get_filter_link(all_filtered_links, maximum=maximum)

    else:
        # If only one batch, process normally
        filter_link = company_agent.get_filter_link(link_list, maximum=maximum)
        log_info(f"[{thread_name}] Single batch processed, got {len(filter_link)} filtered links")
    # Now all_filtered_links contains the combined results from all batches

    log_info(f"[{thread_name}] Total filtered links from all batches: {len(filter_link)}")

    # If we already have some existing links (and not replace mode), we need to:
    # 1. Remove duplicates (don't re-insert existing ones)
    # 2. Only add up to the maximum limit
    if existing_filter_links and not replace:
        # Convert existing links to a set for faster lookup
        existing_links_set = {link.get("link") if isinstance(link, dict) else link for link in existing_filter_links}

        # Filter out links that already exist
        new_filter_links = [link for link in filter_link if link not in existing_links_set]

        # Calculate how many more we need
        needed_count = maximum - len(existing_filter_links)

        if needed_count <= 0:
            log_info(f"[{thread_name}] Already have enough filtered links ({len(existing_filter_links)}/{maximum})")
            return

        # Take only up to the needed count
        links_to_add = new_filter_links[:needed_count]

        log_info(
            f"[{thread_name}] Adding {len(links_to_add)} new filtered links (already had {len(existing_filter_links)})")
    else:
        # No existing links OR replace mode - just take up to maximum
        links_to_add = filter_link[:maximum]
        log_info(f"[{thread_name}] Adding {len(links_to_add)} filtered links (max {maximum})")

    # Insert the new filtered links
    if links_to_add:
        log_info(f"Inserting {len(links_to_add)} filtered links into DB for: {unique_name}")
        for each in links_to_add:
            filter_link_db.insert_filter_link(unique_name=unique_name, link=each, replace=replace)
            log_db(f"[{thread_name}] Inserted → {each}")

        if existing_filter_links and not replace:
            final_count = len(existing_filter_links) + len(links_to_add)
        else:
            final_count = len(links_to_add)

        log_success(
            f"[{thread_name}] Done → {unique_name}  ({final_count}/{maximum} filter links saved)"
        )
    else:
        log_info(f"[{thread_name}] No new filtered links to add for: {unique_name}")



def add_filter_link(all_companies: list, max_workers=3) -> None:
    """Step 2 — AI-filter the collected links for each company."""
    total = len(all_companies)

    safe_print(
        f"[STEP 2] Filtering links for {total} companies — {max_workers} workers",
        color="cyan", icon=Icons.SEARCH,
    )
    print_separator()

    completed = failed = 0

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Filter") as executor:
        futures = {
            executor.submit(process_filter_company, company): company
            for company in all_companies
        }

        for future in as_completed(futures):
            company = futures[future]
            try:
                future.result()
                completed += 1
            except Exception as exc:
                failed += 1
                log_error(f"Company '{company.get('unique_name')}' raised an error: {exc}")

            safe_print(
                f"Progress: {completed + failed}/{total}  ✅ {completed}  ❌ {failed}",
                color="white",
            )

    print_separator()
    safe_print(
        f"[STEP 2] Finished — {completed} succeeded, {failed} failed out of {total}",
        color="green" if failed == 0 else "yellow",
        icon=Icons.SUCCESS if failed == 0 else Icons.WARNING,
    )


# ──────────────────────────────────────────────
#  Entry point — run both steps in sequence
# ──────────────────────────────────────────────

if __name__ == "__main__":
    '''
    company_name_link_db = company_name_link.CompanyNameLink()
    all_companies        = company_name_link_db.get_all_companies()

    safe_print(
        f"Pipeline starting — {len(all_companies)} companies total",
        color="cyan", icon=Icons.INFO,
    )
    print_separator()

    #add_all_link(all_companies)      # Step 1 — crawl & collect

    #safe_print("")                   # blank line between steps

    add_filter_link(all_companies)   # Step 2 — AI filter
    '''