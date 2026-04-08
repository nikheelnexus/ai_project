from company_ai_project_old.database_old import certification_database
import json
from agent.agents import company_agent
from agent.common_agent import common_agent
from agent.agents import company_agent_template, text_util_agent_template
from company_ai_project.database.certification_database import certification_db
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

print_lock = threading.Lock()  # Remove duplicate

COLORS = {
    "gray": "\033[90m",
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "reset": "\033[0m",  # Add reset here directly
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


def print_separator(): safe_print("─" * 60, color="gray")


_certification_db = certification_db.CertificationDB()

certification_database_db = certification_database.CertificationDB()
all_certification = certification_database_db.get_all_certifications()

# Progress tracking
progress_lock = threading.Lock()
completed_count = 0
total_count = len(all_certification)


class CertificationProcessor:
    """Handles concurrent certification processing"""

    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.print_lock = threading.Lock()
        self.progress_lock = threading.Lock()
        self.completed_count = 0
        self.total_count = 0
        self._init_databases()

    def _init_databases(self):
        """Initialize database connections"""
        self.certification_db = certification_db.CertificationDB()
        self.old_certification_db = certification_database.CertificationDB()

    def _update_progress(self):
        """Update and display progress with nice formatting"""
        with self.progress_lock:
            self.completed_count += 1
            percentage = (self.completed_count / self.total_count) * 100
            bar_length = 30
            filled_length = int(bar_length * self.completed_count // self.total_count)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            progress_text = f"📊 Progress: {self.completed_count}/{self.total_count} | [{bar}] | {percentage:.1f}%"
            return progress_text

    def _process_certification(self, certification_item, worker_id):
        """Process a single certification"""
        certification_name = certification_item['certification_name']
        start_time = time.time()

        try:
            get_certification = self.certification_db.search_certifications(search_term=certification_name)

            if not get_certification:
                log_worker(f"[Worker {worker_id}] 🔄 Processing: {certification_name[:50]}...")

                certification_ai = common_agent.common_agent(
                    template=company_agent_template.explain_certification_markdown(),
                    input_str=str(certification_name),
                    json_convert=False
                )

                self.certification_db.insert_certification(
                    certification_name=certification_name,
                    certification_data=certification_ai
                )

                elapsed_time = time.time() - start_time
                log_success(f"[Worker {worker_id}] ✅ Completed: {certification_name[:50]}... ({elapsed_time:.2f}s)")
                success = True
            else:
                elapsed_time = time.time() - start_time
                log_skip(
                    f"[Worker {worker_id}] ⏭️ Skipped (exists): {certification_name[:50]}... ({elapsed_time:.2f}s)")
                success = True

            progress_msg = self._update_progress()
            with self.print_lock:
                print(f"\r{COLORS['cyan']}{progress_msg}{COLORS['reset']}", end="", flush=True)

            return success, certification_name

        except Exception as e:
            elapsed_time = time.time() - start_time
            log_error(
                f"[Worker {worker_id}] ❌ Failed: {certification_name[:50]}... - {str(e)[:100]} ({elapsed_time:.2f}s)")

            progress_msg = self._update_progress()
            with self.print_lock:
                print(f"\r{COLORS['cyan']}{progress_msg}{COLORS['reset']}", end="", flush=True)

            return False, certification_name

    def run(self):
        """Execute the certification processing"""
        all_certification = self.old_certification_db.get_all_certifications()
        self.total_count = len(all_certification)

        log_info(f"🚀 Starting concurrent processing with {self.max_workers} workers...")
        log_info(f"📋 Total certifications to process: {self.total_count}")
        print_separator()

        print(f"\n{COLORS['cyan']}📊 Progress: 0/{self.total_count} | [{'░' * 30}] | 0.0%{COLORS['reset']}")

        successful = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_cert = {}
            worker_id = 0

            for cert in all_certification:
                future_to_cert[
                    executor.submit(self._process_certification, cert, worker_id % self.max_workers + 1)] = cert
                worker_id += 1

            for future in as_completed(future_to_cert):
                cert = future_to_cert[future]
                try:
                    success, cert_name = future.result()
                    if success:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    log_error(f"Unexpected error for {cert.get('certification_name', 'unknown')}: {str(e)}")

        # Print final summary
        print_separator()
        print("\n" + "=" * 70)
        log_success(f"🎉 PROCESSING COMPLETE!")
        log_info(f"📊 Final Statistics:")
        log_info(f"   ✅ Successful/Processed: {successful}")
        log_info(f"   ❌ Failed: {failed}")
        log_info(f"   📋 Total: {self.total_count}")
        log_info(f"   ⚡ Speed: {self.max_workers}x concurrent")
        print("=" * 70)

        return {'successful': successful, 'failed': failed, 'total': self.total_count}


# Usage
if __name__ == "__main__":
    processor = CertificationProcessor(max_workers=3)
    results = processor.run()
    print(f"\nResults: {results}")