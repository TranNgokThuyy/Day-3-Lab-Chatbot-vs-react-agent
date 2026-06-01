import os
import sys
from typing import Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ChatbotBaseline:
    """
    A minimal chatbot baseline for comparison against the ReAct Agent.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def get_system_prompt(self) -> str:
        return (
            "You are a helpful assistant. Answer the user's question directly "
            "without calling tools. If the information is not available, say so clearly."
        )

    def run(self, user_input: str) -> str:
        logger.log_event("CHATBOT_START", {"input": user_input, "model": self.llm.model_name})
        response = self.llm.generate(user_input, system_prompt=self.get_system_prompt())
        content = response.get("content", "").strip()
        tracker.track_request(response.get("provider", "unknown"), self.llm.model_name, response.get("usage", {}), response.get("latency_ms", 0))
        logger.log_event("CHATBOT_RESPONSE", {"content": content})
        logger.log_event("CHATBOT_END", {})
        return content
