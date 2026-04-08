from company_ai_project.automate.company_automate import add_all_link, link_rewrite
from company_ai_project.automate.company_automate import overview as _overview
from company_ai_project.automate.company_automate import company_name_link as auto_company_name_link
from company_ai_project.automate.exibition_automate import exibition_automate
from company_ai_project.database.company_database import company_name_link, link, overview
from company_ai_project.database.exibition_database import exibition_db
from common_script import website_script, common
import json
from datetime import datetime
import os
from multiprocessing import Pool, cpu_count
from functools import partial
import time
import signal
import sys
import socket
from requests.exceptions import Timeout, ConnectionError


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⚠️ Received interrupt signal. Saving progress...")
    print("💾 Progress has been saved. You can restart the script to continue.")
    sys.exit(0)


# Register signal handler
signal.signal(signal.SIGINT, signal_handler)


def process_company(company_data, output_file, run_id, total_companies, shared_counter=None):
    """Process a single company with improved error handling"""
    unique_name = company_data.get('unique_name')
    website = company_data.get('website')

    try:
        get_all_link = website_script.get_all_link(website)

        if not get_all_link:
            return {
                'unique_name': unique_name,
                'website': website,
                'failed_timestamp': datetime.now().isoformat(),
                'reason': 'No links found',
                'task_id': run_id,
                'status': 'failed'
            }
        else:
            return {
                'unique_name': unique_name,
                'website': website,
                'status': 'success',
                'task_id': run_id
            }
    except KeyboardInterrupt:
        # Re-raise to handle at higher level
        raise
    except Timeout:
        return {
            'unique_name': unique_name,
            'website': website,
            'failed_timestamp': datetime.now().isoformat(),
            'reason': 'Request timeout',
            'task_id': run_id,
            'status': 'failed'
        }
    except ConnectionError as e:
        return {
            'unique_name': unique_name,
            'website': website,
            'failed_timestamp': datetime.now().isoformat(),
            'reason': f'Connection error: {str(e)[:100]}',
            'task_id': run_id,
            'status': 'failed'
        }
    except socket.error as e:
        return {
            'unique_name': unique_name,
            'website': website,
            'failed_timestamp': datetime.now().isoformat(),
            'reason': f'Socket error: {str(e)[:100]}',
            'task_id': run_id,
            'status': 'failed'
        }
    except Exception as e:
        return {
            'unique_name': unique_name,
            'website': website,
            'failed_timestamp': datetime.now().isoformat(),
            'reason': f'Error: {str(e)[:100]}',
            'task_id': run_id,
            'status': 'failed'
        }


def run_parallel():
    company_name_link_db = company_name_link.CompanyNameLink()

    print(f"\n{'=' * 60}")
    print(f"🚀 COMPANY LINK EXTRACTION SYSTEM")
    print(f"{'=' * 60}")
    print(f"⚠️  Press Ctrl+C to stop gracefully\n")

    try:
        all_companies = company_name_link_db.get_companies_by_date()
    except Exception as e:
        print(f"❌ Error fetching companies: {str(e)}")
        return

    total_companies = len(all_companies)

    print(f"\n📊 Total companies to process: {total_companies}")
    print(f"🚀 Starting parallel processing...\n")

    output_file = 'failed_companies_links_1.json'
    current_run_time = datetime.now().isoformat()

    # Load existing data
    all_failed = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                all_failed = json.load(f)
            print(f"📂 Loaded {len(all_failed)} existing failed records")
        except Exception as e:
            print(f"⚠️ Could not load existing records: {str(e)}. Starting fresh.")
            all_failed = {}
    else:
        print(f"📂 No existing failed records found")

    # Filter out companies that already exist in failed records
    companies_to_process = []
    skipped_companies = []

    for company in all_companies:
        unique_name = company.get('unique_name')
        if unique_name and unique_name in all_failed:
            skipped_companies.append(unique_name)
        else:
            companies_to_process.append(company)

    total_to_process = len(companies_to_process)
    skipped_count = len(skipped_companies)

    print(f"\n📊 Processing Summary:")
    print(f"   Total companies: {total_companies}")
    print(f"   Already failed (skipped): {skipped_count}")
    print(f"   New companies to process: {total_to_process}")

    if skipped_count > 0:
        print(f"   ⏭️ Skipping {skipped_count} companies that already exist in failed records")

    if total_to_process == 0:
        print(f"\n✅ No new companies to process! All companies already recorded as failed.")
        return

    # Use fewer processes to avoid overwhelming the system
    num_processes = min(5, cpu_count())
    print(f"\n🔧 Using {num_processes} parallel workers")

    # Progress tracking variables
    completed = 0
    failed_count = 0
    success_count = 0
    start_time = time.time()

    pool = None

    try:
        # Process with parallel workers
        pool = Pool(processes=num_processes)

        # Prepare all tasks
        tasks = []
        for company in companies_to_process:
            tasks.append((company, output_file, 0, total_to_process))

        # Process with async results
        async_results = [pool.apply_async(process_company, task) for task in tasks]

        # Collect results with progress tracking
        for i, async_result in enumerate(async_results, 1):
            try:
                # Add timeout to get to prevent hanging
                failure = async_result.get(timeout=30)
            except Exception as e:
                # Handle timeout or other errors in getting result
                failure = {
                    'status': 'failed',
                    'unique_name': 'unknown',
                    'reason': f'Result retrieval error: {str(e)[:100]}'
                }

            completed = i

            # Calculate and display progress
            percentage = (completed / total_to_process) * 100
            elapsed_time = time.time() - start_time

            # Calculate ETA
            if completed > 0:
                avg_time_per_company = elapsed_time / completed
                remaining = total_to_process - completed
                eta_seconds = remaining * avg_time_per_company
                if eta_seconds < 60:
                    eta_text = f"{int(eta_seconds)}s"
                elif eta_seconds < 3600:
                    eta_text = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                else:
                    eta_text = f"{int(eta_seconds // 3600)}h {int((eta_seconds % 3600) // 60)}m"
            else:
                eta_text = "calculating..."

            if failure and failure.get('status') == 'failed':
                failed_count += 1
                unique_name = failure.get('unique_name')
                if unique_name and unique_name != 'unknown':
                    all_failed[unique_name] = failure

                # Save incrementally every 10 failures or at completion
                if failed_count % 10 == 0 or completed == total_to_process:
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(all_failed, f, indent=4, ensure_ascii=False)
                    except Exception as e:
                        print(f"\n⚠️ Warning: Could not save progress: {str(e)}")
            else:
                success_count += 1

            # Progress bar
            bar_length = 30
            filled_length = int(bar_length * completed // total_to_process)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)

            print(
                f"\r[{completed}/{total_to_process}] {bar} {percentage:.1f}% | ✅ {success_count} | ❌ {failed_count} | ⏭️ {skipped_count} | ⏱️ {eta_text}",
                end='', flush=True)

        print()  # New line after progress bar

        # Final save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_failed, f, indent=4, ensure_ascii=False)

    except KeyboardInterrupt:
        print(f"\n\n{'=' * 60}")
        print(f"⚠️ PROCESS INTERRUPTED BY USER")
        print(f"{'=' * 60}")
        print(f"✅ Progress saved: {completed}/{total_to_process} companies processed")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"💾 Failed companies saved to: {output_file}")
        print(f"🔄 You can restart the script to continue from where it stopped")
        print(f"{'=' * 60}\n")

        # Save current progress
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_failed, f, indent=4, ensure_ascii=False)
        except:
            pass

    except Exception as e:
        print(f"\n\n{'=' * 60}")
        print(f"❌ ERROR OCCURRED")
        print(f"{'=' * 60}")
        print(f"Error: {str(e)}")
        print(f"✅ Progress saved: {completed}/{total_to_process} companies processed")
        print(f"💾 Partial progress saved to: {output_file}")
        print(f"{'=' * 60}\n")

        # Save partial progress
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_failed, f, indent=4, ensure_ascii=False)
        except:
            pass

    finally:
        # Clean up pool
        if pool:
            pool.terminate()
            pool.join()
            print("🔒 Process pool cleaned up")

    # Final summary (only if not interrupted early)
    if completed == total_to_process:
        elapsed_time = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"📊 FINAL SUMMARY")
        print(f"{'=' * 60}")
        print(f"📌 Total companies in database: {total_companies}")
        print(f"⏭️ Skipped (already in failed.json): {skipped_count}")
        print(f"🆕 Newly processed: {total_to_process}")
        print(f"   ✅ Successful in this run: {success_count}")
        print(f"   ❌ Failed in this run: {failed_count}")
        print(f"📊 Total failed companies in file: {len(all_failed)}")

        if elapsed_time < 60:
            time_str = f"{int(elapsed_time)} seconds"
        elif elapsed_time < 3600:
            time_str = f"{int(elapsed_time // 60)}m {int(elapsed_time % 60)}s"
        else:
            time_str = f"{int(elapsed_time // 3600)}h {int((elapsed_time % 3600) // 60)}m"

        print(f"⏱️ Total time taken: {time_str}")
        print(f"💾 Failed companies saved to: {output_file}")
        print(f"{'=' * 60}\n")

        # Print skipped companies if any
        if skipped_count > 0 and skipped_count <= 10:
            print(f"⏭️ Skipped companies:")
            for name in skipped_companies:
                print(f"   - {name}")
        elif skipped_count > 10:
            print(f"⏭️ Skipped {skipped_count} companies (already in failed records)")


if __name__ == "__main__":
    run_parallel()