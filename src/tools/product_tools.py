from typing import Any, Dict, Optional

from src.data.fake_retail_data import PRODUCTS
from src.tools.utils import find_product_by_id, format_vnd, normalize_text


def search_product(query: str, max_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Search products by name, category, or description.

    Args:
        query: Product keyword, for example "laptop", "iphone", "tai nghe".
        max_price: Optional maximum price in VND.

    Returns:
        A dictionary containing matched products.
    """
    query_norm = normalize_text(query)
    matched_products = []

    for product in PRODUCTS:
        searchable_text = " ".join(
            [
                product["name"],
                product["category"],
                product.get("description", ""),
            ]
        ).lower()

        if query_norm in searchable_text:
            if max_price is None or product["price"] <= max_price:
                matched_products.append(
                    {
                        "id": product["id"],
                        "name": product["name"],
                        "category": product["category"],
                        "price": product["price"],
                        "price_text": format_vnd(product["price"]),
                        "stock": product["stock"],
                        "weight": product["weight"],
                        "description": product["description"],
                    }
                )

    if not matched_products:
        return {
            "success": False,
            "message": f"No product found for query='{query}' with max_price={max_price}.",
            "products": [],
        }

    return {
        "success": True,
        "message": f"Found {len(matched_products)} product(s).",
        "products": matched_products,
    }


def check_stock(product_id: str, quantity: int = 1) -> Dict[str, Any]:
    """
    Check whether a product has enough stock.

    Args:
        product_id: Product ID, for example "P001".
        quantity: Desired quantity.

    Returns:
        Stock availability information.
    """
    product = find_product_by_id(product_id)

    if product is None:
        return {
            "success": False,
            "message": f"Product with id='{product_id}' not found.",
            "available": False,
        }

    if quantity <= 0:
        return {
            "success": False,
            "message": "Quantity must be greater than 0.",
            "available": False,
        }

    available = product["stock"] >= quantity

    return {
        "success": True,
        "product_id": product["id"],
        "product_name": product["name"],
        "requested_quantity": quantity,
        "current_stock": product["stock"],
        "available": available,
        "message": (
            f"Enough stock for {quantity} item(s)."
            if available
            else f"Not enough stock. Requested {quantity}, but only {product['stock']} available."
        ),
    }