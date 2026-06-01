from typing import Any, Dict, Optional

from src.data.fake_retail_data import PRODUCTS


def normalize_text(text: str) -> str:
    return text.strip().lower()


def format_vnd(amount: float) -> str:
    return f"{int(round(amount)):,} VND".replace(",", ".")


def find_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    product_id = product_id.strip().upper()

    for product in PRODUCTS:
        if product["id"].upper() == product_id:
            return product

    return None