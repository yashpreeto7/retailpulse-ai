"""
Tests for Data Cleaning, Deduplication, and Validation Pipeline.
"""
import pytest
import pandas as pd
from datetime import date
from retailpulse.data.cleaner import DataCleaner

def test_cleaner_deduplication():
    cleaner = DataCleaner()
    df_raw = pd.DataFrame([
        {"customer_id": "CUST_001", "name": "Alice Smith ", "email": "alice@test.com", "city": "NYC", "state": "NY", "signup_date": "2024-01-01"},
        {"customer_id": "CUST_001", "name": "Alice Smith", "email": "alice@test.com", "city": "NYC", "state": "NY", "signup_date": "2024-01-01"}, # duplicate
        {"customer_id": "CUST_002", "name": "Bob Jones", "email": "bob@test.com", "city": "LA", "state": "CA", "signup_date": "2024-01-02"}
    ])

    df_clean = cleaner.clean_customers(df_raw)
    assert len(df_clean) == 2
    assert cleaner.duplicates_removed == 1
    assert df_clean.iloc[0]["name"] == "Alice Smith" # trimmed

def test_cleaner_missing_values_and_subtotal_repair():
    cleaner = DataCleaner()
    valid_orders = {"ORD_001", "ORD_002"}
    valid_products = {"PROD_001"}

    df_items = pd.DataFrame([
        {"order_item_id": "ITEM_001", "order_id": "ORD_001", "product_id": "PROD_001", "quantity": 2, "unit_price": 50.0, "subtotal": None},
        {"order_item_id": "ITEM_002", "order_id": "ORD_002", "product_id": "PROD_001", "quantity": 3, "unit_price": 10.0, "subtotal": 0.0},
        {"order_item_id": "ITEM_003", "order_id": "ORD_999", "product_id": "PROD_001", "quantity": 1, "unit_price": 10.0, "subtotal": 10.0} # orphan order
    ])

    df_clean = cleaner.clean_order_items(df_items, valid_orders, valid_products)
    assert len(df_clean) == 2
    assert cleaner.missing_values_handled == 2
    assert df_clean.loc[df_clean["order_item_id"] == "ITEM_001", "subtotal"].iloc[0] == 100.0
    assert df_clean.loc[df_clean["order_item_id"] == "ITEM_002", "subtotal"].iloc[0] == 30.0

def test_data_quality_report():
    cleaner = DataCleaner()
    df_cust = pd.DataFrame([
        {"customer_id": "C_1", "name": "John", "email": None, "city": "Austin", "state": "TX", "signup_date": "2024-02-01"}
    ])
    cleaner.clean_customers(df_cust)
    report = cleaner.get_report()
    assert report.total_raw_records == 1
    assert report.missing_values_handled == 1
    assert report.clean_pct == 100.0
