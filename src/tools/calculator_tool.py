import ast
import operator
from typing import Any, Dict

from src.tools.utils import format_vnd


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers are allowed.")

    if isinstance(node, ast.BinOp):
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        op_type = type(node.op)

        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Operator {op_type.__name__} is not allowed.")

        return _ALLOWED_OPERATORS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval_node(node.operand)
        op_type = type(node.op)

        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Unary operator {op_type.__name__} is not allowed.")

        return _ALLOWED_OPERATORS[op_type](operand)

    raise ValueError(f"Unsupported expression: {type(node).__name__}")


def calculator(expression: str) -> Dict[str, Any]:
    """
    Safely calculate an arithmetic expression.

    Args:
        expression: Arithmetic expression, for example "18990000 * 2 + 25000".

    Returns:
        Calculation result.
    """
    try:
        parsed = ast.parse(expression, mode="eval")
        result = _safe_eval_node(parsed.body)

        return {
            "success": True,
            "expression": expression,
            "result": result,
            "result_text": format_vnd(result) if abs(result) >= 1000 else str(result),
            "message": "Calculation completed successfully.",
        }

    except Exception as e:
        return {
            "success": False,
            "expression": expression,
            "result": None,
            "message": f"Calculation error: {str(e)}",
        }