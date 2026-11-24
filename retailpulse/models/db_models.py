"""
SQLAlchemy ORM models for e-commerce retail data.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, ForeignKey, Boolean, Index
)
from sqlalchemy.orm import relationship
from retailpulse.core.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(200), nullable=False)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    signup_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.customer_id}: {self.name}>"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, unique=True)
    department = Column(String(100), nullable=True)

    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.category_id}: {self.name}>"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), unique=True, nullable=False, index=True)
    category_id = Column(String(50), ForeignKey("categories.category_id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")

    def __repr__(self):
        return f"<Product {self.product_id}: {self.name} (${self.price:.2f})>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    status = Column(String(30), nullable=False, default="completed")  # completed, cancelled, refunded
    total_amount = Column(Float, nullable=False)
    shipping_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_id}: ${self.total_amount:.2f} on {self.order_date}>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_item_id = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem {self.order_item_id}: Product {self.product_id} x {self.quantity}>"

# Compound indexes for fast analytical query performance
Index("idx_orders_date_status", Order.order_date, Order.status)
Index("idx_items_order_product", OrderItem.order_id, OrderItem.product_id)
