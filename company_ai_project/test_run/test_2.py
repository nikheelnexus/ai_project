from company_ai_project.automate.company_automate import add_all_link, link_rewrite
from company_ai_project.automate.company_automate import overview as _overview
from company_ai_project.automate.company_automate import company_name_link as auto_company_name_link
from company_ai_project.automate.company_automate import overview as auto_overview
from company_ai_project.automate.exibition_automate import exibition_automate
from company_ai_project.database.company_database import company_name_link, link, overview
from company_ai_project.database.exibition_database import exibition_db
from common_script import website_script, common
from agent.agents import company_agent_template, text_util_agent, company_agent
from company_ai_project.database.user_database import user_comparable
from company_ai_project.database.user_database import user

import json
from datetime import datetime
import os
from multiprocessing import Pool, cpu_count
from functools import partial
import time
first_name='Nikheel'
last_name='Patel'

def get_user_data():
    '''

    :return:
    '''
    user_db = user.UserDB()
    user_name = f"{first_name} {last_name}"
    user_data = user_db.search_users(user_name)
    return user_data

output_file = 'failed_companies_links_2.json'
current_run_time = datetime.now().isoformat()
__exibition_db = exibition_db.ExhibitorDB()
company_name_link_db = company_name_link.CompanyNameLink()
link_db = link.LinkTable()
filter_link_db = link.FilterLinkTable()
overview_db = overview.OverviewTable()
summery_db = overview.SummaryTable()

all_summery  = summery_db.get_all_summaries()
all_overview = overview_db.get_all_overviews()

get_link_unique_name = link_db.get_unique_names()
all_link_list = list(set(link_db.get_unique_names()))
filter_link_list = list(set(filter_link_db.get_unique_names()))
overview_link_list = list(set(overview_db.get_unique_names()))
summery_link_list = list(set(summery_db.get_unique_names()))

comparable_db = user_comparable.UserComparableDB()
user_data = get_user_data()
print(user_data)
user_data = user_data[0]
website = user_data['website']
company_name = company_name_link_db.search_companies(website)[0]
comparable_companies = comparable_db.get_user_comparisons(user_unique_name=company_name.get('unique_name'))

print(comparable_companies)
