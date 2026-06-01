from typing import Any, Dict

from src.data.fake_retail_data import COUPONS
from src.tools.utils import format_vnd


def apply_discount(price: float, coupon_code: str) -> Dict[str, Any]:
    """
    Apply a coupon code to a product price.

    Args:
        price: Original price in VND.
        coupon_code: Coupon code, for example "SALE10".

    Returns:
        Discount result.
    """
    if price < 0:
        return {
            "success": False,
            "message": "Price must be non-negative.",
            "original_price": price,
            "discount_amount": 0,
            "final_price": price,
        }

    coupon_code = coupon_code.strip().upper()

    if coupon_code not in COUPONS:
        return {
            "success": False,
            "message": f"Invalid coupon code: {coupon_code}.",
            "original_price": price,
            "discount_amount": 0,
            "final_price": price,
            "original_price_text": format_vnd(price),
            "final_price_text": format_vnd(price),
        }

    coupon = COUPONS[coupon_code]

    if coupon["type"] == "percent":
        discount_amount = price * coupon["value"]
        final_price = price - discount_amount

        return {
            "success": True,
            "coupon_code": coupon_code,
            "coupon_type": coupon["type"],
            "discount_rate": coupon["value"],
            "original_price": price,
            "discount_amount": discount_amount,
            "final_price": final_price,
            "original_price_text": format_vnd(price),
            "discount_amount_text": format_vnd(discount_amount),
            "final_price_text": format_vnd(final_price),
            "message": f"Coupon {coupon_code} applied successfully.",
        }

    if coupon["type"] == "shipping":
        return {
            "success": True,
            "coupon_code": coupon_code,
            "coupon_type": coupon["type"],
            "original_price": price,
            "discount_amount": 0,
            "final_price": price,
            "original_price_text": format_vnd(price),
            "final_price_text": format_vnd(price),
            "message": f"Coupon {coupon_code} is a shipping coupon, not a product price discount.",
        }

    return {
        "success": False,
        "message": f"Unsupported coupon type: {coupon['type']}.",
        "original_price": price,
        "discount_amount": 0,
        "final_price": price,
    }