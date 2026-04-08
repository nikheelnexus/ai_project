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
from multiprocessing import Pool
from functools import partial
import time


def process_exhibitor(exhibitor_data, output_file, run_id, total_exhibitors):
    """Process a single exhibitor"""
    unique_name = exhibitor_data.get('unique_name')
    company_website = exhibitor_data.get('company_website')
    company_name = exhibitor_data.get('company_name', 'N/A')

    try:
        get_all_link = website_script.get_all_link(company_website)

        if not get_all_link:
            return {
                'unique_name': unique_name,
                'company_name': company_name,
                'website': company_website,
                'failed_timestamp': datetime.now().isoformat(),
                'reason': 'No links found',
                'task_id': run_id,
                'status': 'failed'
            }
        else:
            return {
                'unique_name': unique_name,
                'company_name': company_name,
                'website': company_website,
                'status': 'success',
                'task_id': run_id
            }
    except Exception as e:
        return {
            'unique_name': unique_name,
            'company_name': company_name,
            'website': company_website,
            'failed_timestamp': datetime.now().isoformat(),
            'reason': f'Error: {str(e)}',
            'task_id': run_id,
            'status': 'failed'
        }


def run_parallel_exhibitors():
    __exibition_db = exibition_db.ExhibitorDB()
    all_companies = __exibition_db.get_all_exhibitors()

    # Filter companies with website
    companies_with_website = []
    companies_without_website = []

    for eachCompany in all_companies:
        company_website = eachCompany.get('company_website')
        if company_website:
            companies_with_website.append(eachCompany)
        else:
            companies_without_website.append(eachCompany)

    total_companies = len(companies_with_website)
    total_all = len(all_companies)
    no_website_count = len(companies_without_website)

    print(f"\n📊 Total exhibitors in database: {total_all}")
    print(f"🌐 Exhibitors with website: {total_companies}")
    print(f"⚠️ Exhibitors without website (skipped): {no_website_count}")

    if no_website_count > 0:
        print(f"   ℹ️ Skipping {no_website_count} exhibitors that have no website URL")

    if total_companies == 0:
        print(f"\n✅ No exhibitors with websites to process!")
        return

    print(f"🚀 Starting parallel processing with 3 workers...\n")

    output_file = 'failed_exhibitors_links.json'
    current_run_time = datetime.now().isoformat()

    # Load existing data
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            all_failed = json.load(f)
        print(f"📂 Loaded {len(all_failed)} existing failed records")
    else:
        all_failed = {}
        print(f"📂 No existing failed records found")

    # Filter out exhibitors that already exist in failed records
    exhibitors_to_process = []
    skipped_exhibitors = []

    for exhibitor in companies_with_website:
        unique_name = exhibitor.get('unique_name')
        if unique_name in all_failed:
            skipped_exhibitors.append(unique_name)
        else:
            exhibitors_to_process.append(exhibitor)

    total_to_process = len(exhibitors_to_process)
    skipped_count = len(skipped_exhibitors)

    print(f"\n📊 Processing Summary:")
    print(f"   Total exhibitors with website: {total_companies}")
    print(f"   Already failed (skipped): {skipped_count}")
    print(f"   New exhibitors to process: {total_to_process}")

    if skipped_count > 0:
        print(f"   ⏭️ Skipping {skipped_count} exhibitors that already exist in failed records")

    if total_to_process == 0:
        print(f"\n✅ No new exhibitors to process! All exhibitors already recorded as failed.")
        return

    # Split exhibitors into 3 batches
    batch_size = total_to_process // 3
    batches = [
        exhibitors_to_process[:batch_size],
        exhibitors_to_process[batch_size:batch_size * 2],
        exhibitors_to_process[batch_size * 2:]
    ]

    # Print batch sizes
    print(f"\n📦 Batch distribution:")
    for i, batch in enumerate(batches):
        print(f"   Batch {i + 1}: {len(batch)} exhibitors")

    # Progress tracking variables
    completed = 0
    failed_count = 0
    success_count = 0
    start_time = time.time()

    # Process with 3 parallel workers
    with Pool(processes=3) as pool:
        # Prepare all tasks
        tasks = []
        for batch_id, batch in enumerate(batches):
            for exhibitor in batch:
                tasks.append((exhibitor, output_file, batch_id, total_to_process))

        # Process with async results
        async_results = [pool.apply_async(process_exhibitor, task) for task in tasks]

        # Collect results with progress tracking
        for i, async_result in enumerate(async_results, 1):
            failure = async_result.get()
            completed = i

            # Calculate and display progress
            percentage = (completed / total_to_process) * 100
            elapsed_time = time.time() - start_time

            # Calculate ETA
            if completed > 0:
                avg_time_per_company = elapsed_time / completed
                remaining = total_to_process - completed
                eta_seconds = remaining * avg_time_per_company
                eta_minutes = eta_seconds / 60
                eta_text = f"{int(eta_minutes)}m {int(eta_seconds % 60)}s" if eta_minutes < 60 else f"{int(eta_minutes / 60)}h {int(eta_minutes % 60)}m"
            else:
                eta_text = "calculating..."

            if failure and failure.get('status') == 'failed':
                failed_count += 1
                unique_name = failure['unique_name']
                all_failed[unique_name] = failure

                # Progress bar with skip info
                print(
                    f"\r[{completed}/{total_to_process}] {percentage:.1f}% | ✅ Success: {success_count} | ❌ Failed: {failed_count} | ⏭️ Skipped: {skipped_count} | ⏱️ ETA: {eta_text}",
                    end='', flush=True)

                # Save incrementally
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_failed, f, indent=4, ensure_ascii=False)
            else:
                success_count += 1
                print(
                    f"\r[{completed}/{total_to_process}] {percentage:.1f}% | ✅ Success: {success_count} | ❌ Failed: {failed_count} | ⏭️ Skipped: {skipped_count} | ⏱️ ETA: {eta_text}",
                    end='', flush=True)

    # Final summary
    elapsed_time = time.time() - start_time
    print(f"\n\n{'=' * 60}")
    print(f"📊 FINAL SUMMARY - EXHIBITORS")
    print(f"{'=' * 60}")
    print(f"📌 Total exhibitors in database: {total_all}")
    print(f"⚠️ No website URL: {no_website_count}")
    print(f"🌐 With website URL: {total_companies}")
    print(f"⏭️ Skipped (already in failed.json): {skipped_count}")
    print(f"🆕 Newly processed: {total_to_process}")
    print(f"   ✅ Successful in this run: {success_count}")
    print(f"   ❌ Failed in this run: {failed_count}")
    print(f"📊 Total failed exhibitors in file: {len(all_failed)}")
    print(f"⏱️ Total time taken: {int(elapsed_time // 60)}m {int(elapsed_time % 60)}s")
    print(f"💾 Failed exhibitors saved to: {output_file}")
    print(f"{'=' * 60}\n")

    # Print sample of skipped exhibitors if any
    if skipped_count > 0 and skipped_count <= 10:
        print(f"⏭️ Skipped exhibitors:")
        for name in skipped_exhibitors:
            print(f"   - {name}")
    elif skipped_count > 10:
        print(f"⏭️ Skipped {skipped_count} exhibitors (use 'view_skipped_exhibitors.py' to see full list)")

    # Print exhibitors without website
    if no_website_count > 0 and no_website_count <= 10:
        print(f"\n⚠️ Exhibitors without website:")
        for exhibitor in companies_without_website:
            print(f"   - {exhibitor.get('unique_name', 'N/A')} (Name: {exhibitor.get('company_name', 'N/A')})")
    elif no_website_count > 10:
        print(f"\n⚠️ {no_website_count} exhibitors have no website URL")


if __name__ == "__main__":
    run_parallel_exhibitors()