"""
Data Cleaning, Validation, and Standardization Pipeline.
"""
from datetime import datetime, date
import pandas as pd
from retailpulse.core.logger import get_logger
from retailpulse.models.schemas import DataQualityReport

logger = get_logger("retailpulse.cleaner")

class DataCleaner:
    def __init__(self):
        self.duplicates_removed = 0
        self.missing_values_handled = 0
        self.total_raw_records = 0
        self.records_loaded = 0
        self.issues_detected: list[str] = []

    def clean_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        raw_count = len(df)
        self.total_raw_records += raw_count
        
        # 1. Deduplicate by customer_id or exact rows
        df_clean = df.drop_duplicates(subset=["customer_id"], keep="first").copy()
        dups = raw_count - len(df_clean)
        if dups > 0:
            self.duplicates_removed += dups
            self.issues_detected.append(f"Removed {dups} duplicate customer records")

        # 2. Trim string whitespace
        for col in ["name", "email", "city", "state"]:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.strip()
                df_clean[col] = df_clean[col].replace({"nan": None, "None": None, "": None})

        # 3. Handle missing emails
        missing_emails = df_clean["email"].isna().sum()
        if missing_emails > 0:
            self.missing_values_handled += missing_emails
            self.issues_detected.append(f"Imputed {missing_emails} missing customer emails with fallback format")
            df_clean["email"] = df_clean.apply(
                lambda r: f"user_{r['customer_id'].lower()}@unverified.retailpulse.com" if pd.isna(r["email"]) else r["email"],
                axis=1
            )

        # 4. Handle missing city/state
        df_clean["city"] = df_clean["city"].fillna("Unknown")
        df_clean["state"] = df_clean["state"].fillna("NA")

        # 5. Parse signup_date
        df_clean["signup_date"] = pd.to_datetime(df_clean["signup_date"]).dt.date
        
        self.records_loaded += len(df_clean)
        return df_clean

    def clean_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        raw_count = len(df)
        self.total_raw_records += raw_count
        
        df_clean = df.drop_duplicates(subset=["category_id"], keep="first").copy()
        dups = raw_count - len(df_clean)
        if dups > 0:
            self.duplicates_removed += dups
            self.issues_detected.append(f"Removed {dups} duplicate category records")

        df_clean["name"] = df_clean["name"].astype(str).str.strip()
        df_clean["department"] = df_clean["department"].astype(str).str.strip()
        
        self.records_loaded += len(df_clean)
        return df_clean

    def clean_products(self, df: pd.DataFrame) -> pd.DataFrame:
        raw_count = len(df)
        self.total_raw_records += raw_count
        
        # 1. Deduplicate
        df_clean = df.drop_duplicates(subset=["product_id"], keep="first").copy()
        dups = raw_count - len(df_clean)
        if dups > 0:
            self.duplicates_removed += dups
            self.issues_detected.append(f"Removed {dups} duplicate product records")

        # 2. String trimming
        for col in ["name", "sku", "category_id"]:
            df_clean[col] = df_clean[col].astype(str).str.strip()

        # 3. Numeric bounds & types
        df_clean["price"] = pd.to_numeric(df_clean["price"], errors="coerce")
        df_clean["cost"] = pd.to_numeric(df_clean["cost"], errors="coerce")
        df_clean["stock"] = pd.to_numeric(df_clean["stock"], errors="coerce").fillna(0).astype(int)

        # Filter out invalid prices if any
        invalid_prices = (df_clean["price"] <= 0) | df_clean["price"].isna()
        if invalid_prices.any():
            self.issues_detected.append(f"Flagged {invalid_prices.sum()} products with invalid price")
            df_clean = df_clean[~invalid_prices]

        self.records_loaded += len(df_clean)
        return df_clean

    def clean_orders(self, df: pd.DataFrame, valid_customer_ids: set[str]) -> pd.DataFrame:
        raw_count = len(df)
        self.total_raw_records += raw_count

        # 1. Deduplicate by order_id
        df_clean = df.drop_duplicates(subset=["order_id"], keep="first").copy()
        dups = raw_count - len(df_clean)
        if dups > 0:
            self.duplicates_removed += dups
            self.issues_detected.append(f"Removed {dups} duplicate order records")

        # 2. Foreign Key validation (Customer exists)
        orphan_orders = ~df_clean["customer_id"].isin(valid_customer_ids)
        if orphan_orders.any():
            count = orphan_orders.sum()
            self.issues_detected.append(f"Removed {count} orphan orders referencing nonexistent customers")
            df_clean = df_clean[~orphan_orders]

        # 3. Standardize dates
        df_clean["order_date"] = pd.to_datetime(df_clean["order_date"]).dt.date

        # 4. Standardize numeric columns
        df_clean["total_amount"] = pd.to_numeric(df_clean["total_amount"], errors="coerce").round(2)
        df_clean["shipping_amount"] = pd.to_numeric(df_clean["shipping_amount"], errors="coerce").fillna(0.0).round(2)
        df_clean["discount_amount"] = pd.to_numeric(df_clean["discount_amount"], errors="coerce").fillna(0.0).round(2)

        # 5. Status validation
        valid_statuses = {"completed", "cancelled", "refunded"}
        df_clean["status"] = df_clean["status"].astype(str).str.strip().str.lower()
        df_clean.loc[~df_clean["status"].isin(valid_statuses), "status"] = "completed"

        self.records_loaded += len(df_clean)
        return df_clean

    def clean_order_items(self, df: pd.DataFrame, valid_order_ids: set[str], valid_product_ids: set[str]) -> pd.DataFrame:
        raw_count = len(df)
        self.total_raw_records += raw_count

        # 1. Deduplicate by order_item_id
        df_clean = df.drop_duplicates(subset=["order_item_id"], keep="first").copy()
        dups = raw_count - len(df_clean)
        if dups > 0:
            self.duplicates_removed += dups
            self.issues_detected.append(f"Removed {dups} duplicate order item records")

        # 2. Foreign Key validation
        valid_mask = df_clean["order_id"].isin(valid_order_ids) & df_clean["product_id"].isin(valid_product_ids)
        orphans = (~valid_mask).sum()
        if orphans > 0:
            self.issues_detected.append(f"Filtered {orphans} order items with invalid order_id or product_id")
            df_clean = df_clean[valid_mask]

        # 3. Numeric conversion and subtotal computation/repair
        df_clean["quantity"] = pd.to_numeric(df_clean["quantity"], errors="coerce").fillna(1).astype(int)
        df_clean["unit_price"] = pd.to_numeric(df_clean["unit_price"], errors="coerce").round(2)

        # Handle missing or mismatched subtotals
        expected_subtotal = (df_clean["quantity"] * df_clean["unit_price"]).round(2)
        missing_subtotals = df_clean["subtotal"].isna() | (df_clean["subtotal"] <= 0)
        if missing_subtotals.any():
            fixed_count = missing_subtotals.sum()
            self.missing_values_handled += fixed_count
            self.issues_detected.append(f"Computed and repaired {fixed_count} missing subtotals")
            df_clean["subtotal"] = expected_subtotal
        else:
            df_clean["subtotal"] = pd.to_numeric(df_clean["subtotal"]).round(2)

        self.records_loaded += len(df_clean)
        return df_clean

    def get_report(self) -> DataQualityReport:
        clean_pct = round((self.records_loaded / self.total_raw_records * 100), 2) if self.total_raw_records > 0 else 100.0
        return DataQualityReport(
            total_raw_records=self.total_raw_records,
            duplicates_removed=self.duplicates_removed,
            missing_values_handled=self.missing_values_handled,
            records_loaded=self.records_loaded,
            clean_pct=clean_pct,
            issues_detected=self.issues_detected
        )
