from agent.agents import company_agent
import json
from agent.common_agent import ai_agent_utils
from common_script import website_script, common
from company_ai_project.database.company_database import company_name_link, link
from company_ai_project.database.exibition_database import exibition_db
from threading import Lock
from datetime import datetime
import os
from company_ai_project.automate import exibition_automate

# Thread-safe print lock
print_lock = Lock()


def safe_print(message, color_code=""):
    """Thread-safe printing with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with print_lock:
        if color_code:
            print(f"{color_code}[{timestamp}] {message}\033[0m")
        else:
            print(f"[{timestamp}] {message}")


# Color codes for different message types
COLORS = {
    "gray": "\033[90m",
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m"
}


class Icons:
    """Unicode icons for status messages."""
    SUCCESS = '✅'
    ERROR = '❌'
    WARNING = '⚠️'
    INFO = 'ℹ️'
    DATABASE = '💾'
    COMPANY = '🏢'
    WEBSITE = '🌐'
    SEARCH = '🔍'
    TRASH = '🗑️'
    UPDATE = '🔄'
    VALIDATION = '🔍'


company_name_link_db = company_name_link.CompanyNameLink()
_exibition_db = exibition_db.ExhibitorDB()

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import os
from queue import Queue
import time

file_lock = Lock()
chunk_queue = Queue()
chunk_id_lock = Lock()
next_chunk_id = 0

# Global counters for progress tracking
total_processed = 0
total_successful = 0
total_failed = 0
total_companies_to_process = 0
processed_chunks = 0
total_chunks = 0

# Track failed companies with details
failed_companies = []  # List to store failed company details
failed_companies_lock = Lock()


def get_total_lines_count(file_path):
    """Get total number of lines in the file for progress tracking"""
    with open(file_path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def load_all_chunks(file_path, lines_per_chunk=50):
    """Load all chunks from file without modifying the original file"""
    global total_chunks

    if not os.path.isfile(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    if not all_lines:
        return []

    chunks = []
    for i in range(0, len(all_lines), lines_per_chunk):
        chunk = [line.strip() for line in all_lines[i:i + lines_per_chunk]]
        chunks.append(chunk)

    total_chunks = len(chunks)
    return chunks


def get_next_chunk_from_queue():
    """Get next chunk from queue"""
    global next_chunk_id

    try:
        chunk = chunk_queue.get_nowait()
        with chunk_id_lock:
            chunk_id = next_chunk_id
            next_chunk_id += 1
        return chunk, chunk_id
    except:
        return None, None


def log_failed_company(company_name, chunk_id, error_message, company_data=None):
    """Log failed company details"""
    with failed_companies_lock:
        failed_companies.append({
            'company_name': company_name,
            'chunk_id': chunk_id,
            'error': str(error_message),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'company_data': company_data
        })


def process_company(eachCompany, exibitor, company_index, total_companies_in_chunk, chunk_id):
    global total_processed, total_successful, total_failed

    company_name = eachCompany.get("company_name")
    if not company_name:
        with print_lock:
            total_failed += 1
            log_failed_company("UNKNOWN", chunk_id, "Company name is missing", eachCompany)
        return False

    eachCompany["exibition"] = exibitor
    safe_print(
        f"{Icons.COMPANY} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] Processing: {company_name}",
        COLORS["gray"])

    template = """Return ONLY the website URL as a raw string. NO JSON, NO explanation, NO additional text.
AND MAKE SURE IT SHOULD BE HOME PAGE"""

    try:
        safe_print(
            f"{Icons.SEARCH} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] Searching for website of {company_name}...",
            COLORS["blue"])
        json_content, content = ai_agent_utils.open_ai_text(company_name, template)
        content = content.split()

        formatted = ""
        if content:
            url = content[0]
            safe_print(
                f"{Icons.WEBSITE} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] Found URL: {url}",
                COLORS["yellow"])

            formatted = website_script.format_website_url(url)
            safe_print(
                f"{Icons.WEBSITE} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] Formatted URL: {formatted}",
                COLORS["gray"])

            safe_print(
                f"{Icons.VALIDATION} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] Checking website status...",
                COLORS["blue"])
            is_working, status_info = website_script.check_link_status(formatted)

            if not is_working:
                error_msg = f"Website not working: {formatted} (Status: {status_info})"
                safe_print(
                    f"{Icons.ERROR} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] {error_msg}",
                    COLORS["red"])
                formatted = ""
                with print_lock:
                    total_failed += 1
                    log_failed_company(company_name, chunk_id, error_msg, eachCompany)
                return False
            else:
                safe_print(
                    f"{Icons.SUCCESS} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] Website is working: {formatted}",
                    COLORS["green"])
        else:
            error_msg = "No URL found from AI response"
            safe_print(
                f"{Icons.ERROR} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] {error_msg}",
                COLORS["red"])
            with print_lock:
                total_failed += 1
                log_failed_company(company_name, chunk_id, error_msg, eachCompany)
            return False

        safe_print(
            f"{Icons.DATABASE} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] Inserting into database...",
            COLORS["blue"])
        _exibition_db.insert_exhibitor(
            company_name=company_name,
            company_website=formatted,
            exhibitor_name=exibitor,
            company_data=eachCompany
        )

        with print_lock:
            total_processed += 1
            total_successful += 1

        safe_print(
            f"{Icons.SUCCESS} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] Successfully inserted {company_name} (Total: {total_successful}/{total_processed})",
            COLORS["green"])
        return True

    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        with print_lock:
            total_processed += 1
            total_failed += 1
            log_failed_company(company_name, chunk_id, error_msg, eachCompany)
        safe_print(
            f"{Icons.ERROR} [Chunk {chunk_id}] [{company_index}/{total_companies_in_chunk}] Error processing {company_name}: {e}",
            COLORS["red"])
        return False


def process_chunk_worker(exibitor, total_lines, chunk_id, chunk):
    """Worker function to process a single chunk"""
    global processed_chunks

    safe_print(f"{Icons.COMPANY} [Chunk {chunk_id}] Getting company names and websites from chunk...",
               COLORS["blue"])

    try:
        companydic = company_agent.get_company_name_website(str(chunk))
    except Exception as e:
        safe_print(f"{Icons.ERROR} [Chunk {chunk_id}] Failed to extract companies: {e}", COLORS["red"])
        with print_lock:
            processed_chunks += 1
        return

    total_in_chunk = len(companydic)

    # Calculate start index based on chunk_id
    companies_per_chunk_estimate = 50  # Approximate
    chunk_start_index = chunk_id * companies_per_chunk_estimate + 1

    safe_print(
        f"{Icons.INFO} [Chunk {chunk_id}]: Found {total_in_chunk} companies to process",
        COLORS["cyan"])

    success = 0
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        for idx, eachCompany in enumerate(companydic, start=1):
            future = executor.submit(process_company, eachCompany, exibitor, idx, total_in_chunk, chunk_id)
            futures[future] = idx

        for future in as_completed(futures):
            if future.result():
                success += 1

    with print_lock:
        chunk_success_rate = (success / total_in_chunk * 100) if total_in_chunk > 0 else 0
        processed_chunks += 1

    safe_print(
        f"{Icons.SUCCESS} [Chunk {chunk_id}] completed. Successful: {success}/{total_in_chunk} ({chunk_success_rate:.1f}%)",
        COLORS["green"])


def clear_file(file_path):
    """Clear the txt file after all processing is complete"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')  # Clear the file
            safe_print(f"{Icons.SUCCESS} File cleared successfully: {file_path}", COLORS["green"])
            return True
        else:
            safe_print(f"{Icons.WARNING} File not found: {file_path}", COLORS["yellow"])
            return False
    except Exception as e:
        safe_print(f"{Icons.ERROR} Failed to clear file: {e}", COLORS["red"])
        return False


def save_failed_companies_to_file():
    """Save failed companies details to a JSON log file"""
    if not failed_companies:
        return

    log_filename = f"failed_companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path = os.path.join(os.path.dirname(__file__), log_filename)

    try:
        # Prepare data for JSON
        log_data = {
            "report_info": {
                "generated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_failed": len(failed_companies),
                "report_type": "Failed Companies Report"
            },
            "failed_companies": []
        }

        # Add each failed company to the list
        for failed in failed_companies:
            log_data["failed_companies"].append({
                "company_name": failed['company_name'],
                "chunk_id": failed['chunk_id'],
                "timestamp": failed['timestamp'],
                "error": failed['error'],
                "company_data": failed.get('company_data', None)
            })

        # Write to JSON file
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        safe_print(f"{Icons.INFO} Failed companies log saved to: {log_path}", COLORS["cyan"])
        return log_path
    except Exception as e:
        safe_print(f"{Icons.ERROR} Failed to save log file: {e}", COLORS["red"])
        return None


def print_failed_companies_summary():
    """Print detailed summary of failed companies"""
    if not failed_companies:
        safe_print(f"{Icons.SUCCESS} No failed companies! All processed successfully.", COLORS["green"])
        return

    safe_print(f"\n{Icons.ERROR} {'=' * 60}", COLORS["red"])
    safe_print(f"{Icons.ERROR} FAILED COMPANIES DETAILS ({len(failed_companies)} failures):", COLORS["red"])
    safe_print(f"{Icons.ERROR} {'=' * 60}", COLORS["red"])

    # Group failures by error type
    error_types = {}
    for failed in failed_companies:
        error_key = failed['error'].split(':')[0]  # Get error category
        if error_key not in error_types:
            error_types[error_key] = []
        error_types[error_key].append(failed)

    # Print summary by error type
    safe_print(f"\n{Icons.INFO} SUMMARY BY ERROR TYPE:", COLORS["yellow"])
    for error_type, failures in error_types.items():
        safe_print(f"  • {error_type}: {len(failures)} company(ies)", COLORS["yellow"])

    # Print detailed list
    safe_print(f"\n{Icons.INFO} DETAILED LIST:", COLORS["yellow"])
    for idx, failed in enumerate(failed_companies, 1):
        safe_print(f"\n  {idx}. {Icons.ERROR} {failed['company_name']}", COLORS["red"])
        safe_print(f"     Chunk: {failed['chunk_id']}", COLORS["gray"])
        safe_print(f"     Error: {failed['error']}", COLORS["gray"])
        safe_print(f"     Time: {failed['timestamp']}", COLORS["gray"])

    safe_print(f"\n{Icons.ERROR} {'=' * 60}", COLORS["red"])


def rub_task(exibitor="gulffood", max_workers=5):
    global total_processed, total_successful, total_failed, total_companies_to_process, processed_chunks, total_chunks, next_chunk_id, chunk_queue, failed_companies

    # Reset counters
    total_processed = 0
    total_successful = 0
    total_failed = 0
    processed_chunks = 0
    next_chunk_id = 0
    failed_companies = []  # Reset failed companies list

    # Clear and reinitialize queue
    chunk_queue = Queue()

    filename = "exibition_text.txt"
    file_path = os.path.join(
        os.path.abspath(os.path.dirname(exibition_automate.__file__)),
        filename
    )

    if not os.path.isfile(file_path):
        safe_print(f"{Icons.ERROR} Error: {filename} not found at {file_path}", COLORS["red"])
        return

    # Load all chunks without modifying the file
    safe_print(f"{Icons.INFO} Loading chunks from {filename}...", COLORS["cyan"])
    all_chunks = load_all_chunks(file_path, lines_per_chunk=50)

    if not all_chunks:
        safe_print(f"{Icons.ERROR} No chunks loaded from file", COLORS["red"])
        return

    total_lines = sum(len(chunk) for chunk in all_chunks)
    total_chunks = len(all_chunks)

    # Add all chunks to queue
    for chunk in all_chunks:
        chunk_queue.put(chunk)

    safe_print(f"{Icons.INFO} Total lines to process: {total_lines}", COLORS["cyan"])
    safe_print(f"{Icons.INFO} Total chunks created: {total_chunks}", COLORS["cyan"])
    safe_print(f"{Icons.INFO} Total companies to process: ~{total_lines}", COLORS["cyan"])
    safe_print(f"{Icons.INFO} Processing {min(max_workers, total_chunks)} chunks simultaneously...", COLORS["cyan"])
    safe_print(f"{Icons.UPDATE} {'=' * 60}", COLORS["magenta"])

    # Process chunks with 3 concurrent workers
    with ThreadPoolExecutor(max_workers=max_workers) as chunk_executor:
        futures = []

        # Submit initial batch of chunks
        for _ in range(min(max_workers, total_chunks)):
            chunk, chunk_id = get_next_chunk_from_queue()
            if chunk is not None:
                future = chunk_executor.submit(process_chunk_worker, exibitor, total_lines, chunk_id, chunk)
                futures.append(future)

        # Continue submitting as chunks complete
        while processed_chunks < total_chunks:
            # Check if any future completed
            for future in as_completed(futures):
                if processed_chunks >= total_chunks:
                    break

                # Get next chunk from queue
                next_chunk, next_chunk_id = get_next_chunk_from_queue()
                if next_chunk is not None:
                    # Submit new chunk
                    new_future = chunk_executor.submit(process_chunk_worker, exibitor, total_lines, next_chunk_id,
                                                       next_chunk)
                    futures.append(new_future)

                # Remove completed future from list
                futures.remove(future)

                # Print cumulative progress after each chunk completes
                success_rate = (total_successful / total_processed * 100) if total_processed > 0 else 0
                safe_print(f"\n{Icons.INFO} {'=' * 60}", COLORS["cyan"])
                safe_print(f"{Icons.INFO} CUMULATIVE PROGRESS:", COLORS["cyan"])
                safe_print(f"{Icons.INFO} Chunks completed: {processed_chunks}/{total_chunks}", COLORS["cyan"])
                safe_print(f"{Icons.INFO} Total processed: {total_processed}/{total_lines} companies", COLORS["cyan"])
                safe_print(f"{Icons.SUCCESS} Successful: {total_successful}", COLORS["green"])
                safe_print(f"{Icons.ERROR} Failed: {total_failed}", COLORS["red"])
                safe_print(f"{Icons.INFO} Success rate: {success_rate:.1f}%", COLORS["cyan"])
                safe_print(f"{Icons.INFO} {'=' * 60}\n", COLORS["cyan"])

                break  # Break to re-evaluate the while condition

        # Wait for all remaining futures to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                safe_print(f"{Icons.ERROR} Chunk processing failed: {e}", COLORS["red"])

    # Print detailed failed companies summary
    print_failed_companies_summary()

    # Save failed companies to log file
    if failed_companies:
        log_file = save_failed_companies_to_file()
        if log_file:
            safe_print(f"{Icons.INFO} Check {log_file} for complete failure details", COLORS["cyan"])

    # CLEAR THE FILE AFTER ALL CHUNKS ARE PROCESSED
    safe_print(f"\n{Icons.UPDATE} {'=' * 60}", COLORS["yellow"])
    safe_print(f"{Icons.UPDATE} All chunks processed! Clearing the txt file...", COLORS["yellow"])
    clear_file(file_path)

    # Final summary
    safe_print(f"\n{Icons.SUCCESS} {'=' * 60}", COLORS["green"])
    safe_print(f"{Icons.SUCCESS} TASK COMPLETED - FINAL SUMMARY:", COLORS["green"])
    safe_print(f"{Icons.SUCCESS} Total chunks processed: {processed_chunks}/{total_chunks}", COLORS["green"])
    safe_print(f"{Icons.SUCCESS} Total companies processed: {total_processed}", COLORS["green"])
    safe_print(f"{Icons.SUCCESS} Successfully inserted: {total_successful}", COLORS["green"])
    safe_print(f"{Icons.ERROR} Failed: {total_failed}", COLORS["red"])
    safe_print(
        f"{Icons.INFO} Overall success rate: {(total_successful / total_processed * 100) if total_processed > 0 else 0:.1f}%",
        COLORS["cyan"])

    # Show failed companies count again at the end
    if failed_companies:
        safe_print(f"\n{Icons.ERROR} {len(failed_companies)} company(ies) failed. See details above.", COLORS["red"])

    safe_print(f"{Icons.SUCCESS} {'=' * 60}", COLORS["green"])