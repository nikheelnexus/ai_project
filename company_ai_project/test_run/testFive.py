from company_ai_project_old.database_old import certification_database
import json
from agent.agents import company_agent
from agent.common_agent import common_agent
from agent.agents import company_agent_template, text_util_agent_template
from company_ai_project.database.certification_database import certification_db


_certification_db = certification_db.CertificationDB()



certification_database_db = certification_database.CertificationDB()
all_certification = certification_database_db.get_all_certifications()
for each in all_certification:
    print(each)
    certification_name = each['certification_name']
    certification_ai = common_agent.common_agent(
        template=company_agent_template.explain_certification_markdown(),
        input_str=str(certification_name),
        json_convert=False
    )
    print(certification_ai)
    _certification_db.insert_certification(certification_name=certification_name,
                                           certification_data=certification_ai)

    break