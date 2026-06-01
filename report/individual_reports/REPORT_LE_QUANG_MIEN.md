# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Lê Quang Miền
- **Student ID**: 2A202600715
- **Date**: 01-06-2026

---

## I. Technical Contribution (15 Points)

### 1. Overview

In this lab, my main contribution was implementing and evaluating a **ReAct-based retail assistant agent** and comparing it against a normal baseline chatbot. The agent was designed for a small e-commerce scenario where the user asks about products, stock availability, discount codes, shipping fees, and final payment totals.

The baseline chatbot only generated direct answers from the LLM. In contrast, the ReAct agent followed a structured reasoning loop:

```text
User Question
→ Thought
→ Action: call a tool
→ Observation: receive tool result
→ repeat if needed
→ Final Answer
```

### 2. Modules Implemented

The implementation focused on the following components:

- **ReAct Agent Core**: `src/agent/agent.py`
  - Implemented the multi-step ReAct reasoning loop.
  - Added parsing for tool actions.
  - Added execution flow for tool calls and observations.
  - Added max-step protection to avoid infinite loops.

- **Retail Tools**: `src/tools`
  - `search_product(query)`: searches a small product database.
  - `check_stock(product_id, quantity)`: checks whether the requested quantity is available.
  - `apply_discount(price, coupon_code)`: applies supported coupons such as `SALE10` and `STUDENT5`.
  - `calculate_shipping(weight, destination, coupon_code=None)`: computes shipping fee by destination and weight.
  - `calculator(expression)`: performs final arithmetic calculation.

- **Evaluation Script**: `evaluation`
  - Created 13 test cases across three categories: `success`, `edge`, and `failure_stress`.
  - Compared baseline and agent answers using expected totals, expected keywords, forbidden keywords, and expected tool calls.
  - Saved evaluation results to `retail_eval_20260601_151158.json`.

---

## II. Debugging Case Study (10 Points)

### 1. Problem Description

The most important failure case was **E01: MacBook quantity exceeds stock**.

The user requested:

```text
I want to buy 3 MacBook Air M2 units and ship them to Hanoi.
Use STUDENT5 and calculate the final total.
Please check stock before calculating.
```

The product database only had **2 MacBook Air M2 units** in stock. The agent correctly called `search_product` and `check_stock`, and the observation clearly showed:

```json
{
  "requested_quantity": 3,
  "current_stock": 2,
  "available": false,
  "message": "Not enough stock. Requested 3, but only 2 available."
}
```

However, the agent did not stop. It asked whether the user wanted to continue with 2 units and then continued calculating a total for 2 units. This caused the test case to fail because the agent should not change the requested quantity by itself.

### 2. Log Source

The failure was identified in the evaluation output file:

```text
retail_eval_20260601_151158.json
```

Relevant trace summary:

```text
Step 1: search_product(query="MacBook Air M2")
Step 2: check_stock(product_id="P002", quantity=3)
Observation: Not enough stock. Requested 3, but only 2 available.
Step 3: Agent asks whether user wants to buy 2 units instead.
Later steps: Agent continues calculating price for 2 units.
Final result: Failed.
```

### 3. Diagnosis

The root cause was not a tool failure. The tools returned correct information. The problem was caused by **insufficient policy constraints in the agent prompt and loop control**.

The model understood that only 2 units were available, but it treated this as an opportunity to continue the conversation by suggesting a modified quantity. In a real checkout system, this is unsafe because the user asked for 3 units and did not approve changing the order to 2 units.

There were three related issues:

1. The system prompt did not explicitly say that `available=false` must stop the purchase flow.
2. The code did not include a hard guardrail after the `check_stock` tool.
3. The agent was allowed to continue reasoning even after a business-rule violation.

### 4. Solution

The solution is to add a **prompt-level rule**:

```text
If check_stock returns available=false, you MUST stop immediately.
```

This fix is important because safety-critical business rules should not rely only on the LLM's reasoning. The program should enforce them deterministically.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning

The `Thought` block helped the agent decompose a user request into smaller steps. A direct chatbot often produced a vague answer such as "I cannot check current stock or price." The ReAct agent, however, could reason through a concrete workflow:

```text
Find product → check stock → apply discount → calculate shipping → compute final total
```

This made the agent much more effective for tasks that require external data and arithmetic. In all four normal success cases, the ReAct agent produced the correct final amount, while the baseline chatbot failed all of them.

### 2. Reliability

The agent performed worse or less reliably than expected in edge cases. The main examples were:

- **Out-of-stock or insufficient-stock cases**: the agent sometimes continued the purchase flow instead of stopping immediately.
- **Evaluator-sensitive cases**: the answer was semantically correct but failed because the wording did not match expected keywords exactly.
- **Mandatory tool-call cases**: the agent sometimes skipped a tool because the needed information was already available from a previous observation. For example, if `search_product` already returned `stock = 0`, the agent answered directly instead of calling `check_stock`, even though the evaluator expected `check_stock`.
- **Final arithmetic cases**: the agent sometimes calculated the final total directly instead of calling the `calculator` tool, causing a tool-chain mismatch.

This showed that ReAct agents are powerful but not automatically reliable. They need clear tool contracts, strict stopping rules, and deterministic validation around important business logic.

### 3. Observation

Observations were the key difference between the chatbot and the agent. They grounded the model's next step in actual tool outputs.

For example:

- After `search_product`, the agent received product ID, price, stock, and weight.
- After `check_stock`, the agent knew whether it could proceed.
- After `apply_discount`, the agent received the exact discounted price.
- After `calculate_shipping`, the agent received the shipping fee.
- After `calculator`, the agent received the final computed total.

This feedback loop made the agent more accurate than a normal chatbot. However, the E01 failure showed that observations alone are not enough. The agent must also have strict rules for interpreting observations, especially when an observation indicates failure.

---

## IV. Future Improvements (5 Points)

### 1. Scalability

To scale this agent beyond a small demo, I would separate the system into multiple layers:

- **Planner layer**: decides which tools are needed.
- **Tool execution layer**: validates arguments and executes tools.
- **Policy layer**: enforces business rules such as stock availability and supported destinations.
- **Response layer**: formats the final answer for the user.

For many tools, I would also add a tool registry with metadata, schema validation, and examples for each tool.

### 2. Safety

The most important safety improvement is deterministic guardrails. Some rules should be enforced by code, not by the LLM:

- If stock is insufficient, stop immediately.
- If destination is unsupported, stop immediately.
- If product is not found, stop immediately.
- If coupon is invalid, continue only if the user explicitly allowed checkout without a valid coupon or if the task says to calculate without it.
- Never change the requested quantity without user confirmation.

I would also add a supervisor check before the final answer:

```text
Did the agent call all required tools?
Did any tool return success=false?
Did the agent continue after a failed business condition?
Is the final total computed by calculator?
```

### 3. Performance

The current agent often takes 5-6 reasoning steps for successful cases. This is acceptable for a lab, but production systems should reduce latency and token usage.

Possible improvements:

- Combine deterministic calculations into one checkout tool.
- Use structured JSON outputs instead of free-form action strings.
- Cache repeated product search results.
- Use smaller or cheaper models for simple tool-routing decisions.
- Track token usage, latency, number of steps, and failed parse rate in a dashboard.

### 4. Next Version Plan

For the next version of the agent, I would prioritize:

1. Add hard stop for `check_stock.available == false`.
2. Require `check_stock` before any stock-related final answer.
3. Require `calculator` before every final monetary total.
4. Standardize failure messages:
   - `Không đủ hàng...`
   - `Không tìm thấy sản phẩm trong hệ thống.`
   - `Không hỗ trợ giao hàng đến ... (unsupported destination).`
5. Fix or review the expected total for the F03 test case, where the current expected value appears inconsistent with the shipping formula.

---
