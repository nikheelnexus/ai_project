from company_ai_project.automate.company_automate import add_all_link, link_rewrite
from company_ai_project.automate.company_automate import overview as _overview
from company_ai_project.automate.company_automate import company_name_link as auto_company_name_link
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


output_file = 'failed_companies_links_1.json'
current_run_time = datetime.now().isoformat()
__exibition_db = exibition_db.ExhibitorDB()
company_name_link_db = company_name_link.CompanyNameLink()
link_db = link.LinkTable()
filter_link_db = link.FilterLinkTable()
overview_db = overview.OverviewTable()

# Load existing data
if os.path.exists(output_file):
    with open(output_file, 'r', encoding='utf-8') as f:
        all_failed = json.load(f)
    print(f"📂 Loaded {len(all_failed)} existing failed records")
else:
    all_failed = {}
    print(f"📂 No existing failed records found")

for each in all_failed:
  dic_val = all_failed[each]
  unique_name = dic_val['unique_name']
  website = dic_val['website']
  company = company_name_link_db.get_company(unique_name=unique_name)
  get_all_link = website_script.get_all_link(website)
  if not get_all_link:
      print(company)
      all_link = link_db.get_links_by_unique_name(unique_name=unique_name)
      filter_link = filter_link_db.get_filter_links_by_unique_name(unique_name=unique_name)
      ovevire = overview_db.get_overview(unique_name=unique_name)

      if all_link:
          for each_link in all_link:
              print(each_link)
    if filter_link:
            pass


      print(all_link)
      print(filter_link)
      print(ovevire)
      '''
      company_name_link_db.delete_company(unique_name)
      
      __exibition_db.insert_exhibitor(company_name=company.get('company_name'),
                                      company_website='',
                                      replace=True)
                                      '''
      break







