from company_ai_project.automate.company_automate import add_all_link, link_rewrite
from company_ai_project.automate.company_automate import overview as _overview
from company_ai_project.automate.company_automate import company_name_link as auto_company_name_link
from company_ai_project.automate.exibition_automate import exibition_automate
from company_ai_project.database.company_database import company_name_link, link, overview
from company_ai_project.database.exibition_database import exibition_db

company_name_link_db = company_name_link.CompanyNameLink()
_exibition_db = exibition_db.ExhibitorDB()
all_companies = company_name_link_db.get_companies_by_date()

_exibition_automate = False
transfer_from_exibition = False
filter_link_flag = False
_summer_flag = True
add_all_link_flag = True
filter_link_rewrite_flag = False
_overview_flag = False
_each_company_auto = False

if _exibition_automate:
    exibitor_name = 'gulffood'
    exibition_automate.rub_task(exibitor=exibitor_name)

if transfer_from_exibition:
    auto_company_name_link.transfer_from_exibition()

if filter_link_flag:
    add_all_link.add_filter_link(all_companies, max_workers=5)  # Step 2 — AI filter

if _summer_flag:
    _overview.all_summery()

if add_all_link_flag:
    add_all_link.add_all_link(all_companies)  # Step 1 — crawl & collect

if filter_link_rewrite_flag:
    link_rewrite.filter_rewrite()

if _overview_flag:
    _overview.all_overview()

def each_company_auto():
    for eachCompany in all_companies:
        print(eachCompany)
        add_all_link.process_company(eachCompany)
        link_rewrite.link_rewrite(eachCompany)




        break
