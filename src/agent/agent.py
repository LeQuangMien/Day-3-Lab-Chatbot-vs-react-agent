import ast
import json
import os
import re
import inspect
from typing import List, Dict, Tuple, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        Implement the system prompt that instructs the agent to follow ReAct.
        Should include:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
You are an intelligent ReAct agent.

You have access to the following tools:
{tool_descriptions}

You must solve the user's task by reasoning step-by-step and using tools when needed.

Use this exact format:

Thought: explain what you need to do next.
Action: tool_name(arg1=value1, arg2=value2)

After you receive an Observation, continue:

Thought: explain the next step.
Action: tool_name(arg1=value1, arg2=value2)

When you have enough information, stop using tools and answer with:

Final Answer: your final answer to the user.

Important rules:
- Only use tools listed above.
- Do not invent product prices, stock, discounts, or shipping fees.
- If a question requires product data, stock, discount, shipping, or calculation, use the tools.
- Do not write Observation yourself. Observation will be provided by the system after a tool call.
- Use valid Python-style arguments in Action.
- Always answer in the same language as the user's question.
- Example Action formats:
  Action: search_product(query="laptop", max_price=20000000)
  Action: check_stock(product_id="P001", quantity=2)
  Action: apply_discount(price=31000000, coupon_code="SALE10")
  Action: calculate_shipping(weight=3.4, destination="Hà Nội")
  Action: calculator(expression="15500000 * 2 * 0.9 + 52200")
"""

    def run(self, user_input: str) -> str:
        """
        Implement the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name, "max_steps": self.max_steps})
        
        self.history = []

        current_prompt = f"User question: {user_input}\n"
        last_response = ""

        steps = 0


        while steps < self.max_steps:
            steps += 1
            # Generate LLM response
            try:
                result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            except Exception as e:
                logger.log_event("LLM ERROR", {"step": steps, "error": str(e)})
                return f"Error during LLM generation: {e}"
            
            llm_output = result.get("content", "").strip()
            last_response = llm_output

            self.history.append(
                {
                    "step": steps,
                    "prompt": current_prompt,
                    "llm_output": llm_output,
                    "llm_metadata": {
                        "provider": result.get("provider"),
                        "usage": result.get("usage"),
                        "latency_ms": result.get("latency_ms"),
                    },
                }
            )

            logger.log_event(
                "AGENT_STEP",
                {
                    "step": steps,
                    "llm_output": llm_output,
                    "provider": result.get("provider"),
                    "usage": result.get("usage"),
                    "latency_ms": result.get("latency_ms"),
                },
            )

            final_answer = self._extract_final_answer(llm_output)
            if final_answer is not None:
                logger.log_event(
                    "AGENT_END",
                    {
                        "status": "success",
                        "steps": steps,
                        "final_answer": final_answer,
                    },
                )
                return final_answer
            
            # Parse Thought/Action from result
            action = self._parse_action(llm_output)

            if action is None:
                logger.log_event(
                    "PARSER_ERROR",
                    {
                        "step": steps,
                        "raw_output": llm_output,
                    },
                )

                current_prompt += f"""

Assistant output:
{llm_output}

Observation: Could not parse a valid Action. Please follow the required format:
Thought: ...
Action: tool_name(arg1=value1, arg2=value2)
"""
                continue

            # If Action found -> Call tool -> Append Observation

            tool_name, args = action

            observation = self._execute_tool(tool_name, args)

            logger.log_event(
                "TOOL_CALL",
                {
                    "step": steps,
                    "tool_name": tool_name,
                    "args": args,
                    "observation": observation,
                },
            )

            current_prompt += f"""

Assistant output:
{llm_output}

Observation: {observation}
"""

        logger.log_event(
            "AGENT_END",
            {
                "status": "max_steps_reached",
                "steps": steps,
                "last_response": last_response,
            },
        )

        return (
            "I could not complete the task within the maximum number of reasoning steps. "
            "Here is the last model response:\n\n"
            f"{last_response}"
        )



            
            # TODO: If Final Answer found -> Break loop
                        

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Execute a tool by name with given arguments.
        
        Returns:
            JSON string containing the tool result or error
        """
        tool_func = None

        for tool in self.tools:
            if tool['name'] == tool_name:
                tool_func = tool['func']
                break
        
        if tool_func is None:
            return self._to_json_string(
                {
                    "success": False,
                    "message": f"Tool '{tool_name}' not found.",
                }
            )
        try:
            if isinstance(args, dict) and "_args" in args and "_kwargs" in args:
                result = tool_func(*args["_args"], **args["_kwargs"])
            elif isinstance(args, dict):
                result = tool_func(**args)
            elif isinstance(args, list):
                result = tool_func(*args)
            elif args is None:
                result = tool_func()
            else:
                result = tool_func(args)

            return self._to_json_string(result)
        except TypeError as e:
            logger.log_event(
                "TOOL_ERROR",
                {
                    "tool_name": tool_name,
                    "args": args,
                    "error": str(e),
                    "signature": str(inspect.signature(tool_func)),
                },
            )

            return self._to_json_string(
                {
                    "success": False,
                    "message": f"Tool argument error for '{tool_name}': {str(e)}",
                    "expected_signature": str(inspect.signature(tool_func)),
                    "received_args": args,
                }
            )
        
        except Exception as e:
            logger.log_event(
                "TOOL_ERROR",
                {
                    "tool_name": tool_name,
                    "args": args,
                    "error": str(e),
                },
            )

            return self._to_json_string(
                {
                    "success": False,
                    "message": f"Tool execution error for '{tool_name}': {str(e)}",
                    "received_args": args,
                }
            )            
    

    def _extract_final_answer(self, text: str) -> Optional[str]:
        """
        Extract Final Answer from LLM output if present.
        """
        match = re.search(
            r"Final Answer\s*:\s*(.*)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            return match.group(1).strip()

        return None
    
    def _parse_action(self, text: str) -> Optional[Tuple[str, Any]]:
        """
        Parse Action from LLM output.

        Supported formats:
            Action: search_product(query="laptop", max_price=20000000)
            Action: check_stock(product_id="P001", quantity=2)
            Action: calculator(expression="15500000 * 2")
            Action: search_product({"query": "laptop", "max_price": 20000000})
        """
        action_match = re.search(
            r"Action\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not action_match:
            return None

        tool_name = action_match.group(1).strip()
        raw_args = action_match.group(2).strip()

        try:
            parsed_args = self._parse_tool_args(raw_args)
            return tool_name, parsed_args
        except Exception as e:
            logger.log_event(
                "ACTION_PARSE_ERROR",
                {
                    "tool_name": tool_name,
                    "raw_args": raw_args,
                    "error": str(e),
                },
            )

            return tool_name, raw_args
        
    def _parse_tool_args(self, raw_args: str) -> Any:
        """
        Parse the argument string inside tool_name(...).

        Examples:
            query="laptop", max_price=20000000
            {"query": "laptop", "max_price": 20000000}
            "15500000 * 2"
        """
        raw_args = raw_args.strip()

        if raw_args == "":
            return {}

        # Case 1: dictionary argument
        # Example: {"query": "laptop", "max_price": 20000000}
        if raw_args.startswith("{") and raw_args.endswith("}"):
            try:
                return json.loads(raw_args)
            except json.JSONDecodeError:
                return ast.literal_eval(raw_args)

        # Case 2: list/tuple argument
        if (
            raw_args.startswith("[")
            and raw_args.endswith("]")
            or raw_args.startswith("(")
            and raw_args.endswith(")")
        ):
            return ast.literal_eval(raw_args)

        # Case 3: keyword arguments
        # Example: query="laptop", max_price=20000000
        fake_call = f"tool({raw_args})"
        parsed = ast.parse(fake_call, mode="eval")

        if not isinstance(parsed.body, ast.Call):
            raise ValueError("Parsed expression is not a function call.")

        call_node = parsed.body

        args = []

        for arg in call_node.args:
            args.append(ast.literal_eval(arg))

        kwargs = {}

        for keyword in call_node.keywords:
            if keyword.arg is None:
                raise ValueError("Keyword argument cannot be None.")
            kwargs[keyword.arg] = ast.literal_eval(keyword.value)

        if args and kwargs:
            return {
                "_args": args,
                "_kwargs": kwargs,
            }

        if kwargs:
            return kwargs

        if len(args) == 1:
            return args[0]

        if args:
            return args

        return {}
    
    def _to_json_string(self, data: Any) -> str:
        """
        Convert tool result to JSON string for Observation.
        """
        try:
            return json.dumps(data, ensure_ascii=False)
        except TypeError:
            return str(data)