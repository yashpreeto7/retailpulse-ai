"""
Realistic e-commerce dataset generator with intentional dirty records for cleaning pipeline.
"""
import random
from datetime import datetime, date, timedelta
import pandas as pd
from retailpulse.config import RAW_DATA_DIR
from retailpulse.core.logger import get_logger

logger = get_logger("retailpulse.generator")

# Set deterministic seed for reproducible benchmarking
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

CATEGORIES = [
    {"category_id": "CAT_ELEC", "name": "Electronics", "department": "Technology"},
    {"category_id": "CAT_APP", "name": "Apparel", "department": "Fashion"},
    {"category_id": "CAT_HOME", "name": "Home & Kitchen", "department": "Living"},
    {"category_id": "CAT_FIT", "name": "Fitness & Outdoor", "department": "Sports"},
    {"category_id": "CAT_BEAU", "name": "Beauty & Personal Care", "department": "Personal Care"},
]

PRODUCTS = [
    # Electronics
    {"product_id": "PROD_001", "category_id": "CAT_ELEC", "name": "Ultra Wireless Noise-Cancelling Headphones", "sku": "ELC-NC-001", "price": 299.99, "cost": 140.00, "stock": 45},
    {"product_id": "PROD_002", "category_id": "CAT_ELEC", "name": "Pro 4K Gaming & Workstation Monitor", "sku": "ELC-4K-002", "price": 549.99, "cost": 290.00, "stock": 18},
    {"product_id": "PROD_003", "category_id": "CAT_ELEC", "name": "Mechanical Keyboard with RGB Backlight", "sku": "ELC-KB-003", "price": 129.99, "cost": 55.00, "stock": 80},
    {"product_id": "PROD_004", "category_id": "CAT_ELEC", "name": "Smart Fitness Watch Series 5", "sku": "ELC-SW-004", "price": 219.99, "cost": 95.00, "stock": 60},
    {"product_id": "PROD_005", "category_id": "CAT_ELEC", "name": "USB-C Fast Charging Hub 7-in-1", "sku": "ELC-HB-005", "price": 49.99, "cost": 18.00, "stock": 150},
    
    # Apparel
    {"product_id": "PROD_006", "category_id": "CAT_APP", "name": "Premium Heavyweight Cotton Hoodie", "sku": "APP-HD-006", "price": 89.99, "cost": 32.00, "stock": 120},
    {"product_id": "PROD_007", "category_id": "CAT_APP", "name": "Classic Stretch Denim Jacket", "sku": "APP-DJ-007", "price": 119.99, "cost": 48.00, "stock": 75},
    {"product_id": "PROD_008", "category_id": "CAT_APP", "name": "Breathable Performance Running Tee", "sku": "APP-RT-008", "price": 38.99, "cost": 12.00, "stock": 200},
    {"product_id": "PROD_009", "category_id": "CAT_APP", "name": "Water-Resistant All-Weather Parka", "sku": "APP-PK-009", "price": 199.99, "cost": 85.00, "stock": 40},
    {"product_id": "PROD_010", "category_id": "CAT_APP", "name": "Merino Wool Thermal Socks 3-Pack", "sku": "APP-SK-010", "price": 24.99, "cost": 7.50, "stock": 300},

    # Home & Kitchen
    {"product_id": "PROD_011", "category_id": "CAT_HOME", "name": "Artisan Compact Espresso Machine", "sku": "HOM-ESP-011", "price": 449.99, "cost": 210.00, "stock": 30},
    {"product_id": "PROD_012", "category_id": "CAT_HOME", "name": "Digital XL Air Fryer with Crisper", "sku": "HOM-AF-012", "price": 139.99, "cost": 62.00, "stock": 65},
    {"product_id": "PROD_013", "category_id": "CAT_HOME", "name": "Non-Stick Ceramic Cookware Set 10-Piece", "sku": "HOM-CK-013", "price": 249.99, "cost": 115.00, "stock": 35},
    {"product_id": "PROD_014", "category_id": "CAT_HOME", "name": "High-Speed Vortex Countertop Blender", "sku": "HOM-BL-014", "price": 99.99, "cost": 42.00, "stock": 90},
    {"product_id": "PROD_015", "category_id": "CAT_HOME", "name": "Smart Temperature Electric Kettle", "sku": "HOM-KT-015", "price": 69.99, "cost": 28.00, "stock": 110},

    # Fitness & Outdoor
    {"product_id": "PROD_016", "category_id": "CAT_FIT", "name": "High-Density Eco Yoga Mat", "sku": "FIT-YM-016", "price": 45.99, "cost": 16.00, "stock": 140},
    {"product_id": "PROD_017", "category_id": "CAT_FIT", "name": "Quick-Lock Adjustable Dumbbells Pair", "sku": "FIT-DB-017", "price": 329.99, "cost": 160.00, "stock": 25},
    {"product_id": "PROD_018", "category_id": "CAT_FIT", "name": "Insulated Stainless Steel Bottle 32oz", "sku": "FIT-WB-018", "price": 34.99, "cost": 11.00, "stock": 220},
    {"product_id": "PROD_019", "category_id": "CAT_FIT", "name": "Compact Folding Rowing Machine", "sku": "FIT-RW-019", "price": 599.99, "cost": 310.00, "stock": 15},

    # Beauty & Personal Care
    {"product_id": "PROD_020", "category_id": "CAT_BEAU", "name": "Hydrating Hyaluronic Acid Facial Serum", "sku": "BEA-SR-020", "price": 42.00, "cost": 12.00, "stock": 180},
    {"product_id": "PROD_021", "category_id": "CAT_BEAU", "name": "Ionic Salon Hair Dryer with Diffuser", "sku": "BEA-HD-021", "price": 119.99, "cost": 50.00, "stock": 70},
    {"product_id": "PROD_022", "category_id": "CAT_BEAU", "name": "Sonic Electric Toothbrush with Travel Case", "sku": "BEA-TB-022", "price": 79.99, "cost": 30.00, "stock": 100},
    
    # Low-performing / stagnant products (for testing product analytics)
    {"product_id": "PROD_023", "category_id": "CAT_APP", "name": "Vintage Corduroy Bucket Hat", "sku": "APP-BH-023", "price": 28.00, "cost": 10.00, "stock": 95},
    {"product_id": "PROD_024", "category_id": "CAT_HOME", "name": "Cast Iron Bacon Press", "sku": "HOM-BP-024", "price": 19.99, "cost": 8.00, "stock": 120},
]

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"), ("Houston", "TX"),
    ("Phoenix", "AZ"), ("Philadelphia", "PA"), ("San Antonio", "TX"), ("San Diego", "CA"),
    ("Dallas", "TX"), ("Austin", "TX"), ("Seattle", "WA"), ("Denver", "CO"),
    ("Boston", "MA"), ("Atlanta", "GA"), ("San Francisco", "CA")
]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"
]

def generate_raw_datasets():
    """Generates synthetic data and writes raw CSVs with realistic dirty records."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Customers
    num_customers = 160
    customers = []
    start_date = date(2023, 10, 1)
    
    for i in range(1, num_customers + 1):
        cid = f"CUST_{i:04d}"
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        name = f"{fname} {lname}"
        city, state = random.choice(CITIES)
        signup = start_date + timedelta(days=random.randint(0, 360))
        email = f"{fname.lower()}.{lname.lower()}{random.randint(10, 99)}@example.com"
        
        customers.append({
            "customer_id": cid,
            "name": name,
            "email": email,
            "city": city,
            "state": state,
            "signup_date": signup.isoformat()
        })
    
    # Add dirty customer records (duplicates, missing email, trailing whitespace)
    customers.append({
        "customer_id": "CUST_0012",
        "name": customers[11]["name"] + " ",
        "email": customers[11]["email"],
        "city": customers[11]["city"],
        "state": customers[11]["state"],
        "signup_date": customers[11]["signup_date"]
    })  # Duplicate
    customers.append({
        "customer_id": "CUST_0161",
        "name": "Jane MissingEmail",
        "email": None,  # Missing email
        "city": "Chicago",
        "state": "IL",
        "signup_date": "2024-03-15"
    })
    
    df_customers = pd.DataFrame(customers)
    df_customers.to_csv(RAW_DATA_DIR / "raw_customers.csv", index=False)
    
    # 2. Categories & Products
    df_categories = pd.DataFrame(CATEGORIES)
    df_categories.to_csv(RAW_DATA_DIR / "raw_categories.csv", index=False)
    
    df_products = pd.DataFrame(PRODUCTS)
    # Add dirty product record
    dirty_prod = df_products.iloc[0].to_dict()
    df_products = pd.concat([df_products, pd.DataFrame([dirty_prod])], ignore_index=True)  # Duplicate
    df_products.to_csv(RAW_DATA_DIR / "raw_products.csv", index=False)
    
    # 3. Orders & Order Items (12-month period: 2023-11 to 2024-10)
    # Baseline months: Nov 2023 to Sep 2024 with steady growth (~$40k - $65k/mo)
    # Target month: Oct 2024 with deliberate ~22% revenue decline driven by Electronics stockout
    months = [
        ("2023-11", 65, 1.0),
        ("2023-12", 95, 1.3),  # Holiday bump
        ("2024-01", 60, 0.9),
        ("2024-02", 68, 1.0),
        ("2024-03", 75, 1.1),
        ("2024-04", 80, 1.15),
        ("2024-05", 85, 1.2),
        ("2024-06", 90, 1.25),
        ("2024-07", 95, 1.3),
        ("2024-08", 100, 1.35),
        ("2024-09", 110, 1.45), # Peak baseline month: ~110 orders
        ("2024-10", 85, 1.15)   # Target decline month: orders drop to 85, and Electronics drop heavily
    ]
    
    orders = []
    order_items = []
    order_counter = 1
    item_counter = 1
    
    # Define cohort pools: Active cohort vs Inactive cohort
    # We will reserve ~25 customers who only bought in 2023 or early 2024 and haven't bought in last 90 days
    inactive_customer_ids = [f"CUST_{i:04d}" for i in range(1, 26)]
    active_customer_ids = [f"CUST_{i:04d}" for i in range(26, num_customers + 1)]
    
    for month_str, target_order_count, multiplier in months:
        year, month = map(int, month_str.split("-"))
        days_in_month = 30 if month in [4, 6, 9, 11] else (28 if month == 2 else 31)
        
        for _ in range(target_order_count):
            order_id = f"ORD_{order_counter:05d}"
            order_day = random.randint(1, days_in_month)
            order_date = date(year, month, order_day)
            
            # Select customer
            if month_str in ["2023-11", "2023-12", "2024-01", "2024-02"] and random.random() < 0.35:
                cust_id = random.choice(inactive_customer_ids)
            else:
                cust_id = random.choice(active_customer_ids)
                
            # Number of items in order
            num_items = random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0]
            
            # Category selection bias:
            # In Oct 2024 (2024-10), Electronics are heavily suppressed (stockout of PROD_001, PROD_002)
            if month_str == "2024-10":
                avail_products = [p for p in PRODUCTS if p["product_id"] not in ["PROD_001", "PROD_002"]]
                # Lower quantity / basket size
            else:
                avail_products = PRODUCTS
                
            selected_products = random.sample(avail_products, min(num_items, len(avail_products)))
            order_total = 0.0
            
            for prod in selected_products:
                item_id = f"ITEM_{item_counter:06d}"
                qty = random.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]
                price = prod["price"]
                subtotal = round(qty * price, 2)
                order_total += subtotal
                
                order_items.append({
                    "order_item_id": item_id,
                    "order_id": order_id,
                    "product_id": prod["product_id"],
                    "quantity": qty,
                    "unit_price": price,
                    "subtotal": subtotal
                })
                item_counter += 1
            
            # Shipping & discount
            shipping = 9.99 if order_total < 100 else 0.0
            discount = round(order_total * 0.1, 2) if random.random() < 0.2 else 0.0
            final_total = round(order_total + shipping - discount, 2)
            
            # 96% completed, 4% cancelled
            status = "completed" if random.random() < 0.96 else "cancelled"
            
            orders.append({
                "order_id": order_id,
                "customer_id": cust_id,
                "order_date": order_date.isoformat(),
                "status": status,
                "total_amount": final_total,
                "shipping_amount": shipping,
                "discount_amount": discount
            })
            order_counter += 1

    # Inject dirty order items (duplicate row, mismatched subtotal)
    order_items.append(order_items[0].copy()) # Duplicate
    order_items.append({
        "order_item_id": "ITEM_999999",
        "order_id": orders[0]["order_id"],
        "product_id": "PROD_003",
        "quantity": 2,
        "unit_price": 129.99,
        "subtotal": None # Missing subtotal (to be computed)
    })
    
    # Inject dirty order (duplicate order_id, whitespace)
    dirty_order = orders[5].copy()
    orders.append(dirty_order)
    
    df_orders = pd.DataFrame(orders)
    df_orders.to_csv(RAW_DATA_DIR / "raw_orders.csv", index=False)
    
    df_order_items = pd.DataFrame(order_items)
    df_order_items.to_csv(RAW_DATA_DIR / "raw_order_items.csv", index=False)
    
    logger.info(f"Raw datasets successfully generated at {RAW_DATA_DIR}:")
    logger.info(f" - Customers: {len(df_customers)}")
    logger.info(f" - Products: {len(df_products)}")
    logger.info(f" - Orders: {len(df_orders)}")
    logger.info(f" - Order Items: {len(df_order_items)}")

if __name__ == "__main__":
    generate_raw_datasets()
