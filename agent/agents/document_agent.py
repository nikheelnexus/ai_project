from agent.common_agent import common_agent
from agent.agents import document_agent_template




def get_image_overview(image_path):
    information = common_agent.ai_image(prompt=document_agent_template.image_overview_ai_instruction(),
                                            image_path=str(image_path))
    return information