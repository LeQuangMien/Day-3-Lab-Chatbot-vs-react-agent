import os
from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.tools import TOOLS

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider


def build_llm():
    load_dotenv()

    provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    model = os.getenv("DEFAULT_MODEL")

    if provider == "openai":
        return OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name=model or "gpt-4o-mini",
        )

    if provider == "google":
        return GeminiProvider(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name=model or "gemini-1.5-flash",
        )

    raise ValueError(f"Unsupported provider: {provider}")


def main():
    llm = build_llm()

    agent = ReActAgent(
        llm=llm,
        tools=TOOLS,
        max_steps=10,
    )

    question = """
Tôi muốn hỏi tối nay 10 giờ thời tiết như thế nào?
"""

    answer = agent.run(question)

    print("\n=== FINAL ANSWER ===")
    print(answer)


if __name__ == "__main__":
    main()