
from company_ai_project.database.user_database import user
from company_ai_project.database.company_database import company_information, company_name_link, link
from company_ai_project.automate.user_automate import user_comparable_automate, mail_automate
company_name_link_db = company_name_link.CompanyNameLink()



def get_all_user_data():
    '''
    Get all user data from database

    :return: list of user data
    '''
    user_db = user.UserDB()
    all_user = user_db.get_all_users()

    return all_user


user_compare = True
email_automate = False

if user_compare:
    user_comparable_automate.compare_company()

if email_automate:
    mail_automate.run_all_emails_sequential()





