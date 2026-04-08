import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Any

from agent.agents import company_agent_template, text_util_agent, company_agent
from common_script import website_script, common
from company_ai_project.database.company_database import company_name_link, link
from company_ai_project.database.exibition_database import exibition_db

# Database connections
company_name_link_db = company_name_link.CompanyNameLink()
_exibition_db = exibition_db.ExhibitorDB()

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
}


class Icons:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️ "
    INFO = "ℹ️ "
    DATABASE = "💾"
    LINK = "🔗"
    SEARCH = "🔍"
    TRASH = "🗑️ "
    UPDATE = "🔄"
    SKIP = "⏭️ "
    WORKER = "🧵"


def safe_print(message: str, color: str = "", icon: str = ""):
    """Thread-safe print with timestamp, optional color and icon."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = f"{icon} " if icon else ""
    line = f"[{timestamp}] {prefix}{message}"
    with print_lock:
        if color and color in COLORS:
            print(f"{COLORS[color]}{line}\033[0m")
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
def print_separator(): safe_print("─" * 60, color="gray")


# ──────────────────────────────────────────────
#  Transfer function
# ──────────────────────────────────────────────

def transfer_from_exibition():
    all_exibition = _exibition_db.get_all_exhibitors()
    total = len(all_exibition)

    # Use mutable objects for thread-safe counters
    completed = 0
    success_count = 0
    failed_count = 0

    # Add locks for counters
    counter_lock = threading.Lock()

    def process_each(each):
        nonlocal completed, success_count, failed_count
        company_name = each.get('company_name')
        website = each.get('company_website')
        unique_name = each.get('unique_name')

        if website:
            log_worker(f"Processing: {company_name}")
            log_link(f"Website: {website}")

            try:
                exist = company_name_link_db.get_company(unique_name=unique_name)
                if not exist:
                    company_name_link_db.insert_company(
                        company_name=company_name,
                        website=website,
                        unique_name=unique_name
                    )

                with counter_lock:
                    completed += 1
                    success_count += 1
                    log_success(f"[{completed}/{total}] Transferred: {company_name}")
                return True
            except Exception as e:
                with counter_lock:
                    completed += 1
                    failed_count += 1
                    log_error(f"[{completed}/{total}] Failed: {company_name} - {e}")
                return False
        else:
            with counter_lock:
                completed += 1
                failed_count += 1
                log_skip(f"[{completed}/{total}] Skipped: {company_name} - No website")
            return False

    log_info(f"Starting transfer of {total} exhibitors with 3 parallel workers")
    print_separator()

    # Run 3 tasks at the same time - CONSUME the iterator
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(process_each, all_exibition))  # Convert to list to execute all

    print_separator()
    log_success(f"Transfer completed - Success: {success_count}, Failed: {failed_count}, Total: {total}")