import os
from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.core.gemini_provider import GeminiProvider
from src.tools.search_tool import search_documents


def main():
    load_dotenv()

    tools = [
        {
            "name": "search_documents",
            "description": "Search local xdocuments for a query and return snippets.",
            "fn": search_documents,
        }
    ]

    provider = GeminiProvider(
    model_name="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

    agent = ReActAgent(
        llm=provider,
        tools=tools,
        max_steps=4,
        max_retries=2,
    )

    print("=" * 60)
    print("ReAct Agent Interactive Demo")
    print("Type 'exit' to quit")
    print("=" * 60)

    while True:
        try:
            query = input("\nYou: ").strip()

            if not query:
                continue

            if query.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            answer = agent.run(query)

            print("\nAgent:")
            print(answer)

        except KeyboardInterrupt:
            print("\n\nStopped by user.")
            break

        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()