from agent.common_agent import common_agent
from common_script import common, combine_json
import concurrent.futures
from agent.common_agent import google_search
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from agent.agents import company_agent_template, text_util_agent_template

combine_json_class = combine_json.UniversalJSONCombiner()


def get_company_name_website(text):
    information = common_agent.common_agent(template=company_agent_template.get_exhibitor_data(),
                                            input_str=str(text),
                                            json_convert=True)
    return information

def get_company_information(overview):
    information = common_agent.common_agent(template=company_agent_template.get_company_information_data(),
                                            input_str=str(overview),
                                            json_convert=True)
    if not information:
        return {}
    certifications = information.get('certifications', [])

    certification_normalize = get_certification_filter(certifications)
    normalized_certifications = certification_normalize.get('normalized_certifications', [])
    information['certifications'] = normalized_certifications
    return information


def get_company_overview(text):
    information = common_agent.common_agent(template=company_agent_template._company_overview_formatter_instruction(),
                                            input_str=str(text),
                                            json_convert=True)
    return information


def get_company_small_overview(text):
    information = common_agent.common_agent(template=company_agent_template.company_small_overview(),
                                            input_str=str(text),
                                            json_convert=False)
    return information


def get_product_and_service(text, combine_analyzer=False, json_convert=True, max_workers=15):
    template = company_agent_template.get_product_and_service_data()
    information = ''

    # Try full text first
    try:
        information = common_agent.common_agent(template=template, input_str=text, json_convert=json_convert)
    except Exception as e:
        print(f"❌ Failed to get get_ultra_detailed_analyzer: {e}")
    if information:
        return information

    print('\nWE ARE SPLITTING THE TEXT TO RUN THE DETAILED ANALYZER TEXT')
    split_texts = common.split_text_by_words(text, words_per_chunk=100)
    print('this is split: ', len(split_texts))

    def process_chunk(chunk_text):
        """Process a single text chunk"""
        try:
            print('Each text length:', len(chunk_text))
            return common_agent.common_agent(template=template, input_str=chunk_text, json_convert=json_convert)
        except Exception as e:
            print(f"❌ Error processing chunk: {e}")
            return None

    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in split_texts}

        # Collect results as they complete
        if not json_convert:
            _information = ''
            for future in concurrent.futures.as_completed(future_to_chunk):
                result = future.result()
                if result:
                    _information += '\n' + result
        else:
            _information = []
            for future in concurrent.futures.as_completed(future_to_chunk):
                result = future.result()
                if result:
                    _information.append(result)

    if json_convert:
        _information = combine_json_class.combine_json_data(_information)

    if combine_analyzer:
        # Re-analyze the combined rewritten result
        print('Running final combine analysis... ')
        return common_agent.common_agent(template=template, input_str=_information, json_convert=json_convert)

    return _information


def get_exibitor_list(text):
    information = common_agent.common_agent(template=company_agent_template.get_exhibitor_data(),
                                            input_str=str(text),
                                            json_convert=True)
    return information


def get_link_segregator(company_name, link_list):
    text = {
        "company_name": company_name,
        "link_list": link_list
    }
    information = common_agent.common_agent(template=company_agent_template.get_website_segregator(),
                                            input_str=str(text),
                                            json_convert=True)
    return information


def find_best_website(company_name, link_list):
    text = {
        "company_name": company_name,
        "link_list": link_list
    }
    information = common_agent.common_agent(template=company_agent_template.get_best_website(),
                                            input_str=str(text),
                                            json_convert=True)
    return information


def get_best_title(company_name, overview):
    text = {
        "company_name": company_name,
        "overview": overview
    }
    information = common_agent.common_agent(template=company_agent_template.get_best_title(),
                                            input_str=str(text),
                                            json_convert=True)
    return information


def get_best_website(search_query):
    # Single search example
    # search_query = "41. Gourmet Nut"

    # Perform the search
    results = google_search.google_search_single(search_query)

    # Print results
    # print_search_results(results)
    organic_results = results["parsed_results"].get("organic_results", [])

    if organic_results:
        link_list = [res["url"] for res in organic_results if "url" in res]
        link_list = list(set(link_list))  # Remove duplicates
        # Get segregated links
        link_list = get_link_segregator(company_name=search_query, link_list=link_list)

        link_list = find_best_website(
            company_name=search_query,
            link_list=link_list,
        )
        return link_list

    return []


def get_company_profile(company_overview):
    text = 'Please follow Rule'
    information = common_agent.common_agent(
        template=company_agent_template.get_company_profile_template(client_company_overview=company_overview),
        input_str=str(text),
        json_convert=True)
    return information


def get_certification_filter(new_certifications):
    certification_ai = common_agent.common_agent(
        template=company_agent_template.get_certification_normalizer(),
        input_str=str(new_certifications),
        json_convert=True
    )
    return certification_ai


def get_certification_information(eachCertification):
    certification_information = common_agent.common_agent(
        template=text_util_agent_template.explain_certification_json(),
        input_str=str(eachCertification),
        json_convert=True
    )
    return certification_information


def get_filter_link(link_list, maximum=10):
    link_list = common_agent.common_agent(template=company_agent_template.filter_company_urls(maximum=maximum),
                                          input_str=str(link_list),
                                          json_convert=True)
    if not link_list:
        return []
    return link_list


def get_company_summery(overview):
    company_summery = common_agent.common_agent(
        template=company_agent_template.generate_company_summary_agent(company_data=overview),
        input_str=str(''),
        json_convert=False
    )
    return company_summery
