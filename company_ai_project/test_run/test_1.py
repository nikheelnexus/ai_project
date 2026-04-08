from company_ai_project.automate.company_automate import add_all_link, link_rewrite
from company_ai_project.automate.company_automate import overview as _overview
from company_ai_project.automate.company_automate import company_name_link as auto_company_name_link
from company_ai_project.automate.company_automate import overview as auto_overview
from company_ai_project.automate.exibition_automate import exibition_automate
from company_ai_project.database.company_database import company_name_link, link, overview
from company_ai_project.database.exibition_database import exibition_db
from common_script import website_script, common
from agent.agents import company_agent_template, text_util_agent, company_agent

import json
from datetime import datetime
import os
from multiprocessing import Pool, cpu_count
from functools import partial
import time


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

print(f"Total Link: {len(all_link_list)}")
print(f"Total Filter Link: {len(filter_link_list)}")
list_item = []
sorted_list = sorted(get_link_unique_name)
for each in sorted_list:
    filter = filter_link_db.get_filter_links_by_unique_name(unique_name=each)
    if not filter:
        get_links = link_db.get_links_by_unique_name(unique_name=each)
        company = company_name_link_db.get_company(unique_name=each)
        if get_links:
            if company:
                website = company.get('website')
                unique_name = company.get('unique_name')
                #value = add_all_link.process_company(company, replace=True)
                #print('this is value:', value)
                list_item.append(company)

                #if value:
                #    break

print(len(list_item))
unique_url_list = ['pasta-armando-pastarmando.it']
for company in list_item:
    website = company.get('website')
    unique_name = company.get('unique_name')
    if unique_name not in unique_url_list:
        print(company)
        value = add_all_link.process_company(company, replace=True)
