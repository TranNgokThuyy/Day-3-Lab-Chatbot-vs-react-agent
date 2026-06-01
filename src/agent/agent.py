import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5, max_retries: int = 1):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.history: List[Dict[str, Any]] = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
You are an intelligent assistant. You have access to the following tools:
{tool_descriptions}

Follow this format exactly:
Thought: your reasoning about the user question.
Action: tool_name(arguments)
Observation: result of the tool call.
... (repeat Thought/Action/Observation as needed)
Final Answer: your final response to the user.
"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        prompt_history = user_input
        steps = 0
        retry_counts = 0
        final_answer: Optional[str] = None

        while steps < self.max_steps:
            response = self.llm.generate(prompt_history, system_prompt=self.get_system_prompt())
            content = response.get("content", "").strip()
            tracker.track_request(response.get("provider", "unknown"), self.llm.model_name, response.get("usage", {}), response.get("latency_ms", 0))
            logger.log_event("LLM_RESPONSE", {"step": steps, "content": content})

            thought = self._extract_thought(content)
            if thought:
                logger.log_event("THOUGHT", {"step": steps, "thought": thought})

            final_answer = self._extract_final_answer(content)
            if final_answer:
                logger.log_event("FINAL_ANSWER", {"answer": final_answer})
                break

            action = self._extract_action(content)
            if not action:
                if retry_counts < self.max_retries:
                    retry_counts += 1
                    logger.log_event("RETRY", {"reason": "No action parsed", "retry": retry_counts})
                    prompt_history += "\nObservation: I did not understand the action. Please answer with a valid tool call or final answer."
                    continue
                logger.log_event("PARSE_FAILURE", {"content": content})
                final_answer = "I couldn't determine a tool action. Please ask a more specific question."
                break

            tool_name, args = action
            logger.log_event("TOOL_CALL", {"tool": tool_name, "args": args})
            observation = self._execute_tool(tool_name, args)
            logger.log_event("OBSERVATION", {"tool": tool_name, "observation": observation})

            if observation.startswith("Error executing") or observation.startswith("Tool "):
                if retry_counts < self.max_retries:
                    retry_counts += 1
                    logger.log_event("RETRY", {"reason": observation, "retry": retry_counts})
                    prompt_history += f"\nObservation: {observation}"
                    continue
                final_answer = f"Failed to execute the tool {tool_name}. {observation}"
                break

            prompt_history += f"\nObservation: {observation}"
            steps += 1

        logger.log_event("AGENT_END", {"steps": steps, "final_answer": final_answer})
        return final_answer or "No answer produced."

    def _extract_thought(self, content: str) -> Optional[str]:
        match = re.search(r"Thought:\s*(.*?)\n(Action:|Final Answer:|$)", content, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    def _extract_final_answer(self, content: str) -> Optional[str]:
        match = re.search(r"Final Answer:\s*(.*)", content, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    def _extract_action(self, content: str) -> Optional[tuple[str, str]]:
        match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\((.*?)\)", content, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        tool_name = match.group(1).strip()
        args = match.group(2).strip()
        if args.startswith('"') and args.endswith('"'):
            args = args[1:-1]
        if args.startswith("'") and args.endswith("'"):
            args = args[1:-1]
        return tool_name, args

    def _execute_tool(self, tool_name: str, args: str) -> str:
        for tool in self.tools:
            if tool.get("name") == tool_name:
                fn = tool.get("fn")
                try:
                    if callable(fn):
                        return fn(args)
                    return str(fn)
                except Exception as e:
                    return f"Error executing {tool_name}: {e}"
        return f"Tool {tool_name} not found."
