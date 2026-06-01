PRODUCTS = [
    {
        "id": "P001",
        "name": "Laptop Acer Aspire 5",
        "category": "laptop",
        "price": 15_500_000,
        "stock": 5,
        "weight": 1.7,
        "description": "Laptop văn phòng, phù hợp học tập và làm việc cơ bản.",
    },
    {
        "id": "P002",
        "name": "MacBook Air M2",
        "category": "laptop",
        "price": 24_500_000,
        "stock": 2,
        "weight": 1.24,
        "description": "Laptop mỏng nhẹ, hiệu năng tốt, pin lâu.",
    },
    {
        "id": "P003",
        "name": "iPhone 15",
        "category": "phone",
        "price": 18_990_000,
        "stock": 8,
        "weight": 0.2,
        "description": "Điện thoại Apple iPhone 15 128GB.",
    },
    {
        "id": "P004",
        "name": "Samsung Galaxy S24",
        "category": "phone",
        "price": 16_990_000,
        "stock": 0,
        "weight": 0.19,
        "description": "Điện thoại Samsung flagship, hiện đang hết hàng.",
    },
    {
        "id": "P005",
        "name": "Tai nghe Sony WH-1000XM5",
        "category": "headphone",
        "price": 7_500_000,
        "stock": 10,
        "weight": 0.25,
        "description": "Tai nghe chống ồn cao cấp.",
    },
]


COUPONS = {
    "SALE10": {
        "type": "percent",
        "value": 0.10,
        "description": "Giảm 10% cho mọi đơn hàng.",
    },
    "STUDENT5": {
        "type": "percent",
        "value": 0.05,
        "description": "Giảm 5% cho học sinh, sinh viên.",
    },
    "FREESHIP": {
        "type": "shipping",
        "value": 1.0,
        "description": "Miễn phí vận chuyển.",
    },
}


SHIPPING_RATES = {
    "ha noi": {
        "base_fee": 25_000,
        "fee_per_kg": 8_000,
    },
    "hà nội": {
        "base_fee": 25_000,
        "fee_per_kg": 8_000,
    },
    "ho chi minh": {
        "base_fee": 30_000,
        "fee_per_kg": 10_000,
    },
    "hồ chí minh": {
        "base_fee": 30_000,
        "fee_per_kg": 10_000,
    },
    "da nang": {
        "base_fee": 28_000,
        "fee_per_kg": 9_000,
    },
    "đà nẵng": {
        "base_fee": 28_000,
        "fee_per_kg": 9_000,
    },
}