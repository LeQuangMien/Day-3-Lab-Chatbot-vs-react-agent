from typing import Any, Dict, Generator, Optional

from fastapi.testclient import TestClient

from src.api.main import app, get_llm_provider, get_react_agent
from src.core.llm_provider import LLMProvider


class FakeLLMProvider(LLMProvider):
    def __init__(self) -> None:
        super().__init__(model_name="fake-llm", api_key="test-key")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        return {
            "content": f"LLM answer: {prompt}",
            "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            "latency_ms": 12,
            "provider": "fake",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        yield "fake"


class FakeAgent:
    def __init__(self) -> None:
        self.llm = FakeLLMProvider()
        self.max_steps = 5

    def run(self, user_input: str) -> str:
        return f"Agent answer: {user_input}"


def test_llm_endpoint():
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/llm",
        json={"prompt": "Xin chào", "system_prompt": "Trả lời ngắn gọn"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["mode"] == "llm"
    assert payload["model"] == "fake-llm"
    assert payload["response"] == "LLM answer: Xin chào"


def test_agent_endpoint():
    app.dependency_overrides[get_react_agent] = lambda: FakeAgent()
    client = TestClient(app)

    response = client.post(
        "/agent",
        json={"prompt": "Tìm laptop dưới 20 triệu", "max_steps": 3},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["mode"] == "agent"
    assert payload["answer"] == "Agent answer: Tìm laptop dưới 20 triệu"
    assert payload["max_steps"] == 3
