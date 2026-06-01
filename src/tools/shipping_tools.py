from typing import Any, Dict, Optional

from src.data.fake_retail_data import COUPONS, SHIPPING_RATES
from src.tools.utils import format_vnd, normalize_text


def calculate_shipping(
    weight: float,
    destination: str,
    coupon_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calculate shipping fee based on package weight and destination.

    Args:
        weight: Package weight in kg.
        destination: Destination city/province.
        coupon_code: Optional coupon code, for example "FREESHIP".

    Returns:
        Shipping fee information.
    """
    if weight <= 0:
        return {
            "success": False,
            "message": "Weight must be greater than 0.",
            "shipping_fee": None,
        }

    destination_norm = normalize_text(destination)

    if destination_norm not in SHIPPING_RATES:
        return {
            "success": False,
            "message": f"Unsupported destination: {destination}.",
            "shipping_fee": None,
        }

    rate = SHIPPING_RATES[destination_norm]
    shipping_fee = rate["base_fee"] + weight * rate["fee_per_kg"]

    coupon_applied = False

    if coupon_code:
        coupon_code = coupon_code.strip().upper()
        coupon = COUPONS.get(coupon_code)

        if coupon and coupon["type"] == "shipping":
            shipping_fee = 0
            coupon_applied = True

    return {
        "success": True,
        "destination": destination,
        "weight": weight,
        "base_fee": rate["base_fee"],
        "fee_per_kg": rate["fee_per_kg"],
        "shipping_fee": shipping_fee,
        "shipping_fee_text": format_vnd(shipping_fee),
        "coupon_applied": coupon_applied,
        "message": "Shipping fee calculated successfully.",
    }