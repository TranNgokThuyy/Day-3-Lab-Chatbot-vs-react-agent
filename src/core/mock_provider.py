import time
from typing import Dict, Any, Optional
from src.core.llm_provider import LLMProvider


class MockProvider(LLMProvider):
    """
    A deterministic mock provider for demo purposes.
    Behavior:
      - On first call (no 'Observation:' in prompt) it returns an Action to call `search_documents`.
      - If the prompt already contains 'Observation:', it returns a Final Answer summarizing the observation.
    """

    def __init__(self, model_name: str = "mock"):
        super().__init__(model_name=model_name)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start = time.time()
        content = ""

        # If an observation is present, produce a final answer
        if "Observation:" in prompt:
            # Extract the last Observation
            obs_idx = prompt.rfind("Observation:")
            observation = prompt[obs_idx + len("Observation:"):].strip()
            content = f"Final Answer: Based on the observation, here are the most relevant documents:\n{observation}"
        else:
            # Try to get a short query from the user prompt
            user_query = prompt.strip().split('\n')[-1]
            user_query = user_query.replace('\"', '').replace('\'', '')
            content = f"Thought: I should search for documents relevant to the user's query.\nAction: search_documents({user_query})"

        end = time.time()
        return {
            "content": content,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "latency_ms": int((end - start) * 1000),
            "provider": "mock"
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None):
        yield self.generate(prompt, system_prompt=system_prompt)["content"]
