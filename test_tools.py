from src.tools import (
    apply_discount,
    calculate_shipping,
    calculator,
    check_stock,
    get_tool_names,
    get_tools_description,
    search_product,
)


def main():
    print("=== Available tools ===")
    print(get_tool_names())

    print("\n=== Tools description ===")
    print(get_tools_description())

    print("\n=== Test search_product ===")
    print(search_product(query="laptop", max_price=20_000_000))

    print("\n=== Test check_stock ===")
    print(check_stock(product_id="P001", quantity=2))

    print("\n=== Test apply_discount ===")
    print(apply_discount(price=15_500_000 * 2, coupon_code="SALE10"))

    print("\n=== Test calculate_shipping ===")
    print(calculate_shipping(weight=1.7 * 2, destination="Hà Nội"))

    print("\n=== Test calculator ===")
    print(calculator("15500000 * 2 * 0.9 + 52200"))


if __name__ == "__main__":
    main()