import json
from threading import Lock
import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock
import os
from company_ai_project.saved_data import user_data
from common_script import common

from company_ai_project.database.user_database import user, user_comparable
from company_ai_project.database.company_database import company_information, company_name_link, link, overview
from agent.agents import user_agent

user_comparable_db = user_comparable.UserComparableDB()
company_name_link_db = company_name_link.CompanyNameLink()
overview_db = overview.OverviewTable()
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
    COMPARE = '🔄'
    WEBSITE = '🌐'
    SEARCH = '🔍'
    TRASH = '🗑️'
    UPDATE = '📝'
    JSON = '📄'
    STATS = '📊'



def get_all_user_data():
    '''
    Get all user data from database

    :return: list of user data
    '''
    user_db = user.UserDB()
    all_user = user_db.get_all_users()

    return all_user


from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


def compare_company(max_workers=3):
    '''
    Compare all users against all client companies with parallel processing
    '''
    safe_print("Starting company comparison process", COLORS["cyan"] + Icons.COMPARE)

    all_user = get_all_user_data()
    safe_print(f"Retrieved {len(all_user)} users from database", COLORS["blue"] + Icons.INFO)

    overview_list = overview_db.get_all_overviews()
    safe_print(f"Retrieved {len(overview_list)} client overviews", COLORS["blue"] + Icons.INFO)

    # Print header for the comparison process
    safe_print("=" * 80, COLORS["cyan"])
    safe_print(f"{Icons.COMPARE} STARTING COMPARISON PROCESS WITH {max_workers} WORKERS {Icons.COMPARE}",
               COLORS["cyan"])
    safe_print("=" * 80, COLORS["cyan"])

    # Prepare all comparison tasks
    comparison_tasks = []

    for eachUser in all_user:
        website = eachUser['website']
        user_company_data = company_name_link_db.search_companies(website)

        if user_company_data:
            user_company_data = user_company_data[0]
            user_unique_name = user_company_data['unique_name']

            user_main_overview = overview_db.get_main_overview(unique_name=user_unique_name)
            user_small_overview = overview_db.get_small_overview(unique_name=user_unique_name)
            user_final_overview = f'{user_main_overview}\n\n\n{user_small_overview}'

            for eachOverview in overview_list:
                client_unique_name = eachOverview['unique_name']

                # Skip comparing with self
                if client_unique_name == user_unique_name:
                    continue

                # Check if comparison already exists
                compare_data = user_comparable_db.get_comparison_by_names(
                    user_unique_name=user_unique_name,
                    client_unique_name=client_unique_name
                )
                if compare_data:
                    continue

                # Add task to list
                comparison_tasks.append({
                    'user_unique_name': user_unique_name,
                    'client_unique_name': client_unique_name,
                    'user_final_overview': user_final_overview,
                    'website': website
                })

    safe_print(f"Prepared {len(comparison_tasks)} comparison tasks to process", COLORS["blue"] + Icons.INFO)

    # Process tasks in parallel
    completed_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {}
        for task in comparison_tasks:
            future = executor.submit(
                process_single_comparison,
                task['user_unique_name'],
                task['client_unique_name'],
                task['user_final_overview']
            )
            future_to_task[future] = task

        # Process completed tasks
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                result = future.result()
                if result:
                    completed_count += 1
                    safe_print(
                        f"✅ [{completed_count}/{len(comparison_tasks)}] Completed: {task['user_unique_name']} → {task['client_unique_name']}",
                        COLORS["green"] + Icons.SUCCESS
                    )
                else:
                    failed_count += 1
                    safe_print(
                        f"❌ Failed: {task['user_unique_name']} → {task['client_unique_name']}",
                        COLORS["red"] + Icons.ERROR
                    )
            except Exception as e:
                failed_count += 1
                safe_print(
                    f"❌ Exception in {task['user_unique_name']} → {task['client_unique_name']}: {str(e)}",
                    COLORS["red"] + Icons.ERROR
                )

    # Final summary
    safe_print("\n" + "=" * 80, COLORS["green"])
    safe_print(f"{Icons.SUCCESS} COMPANY COMPARISON PROCESS COMPLETED {Icons.SUCCESS}", COLORS["green"])
    safe_print(f"Total: {len(comparison_tasks)} | Success: {completed_count} | Failed: {failed_count}", COLORS["cyan"])
    safe_print("=" * 80, COLORS["green"])


def process_single_comparison(user_unique_name, client_unique_name, user_final_overview):
    '''
    Process a single comparison between user and client company
    This function runs in a separate thread
    '''
    try:
        safe_print(f' Comparing {user_unique_name} vs {client_unique_name}',)
        # Get client overview data
        client_main_overview = overview_db.get_main_overview(unique_name=client_unique_name)
        client_small_overview = overview_db.get_small_overview(unique_name=client_unique_name)
        client_final_overview = f'{client_main_overview}\n\n\n{client_small_overview}'

        # Perform comparison
        information = user_agent.compare_company(
            user_data=user_final_overview,
            company_data=client_final_overview
        )

        # Save to database
        user_comparable_db.insert_comparison(
            client_unique_name=client_unique_name,
            user_unique_name=user_unique_name,
            json_data=information
        )

        return True
    except Exception as e:
        safe_print(f"Error in comparison {user_unique_name} vs {client_unique_name}: {str(e)}",
                   COLORS["red"] + Icons.ERROR)
        return False





