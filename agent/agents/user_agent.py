from agent.common_agent import common_agent
from agent.agents import user_agent_template




def get_partnership_mail_data(user_company_data, client_company_data):
    input_str = 'Please follow rule'
    information = common_agent.common_agent(template=user_agent_template.generate_b2b_partnership_email(user_company_data=user_company_data,
                                                                                                        client_company_data=client_company_data),
                                            input_str=str(input_str),
                                            json_convert=True)

    return information


def get_follow_up_mail_data(user_company_data, client_company_data, previous_email_data):
    template = user_agent_template.generate_b2b_partnership_followup_email(user_company_data=user_company_data,
                                                                           client_company_data=client_company_data,
                                                                           previous_email_data=previous_email_data)
    input_str = 'Please follow rule'
    information = common_agent.common_agent(template=template,
                                            input_str=str(input_str),
                                            json_convert=True)
    return information


def compare_company(user_data, company_data):
    '''

    :param user_name:
    :param company_data:
    :return:
    '''
    information = common_agent.common_agent(template=user_agent_template.get_b2b_compatibility_assessment_(user_data), input_str=str(company_data),
                                            json_convert=True)
    return information