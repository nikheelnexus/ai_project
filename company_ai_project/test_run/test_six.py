from company_ai_project.database.exibition_database import exibition_db
from agent.agents import company_agent
import json
from common_script import website_script, common


old_exibitor_db = exibition_db._ExhibitorDB()
new_exibitor_db = exibition_db.ExhibitorDB()
all_exibition = old_exibitor_db.get_all_exhibitors()
for each_exibit in all_exibition:
    print(each_exibit)
    exhibitor_name = each_exibit.get('exhibitor_name')
    company_name = each_exibit.get('company_name')
    company_website = each_exibit.get('company_website')
    company_data = each_exibit.get('company_data')

    new_exibitor_db.insert_exhibitor(exhibitor_name=exhibitor_name,
                                     company_name=company_name,
                                     company_website=company_website,
                                     company_data=company_data)




