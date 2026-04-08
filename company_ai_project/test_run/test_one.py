from agent.common_agent import common_agent
from agent.agents import company_agent_template, text_util_agent_template, company_agent
from company_ai_project.database.company_database import company_name_link, overview, link, company_information
from company_ai_project.automate.company_automate import add_all_link
import json

company_db = company_name_link.CompanyNameLink()
overview_db = overview.OverviewTable()
link_db = link.LinkTable()
company_info_db = company_information.CompanyInformationTable()
filter_link_db = link.FilterLinkTable()
all_company = company_db.get_all_companies()
get_all_overview = overview_db.get_all_overviews()


def test_one():
    a = 0
    for each in get_all_overview:
        overview = each.get('overview')
        unique_name = each.get('unique_name')
        # print(overview)
        if a == 20:
            print(each)
            instructiion = 'please follow rule'

            short_detail_overview = common_agent.common_agent(
                template=company_agent_template.generate_company_summary_agent(overview),
                input_str=str(instructiion),
                json_convert=True)
            short_detail_overview['company_summary']['unique_name'] = unique_name

            print(json.dumps(short_detail_overview, indent=4))

            break
        a += 1


def get_compransive_data(overview=True, links=True, filter_links=True, company_information=True):
    not_link_data = []
    not_filter_link_data = []
    not_company_information_data = []
    not_overview_list = []
    missing_any_data = []  # New list for unique_names missing any data

    all_company = company_db.get_all_companies()
    print(f'Total number of companies: {len(all_company)}')

    for eachCompany in all_company:
        unique_name = eachCompany.get('unique_name')
        missing = False  # Flag to track if any data is missing

        if overview:
            ove = overview_db.get_overview(unique_name=unique_name)
            if not ove:
                not_overview_list.append(unique_name)
                missing = True
        if links:
            link_data = link_db.get_links_by_unique_name(unique_name)
            if not link_data:
                not_link_data.append(unique_name)
                missing = True

        if filter_links:
            filter_link_data = filter_link_db.get_filter_links_by_unique_name(unique_name)
            if not filter_link_data:
                not_filter_link_data.append(unique_name)
                missing = True

        if links:
            link_data = filter_link_db.get_filter_links_by_unique_name(unique_name)
            if link_data:
                for each_link in link_data:
                    link_data = link_db._get_link_by_unique_name_and_link(unique_name=unique_name,
                                                                          link=each_link.get('link'))
                    if not link_data.get('link_overview'):
                        missing = True
                        break

        if company_information:
            company_information_data = company_info_db.get_company_information(unique_name=unique_name)
            if not company_information_data:
                not_company_information_data.append(unique_name)
                missing = True

        if missing:
            missing_any_data.append(unique_name)

    # Return after the loop completes
    return missing_any_data


def run_all_company_data(all_link=False):
    '''

    :param unique_list:
    :return:
    '''
    missing_any_data = get_compransive_data()
    print(f"Companies missing any data: {len(missing_any_data)}")

    for each in missing_any_data:
        company_data = company_db.get_company(unique_name=each)
        link_data = link_db.get_links_by_unique_name(each)
        if not link_data:
            if company_data:
                add_all_link.process_company(company_data, link_db)

        filter_link_data = filter_link_db.get_filter_links_by_unique_name(each)
        if not filter_link_data and link_data:
            add_all_link.process_filter_company(company_data)

        # FILTER LINK REWRTIE
        filter_link_data = filter_link_db.get_filter_links_by_unique_name(each)
        if filter_link_data:
            # print(filter_link_data)
            pass


run_all_company_data()
