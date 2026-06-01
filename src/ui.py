import os
from typing import Dict

import streamlit as st
from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.agent.chatbot import ChatbotBaseline
from src.core.gemini_provider import GeminiProvider
from src.core.llm_provider import LLMProvider
from src.core.local_provider import LocalProvider
from src.core.mock_provider import MockProvider
from src.core.openai_provider import OpenAIProvider
from src.tools.search_tool import search_documents

load_dotenv()

PROVIDERS = ["Mock", "OpenAI", "Gemini", "Local"]


def get_provider(provider_name: str, config: Dict[str, str]) -> LLMProvider:
    if provider_name == "OpenAI":
        return OpenAIProvider(model_name=config.get("model", "gpt-4o"), api_key=config.get("api_key"))
    if provider_name == "Gemini":
        return GeminiProvider(model_name=config.get("model", "gemini-2.5-flash"), api_key=config.get("api_key"))
    if provider_name == "Local":
        return LocalProvider(model_path=config.get("model_path", ""))
    return MockProvider()


def build_agent(use_react: bool, provider: LLMProvider) -> object:
    if use_react:
        tools = [
            {
                "name": "search_documents",
                "description": "Search local documents for a query and return snippets.",
                "fn": search_documents,
            }
        ]
        return ReActAgent(llm=provider, tools=tools, max_steps=4, max_retries=2)
    return ChatbotBaseline(llm=provider)


def log_history(user_input: str, answer: str, agent_name: str) -> None:
    st.session_state.history.append({"role": "user", "text": user_input, "agent": agent_name})
    st.session_state.history.append({"role": "assistant", "text": answer, "agent": agent_name})


def init_state() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []
    if "active_agent" not in st.session_state:
        st.session_state.active_agent = "Baseline"
    if "provider" not in st.session_state:
        st.session_state.provider = "Mock"


def render_conversation() -> None:
    if not st.session_state.history:
        st.info("Nhập câu hỏi ở bên dưới rồi gửi để so sánh Chatbot và ReAct Agent.")
        return

    for item in st.session_state.history:
        label = "Bạn" if item["role"] == "user" else f"{item['agent']}"
        message_type = st.chat_message("user") if item["role"] == "user" else st.chat_message("assistant")
        with message_type:
            st.markdown(f"**{label}:** {item['text']}")


def render_sidebar() -> Dict[str, str]:
    st.sidebar.title("Cấu hình UI/UX")
    selected_provider = st.sidebar.selectbox("Chọn provider", PROVIDERS, index=PROVIDERS.index(st.session_state.provider))
    selected_agent = st.sidebar.radio("Chọn chế độ", ["Baseline Chatbot", "ReAct Agent"])

    api_key = ""
    model = ""
    model_path = ""
    if selected_provider == "OpenAI":
        api_key = st.sidebar.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
        model = st.sidebar.text_input("OpenAI model", value=os.getenv("OPENAI_MODEL", "gpt-4o"))
    elif selected_provider == "Gemini":
        api_key = st.sidebar.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
        model = st.sidebar.text_input("Gemini model", value=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    elif selected_provider == "Local":
        model_path = st.sidebar.text_input("Đường dẫn model local", value=os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf"))
        model = st.sidebar.text_input("Local model label", value=os.path.basename(model_path) if model_path else "local-model")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Hướng dẫn nhanh")
    st.sidebar.markdown(
        "- Chọn provider phù hợp hoặc dùng `Mock` để chạy thử ngay.\n"
        "- Chọn `Baseline Chatbot` để xem phản hồi trực tiếp.\n"
        "- Chọn `ReAct Agent` để xem agent sử dụng tool search.\n"
        "- Nhập truy vấn và nhấn `Gửi` để so sánh.")

    return {
        "provider": selected_provider,
        "agent": selected_agent,
        "api_key": api_key,
        "model": model,
        "model_path": model_path,
    }


def main() -> None:
    st.set_page_config(page_title="Chatbot vs ReAct Agent", page_icon="🤖", layout="wide")
    init_state()

    st.title("Chatbot vs ReAct Agent")
    st.markdown(
        "Ứng dụng demo UI/UX để so sánh hành vi của một chatbot baseline với agent ReAct có tích hợp search tool." 
        "Sử dụng `Mock` nếu đang chạy thử, hoặc cấu hình OpenAI/Gemini/Local nếu bạn có API key/model." 
    )

    config = render_sidebar()
    st.session_state.provider = config["provider"]
    st.session_state.active_agent = config["agent"]

    valid_provider = True
    provider_message = ""
    try:
        provider = get_provider(config["provider"], config)
    except Exception as exc:
        valid_provider = False
        provider_message = str(exc)

    if not valid_provider:
        st.warning(f"Provider không thể tạo: {provider_message}")
        provider = MockProvider()
        st.info("Chuyển sang Mock Provider để tiếp tục chạy demo.")

    agent = build_agent(use_react=(config["agent"] == "ReAct Agent"), provider=provider)

    container = st.container()
    with container:
        user_input = st.text_area("Nhập câu hỏi của bạn", height=120)
        submitted = st.button("Gửi")

    if submitted and user_input.strip():
        with st.spinner("Đang chạy agent..."):
            answer = agent.run(user_input)
            log_history(user_input, answer, config["agent"])
            st.success("Đã nhận kết quả")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Đối thoại")
        render_conversation()

    with col2:
        st.subheader("Thông tin thêm")
        st.markdown(f"**Provider:** {config['provider']}")
        st.markdown(f"**Chế độ:** {config['agent']}")
        st.markdown("---")
        if config["agent"] == "ReAct Agent":
            st.markdown("**Tool ReAct Agent:**")
            st.code("search_documents(query)", language="python")
            st.markdown("Tìm kiếm nội dung trong `src/tools/docs/` và trả về các đoạn trích phù hợp.")
        else:
            st.markdown("**Ghi chú:** Baseline Chatbot trả lời trực tiếp mà không gọi tool.")

    st.markdown("---")
    st.caption("UI demo được xây dựng để hỗ trợ học tập và minh hoạ cách so sánh hai kiểu trợ lý AI.")


if __name__ == "__main__":
    main()
