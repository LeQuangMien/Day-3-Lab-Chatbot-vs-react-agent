from typing import Callable, Dict, List, Optional

from src.tools.calculator_tool import calculator
from src.tools.discount_tools import apply_discount
from src.tools.product_tools import check_stock, search_product
from src.tools.shipping_tools import calculate_shipping


TOOLS = [
    {
        "name": "search_product",
        "description": (
            "Search products by keyword and optional max price. "
            "Arguments: query: str, max_price: optional number in VND."
        ),
        "func": search_product,
    },
    {
        "name": "check_stock",
        "description": (
            "Check if a product has enough stock. "
            "Arguments: product_id: str, quantity: int."
        ),
        "func": check_stock,
    },
    {
        "name": "apply_discount",
        "description": (
            "Apply a coupon code to a product price. "
            "Arguments: price: number in VND, coupon_code: str."
        ),
        "func": apply_discount,
    },
    {
        "name": "calculate_shipping",
        "description": (
            "Calculate shipping fee by weight and destination. "
            "Arguments: weight: number in kg, destination: str, coupon_code: optional str."
        ),
        "func": calculate_shipping,
    },
    {
        "name": "calculator",
        "description": (
            "Safely calculate arithmetic expressions. "
            "Arguments: expression: str."
        ),
        "func": calculator,
    },
]


def get_tool_by_name(tool_name: str) -> Optional[Callable]:
    """
    Return a tool function by tool name.
    """
    for tool in TOOLS:
        if tool["name"] == tool_name:
            return tool["func"]

    return None


def get_tools_description() -> str:
    """
    Return all tool descriptions as text for the ReAct system prompt.
    """
    lines = []

    for tool in TOOLS:
        lines.append(f"- {tool['name']}: {tool['description']}")

    return "\n".join(lines)


def get_tool_names() -> List[str]:
    """
    Return available tool names.
    """
    return [tool["name"] for tool in TOOLS]