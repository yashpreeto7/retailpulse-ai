"""
Data Ingestion Pipeline: Ingests raw data, cleans, validates, and populates SQLite database.
"""
import json
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from retailpulse.config import DATA_DIR, RAW_DATA_DIR, DB_PATH
from retailpulse.core.database import engine, Base, SessionLocal
from retailpulse.core.logger import get_logger
from retailpulse.models.db_models import Customer, Category, Product, Order, OrderItem
from retailpulse.models.schemas import DataQualityReport
from retailpulse.data.generator import generate_raw_datasets
from retailpulse.data.cleaner import DataCleaner

logger = get_logger("retailpulse.ingestion")
REPORT_PATH = DATA_DIR / "data_quality_report.json"

def run_ingestion_pipeline(force_regenerate: bool = False) -> DataQualityReport:
    """
    Executes full ETL cycle:
    1. Checks/generates raw CSV source data
    2. Runs data cleaning and validation
    3. Recreates tables and seeds SQLite database
    4. Generates and stores DataQualityReport
    """
    logger.info("Starting Data Ingestion & ETL Pipeline...")
    
    # 1. Ensure raw datasets exist
    customers_csv = RAW_DATA_DIR / "raw_customers.csv"
    if force_regenerate or not customers_csv.exists():
        logger.info("Raw datasets not found or regenerate requested. Generating synthetic raw data...")
        generate_raw_datasets()

    # 2. Read raw CSVs
    df_raw_cust = pd.read_csv(RAW_DATA_DIR / "raw_customers.csv")
    df_raw_cat = pd.read_csv(RAW_DATA_DIR / "raw_categories.csv")
    df_raw_prod = pd.read_csv(RAW_DATA_DIR / "raw_products.csv")
    df_raw_orders = pd.read_csv(RAW_DATA_DIR / "raw_orders.csv")
    df_raw_items = pd.read_csv(RAW_DATA_DIR / "raw_order_items.csv")

    cleaner = DataCleaner()

    # 3. Clean datasets in relational dependency order
    df_cust = cleaner.clean_customers(df_raw_cust)
    df_cat = cleaner.clean_categories(df_raw_cat)
    df_prod = cleaner.clean_products(df_raw_prod)

    valid_customer_ids = set(df_cust["customer_id"])
    df_orders = cleaner.clean_orders(df_raw_orders, valid_customer_ids)

    valid_order_ids = set(df_orders["order_id"])
    valid_product_ids = set(df_prod["product_id"])
    df_items = cleaner.clean_order_items(df_raw_items, valid_order_ids, valid_product_ids)

    # 4. Initialize Database Schema
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 5. Populate SQLite in batches
    session = SessionLocal()
    try:
        # Load Categories
        for _, r in df_cat.iterrows():
            session.add(Category(
                category_id=r["category_id"],
                name=r["name"],
                department=r.get("department")
            ))
        session.flush()

        # Load Products
        for _, r in df_prod.iterrows():
            session.add(Product(
                product_id=r["product_id"],
                category_id=r["category_id"],
                name=r["name"],
                sku=r["sku"],
                price=float(r["price"]),
                cost=float(r["cost"]),
                stock_quantity=int(r["stock"]),
                is_active=True
            ))
        session.flush()

        # Load Customers
        for _, r in df_cust.iterrows():
            session.add(Customer(
                customer_id=r["customer_id"],
                name=r["name"],
                email=r["email"],
                city=r.get("city"),
                state=r.get("state"),
                signup_date=r["signup_date"],
                is_active=True
            ))
        session.flush()

        # Load Orders
        for _, r in df_orders.iterrows():
            session.add(Order(
                order_id=r["order_id"],
                customer_id=r["customer_id"],
                order_date=r["order_date"],
                status=r["status"],
                total_amount=float(r["total_amount"]),
                shipping_amount=float(r.get("shipping_amount", 0.0)),
                discount_amount=float(r.get("discount_amount", 0.0))
            ))
        session.flush()

        # Load Order Items
        for _, r in df_items.iterrows():
            session.add(OrderItem(
                order_item_id=r["order_item_id"],
                order_id=r["order_id"],
                product_id=r["product_id"],
                quantity=int(r["quantity"]),
                unit_price=float(r["unit_price"]),
                subtotal=float(r["subtotal"])
            ))
        session.commit()
        logger.info("Successfully committed all cleaned records into SQLite database.")

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to populate database: {e}")
        raise
    finally:
        session.close()

    # 6. Save Data Quality Report
    report = cleaner.get_report()
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2)

    logger.info(f"ETL completed: {report.records_loaded} records loaded from {report.total_raw_records} raw records.")
    logger.info(f"Quality: {report.duplicates_removed} duplicates removed, {report.missing_values_handled} missing values fixed.")
    return report

def get_latest_quality_report() -> DataQualityReport | None:
    if REPORT_PATH.exists():
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return DataQualityReport(**data)
    return None

if __name__ == "__main__":
    run_ingestion_pipeline(force_regenerate=True)
