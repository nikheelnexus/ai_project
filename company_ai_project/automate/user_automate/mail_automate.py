import json
from threading import Lock, Thread, Semaphore
import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock
import os
import time
from company_ai_project.saved_data import user_data
from common_script import common

from company_ai_project.database.user_database import user, user_comparable, mail
from company_ai_project.database.company_database import company_information, company_name_link, link, overview
from agent.agents import user_agent

user_comparable_db = user_comparable.UserComparableDB()
company_name_link_db = company_name_link.CompanyNameLink()
mail_db = mail.UserEmailDB()
overview_db = overview.OverviewTable()
print_lock = Lock()
partnership_semaphore = Semaphore(3)  # Allow 3 concurrent partnership tasks
followup_semaphore = Semaphore(3)  # Allow 3 concurrent follow-up tasks

from agent.agents import user_agent


def get_all_user_data():
    '''
    Get all user data from database

    :return: list of user data
    '''
    user_db = user.UserDB()
    all_user = user_db.get_all_users()
    return all_user


def process_partnership(user_data, overview_list, user_index, total_users):
    """Process partnership emails for a single user with 3 concurrent limit"""
    with partnership_semaphore:  # Limit concurrent partnership tasks to 3
        try:
            safe_print(
                f"[Partnership] Starting processing for user {user_index + 1}/{total_users}: {user_data.get('website', 'Unknown')}",
                COLORS["cyan"], Icons.SEARCH)

            website = user_data['website']
            user_company_data = company_name_link_db.search_companies(website)

            if not user_company_data:
                safe_print(f"[Partnership] No company data found for {website}", COLORS["yellow"], Icons.WARNING)
                return

            user_company_data = user_company_data[0]
            user_unique_name = user_company_data['unique_name']

            user_main_overview = overview_db.get_main_overview(unique_name=user_unique_name)
            user_small_overview = overview_db.get_small_overview(unique_name=user_unique_name)
            user_final_overview = f'{user_main_overview}\n\n\n{user_small_overview}'

            emails_generated = 0

            for eachOverview in overview_list:
                client_unique_name = eachOverview['unique_name']

                # Skip if same company
                if client_unique_name == user_unique_name:
                    continue

                mail_data = mail_db.get_emails_by_user_and_client(
                    user_unique_name=user_unique_name,
                    client_unique_name=client_unique_name
                )
                if mail_data:
                    continue

                client_main_overview = overview_db.get_main_overview(unique_name=client_unique_name)
                client_small_overview = overview_db.get_small_overview(unique_name=client_unique_name)
                client_final_overview = f'{client_main_overview}\n\n\n{client_small_overview}'

                try:
                    partnership_mail = user_agent.get_partnership_mail_data(
                        user_company_data=user_final_overview,
                        client_company_data=client_final_overview
                    )

                    json_data = {}
                    json_data['email_type'] = 'partnership_mail'
                    json_data['subject'] = partnership_mail['email_content']['subject']
                    json_data['body'] = partnership_mail['email_content']['body'] + '\n\n' + \
                                        partnership_mail['email_content']['signature']
                    json_data['client_email'] = ''

                    mail_db.insert_email(
                        user_unique_name=user_unique_name,
                        client_unique_name=client_unique_name,
                        email_type=json_data.get('email_type'),
                        json_data=json_data
                    )

                    emails_generated += 1
                    safe_print(
                        f"[Partnership] Generated email #{emails_generated} for {user_unique_name} -> {client_unique_name}",
                        COLORS["green"], Icons.EMAIL)

                except Exception as e:
                    safe_print(
                        f"[Partnership] Error generating email for {user_unique_name} -> {client_unique_name}: {str(e)}",
                        COLORS["red"], Icons.ERROR)

            safe_print(f"[Partnership] Completed {user_unique_name}: Generated {emails_generated} emails",
                       COLORS["green"], Icons.SUCCESS)

        except Exception as e:
            safe_print(f"[Partnership] Error processing user {user_data.get('website', 'Unknown')}: {str(e)}",
                       COLORS["red"], Icons.ERROR)


def process_followup(user_data, overview_list, user_index, total_users):
    """Process follow-up emails for a single user with 3 concurrent limit"""
    with followup_semaphore:  # Limit concurrent follow-up tasks to 3
        try:
            safe_print(
                f"[Follow-up] Starting processing for user {user_index + 1}/{total_users}: {user_data.get('website', 'Unknown')}",
                COLORS["magenta"], Icons.UPDATE)

            website = user_data['website']
            user_company_data = company_name_link_db.search_companies(website)

            if not user_company_data:
                safe_print(f"[Follow-up] No company data found for {website}", COLORS["yellow"], Icons.WARNING)
                return

            user_company_data = user_company_data[0]
            user_unique_name = user_company_data['unique_name']

            user_main_overview = overview_db.get_main_overview(unique_name=user_unique_name)
            user_small_overview = overview_db.get_small_overview(unique_name=user_unique_name)
            user_final_overview = f'{user_main_overview}\n\n\n{user_small_overview}'

            followups_generated = 0

            for eachOverview in overview_list:
                client_unique_name = eachOverview['unique_name']

                # Skip if same company
                if client_unique_name == user_unique_name:
                    continue

                client_main_overview = overview_db.get_main_overview(unique_name=client_unique_name)
                client_small_overview = overview_db.get_small_overview(unique_name=client_unique_name)
                client_final_overview = f'{client_main_overview}\n\n\n{client_small_overview}'

                try:
                    # Get existing emails for this pair
                    mail_data = mail_db.get_emails_by_user_and_client(
                        user_unique_name=user_unique_name,
                        client_unique_name=client_unique_name
                    )

                    if mail_data:
                        follow_up_mail = user_agent.get_follow_up_mail_data(
                            user_company_data=user_final_overview,
                            client_company_data=client_final_overview,
                            previous_email_data=str(mail_data)
                        )

                        json_data = {}
                        json_data['email_type'] = f'Follow_up_{follow_up_mail["Follow_up"]}'
                        json_data['subject'] = follow_up_mail['email_content']['subject']
                        json_data['body'] = follow_up_mail['email_content']['body'] + '\n\n' + \
                                            follow_up_mail['email_content']['signature']
                        json_data['client_email'] = ''

                        mail_db.insert_email(
                            user_unique_name=user_unique_name,
                            client_unique_name=client_unique_name,
                            email_type=json_data.get('email_type'),
                            json_data=json_data
                        )

                        followups_generated += 1
                        safe_print(
                            f"[Follow-up] Generated follow-up #{followups_generated} for {user_unique_name} -> {client_unique_name}",
                            COLORS["blue"], Icons.EMAIL)
                    else:
                        safe_print(
                            f"[Follow-up] No previous email found for {user_unique_name} -> {client_unique_name}, skipping",
                            COLORS["gray"], Icons.INFO)

                except Exception as e:
                    safe_print(
                        f"[Follow-up] Error generating follow-up for {user_unique_name} -> {client_unique_name}: {str(e)}",
                        COLORS["red"], Icons.ERROR)

            safe_print(f"[Follow-up] Completed {user_unique_name}: Generated {followups_generated} follow-up emails",
                       COLORS["green"], Icons.SUCCESS)

        except Exception as e:
            safe_print(f"[Follow-up] Error processing user {user_data.get('website', 'Unknown')}: {str(e)}",
                       COLORS["red"], Icons.ERROR)


def safe_print(message, color_code="", icon=""):
    """Thread-safe printing with timestamp and icon"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with print_lock:
        if icon:
            message = f"{icon} {message}"
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
    EMAIL = '📧'
    SEARCH = '🔍'
    TRASH = '🗑️'
    UPDATE = '📝'
    JSON = '📄'
    STATS = '📊'
    TYPE = '🏷️'


def run_partnership_emails():
    """Run partnership email generation with 3 concurrent tasks"""
    safe_print("=" * 60, "", "")
    safe_print("Starting PARTNERSHIP email generation with 3 concurrent tasks",
               COLORS["magenta"], Icons.INFO)
    safe_print("=" * 60, "", "")

    all_user = get_all_user_data()
    overview_list = overview_db.get_all_overviews()

    safe_print(f"Loaded {len(all_user)} users and {len(overview_list)} overviews for partnership emails",
               COLORS["blue"], Icons.DATABASE)

    # Create and start threads for partnership emails
    threads = []
    for i, eachUser in enumerate(all_user):
        thread = Thread(target=process_partnership, args=(eachUser, overview_list, i, len(all_user)))
        thread.start()
        threads.append(thread)

        # Small delay to avoid overwhelming the system
        time.sleep(0.05)

    # Wait for all partnership threads to complete
    for thread in threads:
        thread.join()

    safe_print("All PARTNERSHIP emails have been generated successfully!",
               COLORS["green"], Icons.SUCCESS)
    safe_print("=" * 60, "", "")


def run_followup_emails():
    """Run follow-up email generation with 3 concurrent tasks"""
    safe_print("=" * 60, "", "")
    safe_print("Starting FOLLOW-UP email generation with 3 concurrent tasks",
               COLORS["magenta"], Icons.INFO)
    safe_print("=" * 60, "", "")

    all_user = get_all_user_data()
    overview_list = overview_db.get_all_overviews()

    safe_print(f"Loaded {len(all_user)} users and {len(overview_list)} overviews for follow-up emails",
               COLORS["blue"], Icons.DATABASE)

    # Create and start threads for follow-up emails
    threads = []
    for i, eachUser in enumerate(all_user):
        thread = Thread(target=process_followup, args=(eachUser, overview_list, i, len(all_user)))
        thread.start()
        threads.append(thread)

        # Small delay to avoid overwhelming the system
        time.sleep(0.05)

    # Wait for all follow-up threads to complete
    for thread in threads:
        thread.join()

    safe_print("All FOLLOW-UP emails have been generated successfully!",
               COLORS["green"], Icons.SUCCESS)
    safe_print("=" * 60, "", "")


def run_all_emails_sequential():
    """Run both partnership and follow-up emails sequentially"""
    safe_print("Starting COMPLETE email generation process", COLORS["cyan"], Icons.STATS)

    # Run partnership emails first
    run_partnership_emails()

    # Then run follow-up emails
    run_followup_emails()

    safe_print("COMPLETE email generation process finished!", COLORS["green"], Icons.SUCCESS)


def run_all_emails_parallel():
    """Run both partnership and follow-up emails in parallel (each with 3 concurrent tasks)"""
    safe_print("Starting PARALLEL email generation (Partnership + Follow-up simultaneously)",
               COLORS["cyan"], Icons.STATS)
    safe_print("Note: Each process runs with 3 concurrent tasks independently",
               COLORS["yellow"], Icons.INFO)

    # Create threads for both processes to run simultaneously
    partnership_thread = Thread(target=run_partnership_emails)
    followup_thread = Thread(target=run_followup_emails)

    # Start both
    partnership_thread.start()
    followup_thread.start()

    # Wait for both to complete
    partnership_thread.join()
    followup_thread.join()

    safe_print("BOTH Partnership and Follow-up processes completed!",
               COLORS["green"], Icons.SUCCESS)


# Main execution - choose which function to run
if __name__ == "__main__":
    # Option 1: Run partnership emails only
    # run_partnership_emails()

    # Option 2: Run follow-up emails only
    # run_followup_emails()

    # Option 3: Run sequentially (partnership first, then follow-up)
    #run_all_emails_sequential()

    # Option 4: Run both in parallel (each with 3 concurrent tasks)
    # run_all_emails_parallel()
    pass