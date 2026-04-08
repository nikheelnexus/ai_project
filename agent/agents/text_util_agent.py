from agent.agents import text_util_agent_template
from agent.common_agent import common_agent
from common_script import common
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor


def rewrite_text(text, combine_analyzer=False, max_workers=15):
    template = text_util_agent_template.rewrite()
    template = text_util_agent_template.rewrite__()

    information = ''

    # Try full text first
    try:
        information = common_agent.common_agent(template=template, input_str=text, json_convert=False)
    except Exception as e:
        print(f"❌ Failed to get get_ultra_detailed_analyzer: {e}")
    if information:
        return information

    print('\nWE ARE SPLITTING THE TEXT TO RUN THE DETAILED ANALYZER TEXT')
    split_texts = common.split_text_by_words(text, words_per_chunk=20000)
    print('Number of text chunks:', len(split_texts))

    def process_chunk(chunk_text):
        """Process a single text chunk"""
        try:
            print('Processing text chunk length:', len(chunk_text))
            return common_agent.common_agent(template=template, input_str=chunk_text, json_convert=False)
        except Exception as e:
            print(f"❌ Error processing chunk: {e}")
            return None

    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and process as they complete
        future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in split_texts}

        _information = ''
        for future in concurrent.futures.as_completed(future_to_chunk):
            result = future.result()
            if result:
                _information += '\n' + result

    if combine_analyzer:
        # Re-analyze the combined rewritten result
        print('Running final combine analysis...')
        return common_agent.common_agent(template=template, input_str=_information, json_convert=False)

    return _information


def get_ultra_detailed_analyzer(text, combine_analyzer=False, max_workers=15):
    template = text_util_agent_template.ultra_flexible_link_analyzer_instruction()

    information = ''

    # Try full text first
    try:
        information = common_agent.common_agent(template=template, input_str=text, json_convert=False)
    except Exception as e:
        print(f"❌ Failed to get get_ultra_detailed_analyzer: {e}")
    if information:
        return information

    print('\nWE ARE SPLITTING THE TEXT TO RUN THE DETAILED ANALYZER TEXT')
    split_texts = common.split_text_by_words(text, words_per_chunk=20000)
    print('Number of text chunks:', len(split_texts))

    def process_chunk(chunk_text):
        """Process a single text chunk"""
        try:
            print('Processing text chunk length:', len(chunk_text))
            return common_agent.common_agent(template=template, input_str=chunk_text, json_convert=False)
        except Exception as e:
            print(f"❌ Error processing chunk: {e}")
            return None

    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and process as they complete
        future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in split_texts}

        _information = ''
        for future in concurrent.futures.as_completed(future_to_chunk):
            result = future.result()
            if result:
                _information += '\n' + result

    if combine_analyzer:
        # Re-analyze the combined rewritten result
        print('Running final combine analysis...')
        return common_agent.common_agent(template=template, input_str=_information, json_convert=False)

    return _information
