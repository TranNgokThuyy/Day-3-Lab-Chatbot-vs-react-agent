import os
import sys

from dotenv import load_dotenv

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

load_dotenv()

from src.core.gemini_provider import GeminiProvider
from src.agent.agent import ReActAgent
from src.agent.chatbot import ChatbotBaseline
from src.tools.search_tool import search_documents

app = FastAPI()

# Static
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

# Templates
templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

# Gemini Provider
provider = GeminiProvider(
    model_name="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

# Baseline Chatbot
chatbot = ChatbotBaseline(llm=provider)

# ReAct Agent
agent = ReActAgent(
    llm=provider,
    tools=[
        {
            "name": "search_documents",
            "description": "Search local documents for a query and return relevant snippets.",
            "fn": search_documents,
        }
    ],
    max_steps=4,
    max_retries=2,
)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "query": "",
            "baseline_answer": "",
            "agent_answer": "",
            "metrics": [],
        },
    )


@app.post("/", response_class=HTMLResponse)
def submit(request: Request, query: str = Form(...)):
    baseline_answer = chatbot.run(query)
    agent_answer = agent.run(query)

    from src.telemetry.metrics import tracker

    metrics = tracker.session_metrics[-4:]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "query": query,
            "baseline_answer": baseline_answer,
            "agent_answer": agent_answer,
            "metrics": metrics,
        },
    )