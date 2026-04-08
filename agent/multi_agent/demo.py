import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer, util
import json
from typing import Dict, List, Any
import numpy as np


class AIAgent:
    """Base class for all AI agents"""

    def __init__(self, name: str, expertise: str, model_name: str = "microsoft/DialoGPT-medium"):
        self.name = name
        self.expertise = expertise
        self.model_name = model_name
        self.conversation_history = []

        # Initialize the model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

    def process_query(self, query: str, context: str = "") -> str:
        """Process a query and return response"""
        prompt = f"Expert in {self.expertise}. Context: {context}\nQuery: {query}\nResponse:"

        inputs = self.tokenizer.encode(prompt + self.tokenizer.eos_token, return_tensors='pt')

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=150,
                num_return_sequences=1,
                pad_token_id=self.tokenizer.eos_token_id,
                temperature=0.7,
                do_sample=True
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the response part
        response = response.split("Response:")[-1].strip()

        self.conversation_history.append({
            'query': query,
            'response': response,
            'context': context
        })

        return response

    def get_expertise_description(self) -> str:
        return f"{self.name}: {self.expertise}"


class CoordinatorAgent:
    """Main agent that coordinates between specialized agents"""

    def __init__(self):
        self.agents = {}
        self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.initialize_agents()

    def initialize_agents(self):
        """Initialize all specialized agents"""
        agents_config = [
            {"name": "research_agent", "expertise": "research and data analysis"},
            {"name": "coding_agent", "expertise": "software development and programming"},
            {"name": "writing_agent", "expertise": "content writing and editing"},
            {"name": "analysis_agent", "expertise": "data analysis and insights"},
            {"name": "planning_agent", "expertise": "project planning and strategy"}
        ]

        for config in agents_config:
            self.agents[config["name"]] = AIAgent(
                name=config["name"],
                expertise=config["expertise"]
            )

    def find_best_agent(self, query: str) -> str:
        """Find the most suitable agent for a given query using semantic similarity"""
        query_embedding = self.similarity_model.encode(query, convert_to_tensor=True)

        best_agent = None
        best_similarity = -1

        for agent_name, agent in self.agents.items():
            expertise_desc = agent.get_expertise_description()
            expertise_embedding = self.similarity_model.encode(expertise_desc, convert_to_tensor=True)

            similarity = util.pytorch_cos_sim(query_embedding, expertise_embedding).item()

            if similarity > best_similarity:
                best_similarity = similarity
                best_agent = agent_name

        return best_agent, best_similarity

    def process_complex_task(self, task: str) -> Dict[str, Any]:
        """Process a complex task by delegating to multiple agents"""
        print(f"Coordinator: Processing complex task: {task}")

        # Step 1: Planning phase
        planning_prompt = f"Break down this task into subtasks: {task}"
        plan = self.agents["planning_agent"].process_query(planning_prompt)
        print(f"Planning Agent: {plan}")

        # Step 2: Research phase (if needed)
        research_keywords = ["research", "analyze", "study", "investigate"]
        if any(keyword in task.lower() for keyword in research_keywords):
            research_result = self.agents["research_agent"].process_query(
                task,
                f"Task: {task}. Plan: {plan}"
            )
            print(f"Research Agent: {research_result}")
        else:
            research_result = "No research needed"

        # Step 3: Determine main processing agent
        main_agent_name, confidence = self.find_best_agent(task)
        main_agent = self.agents[main_agent_name]

        # Step 4: Execute main task
        context = f"Overall plan: {plan}. Research: {research_result}"
        main_result = main_agent.process_query(task, context)
        print(f"{main_agent_name.title()} Agent: {main_result}")

        # Step 5: Writing/formatting phase
        writing_prompt = f"Format and present this information clearly: {main_result}"
        final_output = self.agents["writing_agent"].process_query(writing_prompt, main_result)

        return {
            "task": task,
            "plan": plan,
            "research": research_result,
            "main_agent": main_agent_name,
            "confidence": confidence,
            "main_result": main_result,
            "final_output": final_output,
            "agents_used": ["planning_agent", "research_agent", main_agent_name, "writing_agent"]
        }


class MultiAgentWorkflow:
    """Advanced workflow with sequential agent processing"""

    def __init__(self, coordinator: CoordinatorAgent):
        self.coordinator = coordinator
        self.workflow_history = []

    def execute_workflow(self, initial_task: str) -> Dict[str, Any]:
        """Execute a complete workflow with multiple agents"""
        print("=" * 60)
        print("STARTING MULTI-AGENT WORKFLOW")
        print("=" * 60)

        # Phase 1: Analysis and Planning
        print("\n📋 Phase 1: Analysis and Planning")
        analysis_result = self.coordinator.agents["analysis_agent"].process_query(
            f"Analyze this task and identify key components: {initial_task}"
        )
        print(f"Analysis Result: {analysis_result}")

        # Phase 2: Research and Information Gathering
        print("\n🔍 Phase 2: Research and Information Gathering")
        research_result = self.coordinator.agents["research_agent"].process_query(
            f"Research aspects of: {initial_task}",
            analysis_result
        )
        print(f"Research Result: {research_result}")

        # Phase 3: Main Processing
        print("\n⚡ Phase 3: Main Processing")
        main_agent_name, confidence = self.coordinator.find_best_agent(initial_task)
        main_agent = self.coordinator.agents[main_agent_name]

        main_context = f"Analysis: {analysis_result}. Research: {research_result}"
        main_result = main_agent.process_query(initial_task, main_context)
        print(f"Main Result from {main_agent_name}: {main_result}")

        # Phase 4: Refinement and Writing
        print("\n✍️ Phase 4: Refinement and Writing")
        final_result = self.coordinator.agents["writing_agent"].process_query(
            f"Create a comprehensive final output based on: {main_result}",
            f"Analysis: {analysis_result}. Research: {research_result}"
        )

        workflow_result = {
            "initial_task": initial_task,
            "phases": {
                "analysis": analysis_result,
                "research": research_result,
                "main_processing": {
                    "agent": main_agent_name,
                    "confidence": confidence,
                    "result": main_result
                },
                "final_output": final_result
            },
            "agents_involved": ["analysis_agent", "research_agent", main_agent_name, "writing_agent"]
        }

        self.workflow_history.append(workflow_result)

        print("\n" + "=" * 60)
        print("WORKFLOW COMPLETED")
        print("=" * 60)

        return workflow_result


# Example usage and demonstration
def main():
    # Initialize the coordinator
    coordinator = CoordinatorAgent()
    workflow = MultiAgentWorkflow(coordinator)

    # Test tasks
    test_tasks = [
        "Create a Python script for data analysis with visualization",
        "Research and write about the impact of AI on healthcare",
        "Develop a project plan for building a chatbot system",
        "Analyze market trends for electric vehicles and create a report"
    ]

    print("🤖 AI Multi-Agent System Demo")
    print("This system demonstrates how one AI agent can suggest and coordinate with other agents.")

    for i, task in enumerate(test_tasks, 1):
        print(f"\n{'#' * 50}")
        print(f"TASK {i}: {task}")
        print(f"{'#' * 50}")

        # Simple delegation example
        best_agent, confidence = coordinator.find_best_agent(task)
        print(f"Coordinator: I suggest using {best_agent} for this task (confidence: {confidence:.2f})")

        # Complex workflow example
        result = workflow.execute_workflow(task)

        print(f"\n📊 Final Output:")
        print(f"{result['phases']['final_output']}")

        print(f"\n🔧 Agents used in this workflow: {', '.join(result['agents_involved'])}")


if __name__ == "__main__":
    main()