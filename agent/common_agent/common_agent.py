from agent.common_agent import ai_agent_utils

import json, re
import threading
import json
# Add a lock for thread safety
json_lock = threading.Lock()
def clean_control_chars(s):
    # Removes ASCII control characters (0–31 except \t \n \r) which are invalid in JSON
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', s)


def extract_json_from_text(text: str):
    """Extract JSON from text that might contain other content"""
    # Try to find JSON code blocks first
    json_blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_blocks:
        return json_blocks[0].strip()

    # Try to find any code blocks
    code_blocks = re.findall(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if code_blocks:
        return code_blocks[0].strip()

    # Try to find JSON object directly
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        return json_match.group(0).strip()

    return None


def common_agent(template, input_str, openai=False, json_convert=True):
    try:
        content = ai_agent_utils.combine(input_str, template, openai=openai)

        if json_convert:
            val = ''
            if content:
                if 'json' in content:
                    val = 'json'
                elif 'python' in content:
                    val = 'python'

                # Clean and sanitize
                clean_json_string = content.replace(f'```{val}', '').replace('```', '').strip()
                clean_json_string = clean_control_chars(clean_json_string)

                return json.loads(clean_json_string)
            else:
                print("⚠️ Empty content returned.")
                #SHOULD BR BREAK
                RuntimeError("Empty content returned from AI agent.")
                return None
        else:
            return content

    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print("🔎 Raw content was:", content)
        return None

    except Exception as e:
        print(f"❌ Unexpected error in `common_agent`: {e}")
        return None


def ai_image(image_path, prompt):
    content = ai_agent_utils.open_ai_image(image_path, prompt)
    if content is None:
        print("❌ No content returned from AI image generation.")
        return None
    content = content['choices'][0]['message']['content']

    return content
