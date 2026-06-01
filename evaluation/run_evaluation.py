import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv

from retail_test_cases import RETAIL_TEST_CASES
from src.agent.agent import ReActAgent
from src.tools import TOOLS


RESULTS_DIR = Path("evaluation/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def build_llm():
    """
    Build LLM provider from .env.

    Supports:
    - DEFAULT_PROVIDER=openai
    - DEFAULT_PROVIDER=google
    - DEFAULT_PROVIDER=local
    """
    load_dotenv()

    provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    model = os.getenv("DEFAULT_MODEL")

    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name=model or "gpt-4o-mini",
        )

    if provider == "google":
        from src.core.gemini_provider import GeminiProvider

        return GeminiProvider(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name=model or "gemini-1.5-flash",
        )

    if provider == "local":
        from src.core.local_provider import LocalProvider

        return LocalProvider(
            model_path=os.getenv("LOCAL_MODEL_PATH"),
            model_name=model or "local-gguf",
        )

    raise ValueError(f"Unsupported provider: {provider}")


def run_baseline_chatbot(llm, question: str) -> Dict[str, Any]:
    """
    Baseline chatbot: no tools, direct answer only.
    This is intentionally tool-free to compare with ReAct Agent.
    """
    system_prompt = """
You are a normal chatbot without access to external tools or databases.
Answer the user's question directly based only on your own reasoning.
If exact product data, stock, coupon, or shipping fee is unknown, say that you are unsure.
"""

    result = llm.generate(question, system_prompt=system_prompt)

    return {
        "answer": result.get("content", "").strip(),
        "provider": result.get("provider"),
        "usage": result.get("usage"),
        "latency_ms": result.get("latency_ms"),
    }


def run_react_agent(llm, question: str, max_steps: int = 10) -> Dict[str, Any]:
    """
    Run ReAct Agent and return answer + trace.
    """
    agent = ReActAgent(
        llm=llm,
        tools=TOOLS,
        max_steps=max_steps,
    )

    answer = agent.run(question)

    trace = agent.history
    tool_calls = extract_tool_calls_from_trace(trace)

    return {
        "answer": answer,
        "trace": trace,
        "tool_calls": tool_calls,
        "num_steps": len(trace),
    }


def extract_tool_calls_from_trace(trace: List[Dict[str, Any]]) -> List[str]:
    """
    Extract tool names from Action lines in agent history.
    """
    tool_calls = []

    for item in trace:
        output = item.get("llm_output", "")

        matches = re.findall(
            r"Action\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            output,
            flags=re.IGNORECASE,
        )

        tool_calls.extend(matches)

    return tool_calls


def normalize_text(text: str) -> str:
    return text.lower().strip()


def normalize_number_text(text: str) -> str:
    """
    Keep only digits.
    Example:
        '46.594.840 VND' -> '46594840'
    """
    return re.sub(r"\D", "", text)


def contains_expected_total(answer: str, expected_total: Optional[int]) -> bool:
    if expected_total is None:
        return True

    digits = normalize_number_text(answer)
    expected_digits = str(expected_total)

    return expected_digits in digits


def contains_keywords(answer: str, keywords: Optional[List[str]]) -> bool:
    if not keywords:
        return True

    answer_norm = normalize_text(answer)

    for keyword in keywords:
        if normalize_text(keyword) not in answer_norm:
            return False

    return True


def avoids_forbidden_keywords(answer: str, forbidden_keywords: Optional[List[str]]) -> bool:
    if not forbidden_keywords:
        return True

    answer_norm = normalize_text(answer)

    for keyword in forbidden_keywords:
        if normalize_text(keyword) in answer_norm:
            return False

    return True


def has_expected_tools(tool_calls: List[str], expected_tools: Optional[List[str]]) -> bool:
    if not expected_tools:
        return True

    called = set(tool_calls)

    for tool_name in expected_tools:
        if tool_name not in called:
            return False

    return True


def judge_answer(
    answer: str,
    tool_calls: List[str],
    test_case: Dict[str, Any],
    mode: str,
) -> Dict[str, Any]:
    """
    Heuristic evaluator.

    For ReAct Agent, we check:
    - expected total
    - expected keywords
    - forbidden keywords
    - expected tools

    For Baseline Chatbot, we check:
    - expected total
    - expected keywords
    - forbidden keywords

    Baseline is not expected to use tools.
    """
    expected_total = test_case.get("expected_total")
    expected_keywords = test_case.get("expected_keywords")
    forbidden_keywords = test_case.get("forbidden_keywords")
    expected_tools = test_case.get("expected_tools")

    checks = {
        "contains_expected_total": contains_expected_total(answer, expected_total),
        "contains_expected_keywords": contains_keywords(answer, expected_keywords),
        "avoids_forbidden_keywords": avoids_forbidden_keywords(answer, forbidden_keywords),
    }

    if mode == "agent":
        checks["has_expected_tools"] = has_expected_tools(tool_calls, expected_tools)

    passed = all(checks.values())

    return {
        "passed": passed,
        "checks": checks,
    }


def evaluate_all_cases(run_baseline: bool = True, run_agent: bool = True) -> List[Dict[str, Any]]:
    """
    Run all test cases.
    """
    llm = build_llm()
    all_results = []

    for index, test_case in enumerate(RETAIL_TEST_CASES, start=1):
        print("=" * 80)
        print(f"[{index}/{len(RETAIL_TEST_CASES)}] {test_case['id']} - {test_case['name']}")
        print("=" * 80)

        case_result = {
            "test_case": test_case,
            "baseline": None,
            "agent": None,
        }

        question = test_case["question"]

        if run_baseline:
            print("[Baseline] Running...")
            baseline_result = run_baseline_chatbot(llm, question)
            baseline_judgment = judge_answer(
                answer=baseline_result["answer"],
                tool_calls=[],
                test_case=test_case,
                mode="baseline",
            )

            case_result["baseline"] = {
                **baseline_result,
                "judgment": baseline_judgment,
            }

            print("[Baseline] Passed:", baseline_judgment["passed"])
            print("[Baseline] Answer:", baseline_result["answer"])

        if run_agent:
            print("[Agent] Running...")
            agent_result = run_react_agent(llm, question)
            agent_judgment = judge_answer(
                answer=agent_result["answer"],
                tool_calls=agent_result["tool_calls"],
                test_case=test_case,
                mode="agent",
            )

            case_result["agent"] = {
                **agent_result,
                "judgment": agent_judgment,
            }

            print("[Agent] Passed:", agent_judgment["passed"])
            print("[Agent] Tool calls:", agent_result["tool_calls"])
            print("[Agent] Answer:", agent_result["answer"])

        all_results.append(case_result)

    return all_results


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build summary metrics.
    """
    summary = {
        "total_cases": len(results),
        "baseline_passed": 0,
        "agent_passed": 0,
        "by_category": {},
    }

    for item in results:
        category = item["test_case"]["category"]

        if category not in summary["by_category"]:
            summary["by_category"][category] = {
                "total": 0,
                "baseline_passed": 0,
                "agent_passed": 0,
            }

        summary["by_category"][category]["total"] += 1

        baseline = item.get("baseline")
        agent = item.get("agent")

        if baseline and baseline["judgment"]["passed"]:
            summary["baseline_passed"] += 1
            summary["by_category"][category]["baseline_passed"] += 1

        if agent and agent["judgment"]["passed"]:
            summary["agent_passed"] += 1
            summary["by_category"][category]["agent_passed"] += 1

    summary["baseline_pass_rate"] = (
        summary["baseline_passed"] / summary["total_cases"]
        if summary["total_cases"] > 0
        else 0
    )

    summary["agent_pass_rate"] = (
        summary["agent_passed"] / summary["total_cases"]
        if summary["total_cases"] > 0
        else 0
    )

    return summary


def save_json_results(results: List[Dict[str, Any]], summary: Dict[str, Any], timestamp: str) -> Path:
    output_path = RESULTS_DIR / f"retail_eval_{timestamp}.json"

    payload = {
        "timestamp": timestamp,
        "summary": summary,
        "results": results,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return output_path


def save_markdown_report(results: List[Dict[str, Any]], summary: Dict[str, Any], timestamp: str) -> Path:
    output_path = RESULTS_DIR / f"retail_eval_{timestamp}.md"

    lines = []
    lines.append("# Retail ReAct Agent Evaluation Report\n")
    lines.append(f"Timestamp: `{timestamp}`\n")

    lines.append("## Summary\n")
    lines.append(f"- Total cases: {summary['total_cases']}")
    lines.append(f"- Baseline passed: {summary['baseline_passed']}/{summary['total_cases']}")
    lines.append(f"- Agent passed: {summary['agent_passed']}/{summary['total_cases']}")
    lines.append(f"- Baseline pass rate: {summary['baseline_pass_rate']:.2%}")
    lines.append(f"- Agent pass rate: {summary['agent_pass_rate']:.2%}\n")

    lines.append("## Summary by Category\n")
    lines.append("| Category | Total | Baseline Passed | Agent Passed |")
    lines.append("|---|---:|---:|---:|")

    for category, stats in summary["by_category"].items():
        lines.append(
            f"| {category} | {stats['total']} | {stats['baseline_passed']} | {stats['agent_passed']} |"
        )

    lines.append("\n## Detailed Results\n")

    for item in results:
        test_case = item["test_case"]
        lines.append(f"### {test_case['id']} - {test_case['name']}\n")
        lines.append(f"- Category: `{test_case['category']}`")
        lines.append(f"- Notes: {test_case.get('notes', '')}")

        baseline = item.get("baseline")
        agent = item.get("agent")

        if baseline:
            lines.append("\n**Baseline**")
            lines.append(f"- Passed: `{baseline['judgment']['passed']}`")
            lines.append(f"- Checks: `{baseline['judgment']['checks']}`")
            lines.append(f"- Answer: {baseline['answer']}")

        if agent:
            lines.append("\n**ReAct Agent**")
            lines.append(f"- Passed: `{agent['judgment']['passed']}`")
            lines.append(f"- Checks: `{agent['judgment']['checks']}`")
            lines.append(f"- Tool calls: `{agent['tool_calls']}`")
            lines.append(f"- Steps: `{agent['num_steps']}`")
            lines.append(f"- Answer: {agent['answer']}")

        lines.append("\n---\n")

    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = evaluate_all_cases(
        run_baseline=True,
        run_agent=True,
    )

    summary = summarize_results(results)

    json_path = save_json_results(results, summary, timestamp)
    md_path = save_markdown_report(results, summary, timestamp)

    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nSaved JSON results to: {json_path}")
    print(f"Saved Markdown report to: {md_path}")


if __name__ == "__main__":
    main()