import sqlalchemy as sql
import sqlalchemy.orm as orm
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timedelta
from hashlib import sha256
from typing import List

engine = sql.create_engine('sqlite:///database.db')
session = orm.Session(bind=engine)

Base = orm.declarative_base()
metadata: sql.MetaData = Base.metadata

orders_products_junction = sql.Table("orders_products_junction_table", Base.metadata, 
    sql.Column("order_id", sql.ForeignKey("orders.id"), primary_key=True),
    sql.Column("product_id", sql.ForeignKey("products.id"), primary_key=True))

class User(Base):
    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    registered_at: orm.Mapped[datetime] = orm.mapped_column(sql.DateTime(), default=datetime.now)

    username: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False, unique=True)
    _email: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False, unique=True, name="email")
    _password_hash: orm.Mapped[str] = orm.mapped_column(sql.String(64), nullable=False, name="password_hash")

    name: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=True)
    role: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False, default="user")

    orders: orm.Mapped[List["Order"]] = orm.relationship("Order", back_populates="user", cascade="all, delete-orphan")
    cart_items: orm.Mapped[List["CartItem"]] = orm.relationship("CartItem", back_populates="user", cascade="all, delete-orphan")

    @hybrid_property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if "@" not in value:
            raise ValueError("wrong email")
        self._email = value.lower()

    @hybrid_property
    def password(self) -> str:
        return self._password_hash

    @password.setter
    def password(self, value: str) -> None:
        self._password_hash = sha256(value.encode("utf-8")).hexdigest()

    def is_password(self, password_check: str) -> bool:
        check_hash = sha256(password_check.encode("utf-8")).hexdigest()
        return check_hash == self._password_hash


class Category(Base):
    __tablename__ = "categories"

    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=True)
    slug: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False, unique=True)

    products: orm.Mapped[List["Product"]] = orm.relationship("Product", back_populates="category", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=True)
    price: orm.Mapped[float] = orm.mapped_column(sql.Numeric(10, 2), nullable=False)
    stock: orm.Mapped[int] = orm.mapped_column(sql.Integer, nullable=False, default=0)
    image: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=True)

    category_id: orm.Mapped[int] = orm.mapped_column(sql.Integer, sql.ForeignKey("categories.id"), nullable=True)
    category: orm.Mapped["Category"] = orm.relationship("Category", back_populates="products")

    cart_items: orm.Mapped[List["CartItem"]] = orm.relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items: orm.Mapped[List["OrderItem"]] = orm.relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    user_id: orm.Mapped[int] = orm.mapped_column(sql.Integer, sql.ForeignKey("users.id"), nullable=False)
    product_id: orm.Mapped[int] = orm.mapped_column(sql.Integer, sql.ForeignKey("products.id"), nullable=False)
    quantity: orm.Mapped[int] = orm.mapped_column(sql.Integer, nullable=False, default=1)

    user: orm.Mapped["User"] = orm.relationship("User", back_populates="cart_items")
    product: orm.Mapped["Product"] = orm.relationship("Product", back_populates="cart_items")


class Order(Base):
    __tablename__ = "orders"

    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    user_id: orm.Mapped[int] = orm.mapped_column(sql.Integer, sql.ForeignKey("users.id"), nullable=False)

    status: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False, default="pending")
    total: orm.Mapped[float] = orm.mapped_column(sql.Numeric(12, 2), nullable=False, default=0.0)
    created_at: orm.Mapped[datetime] = orm.mapped_column(sql.DateTime(), default=datetime.now)

    user: orm.Mapped["User"] = orm.relationship("User", back_populates="orders")
    items: orm.Mapped[List["OrderItem"]] = orm.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    order_id: orm.Mapped[int] = orm.mapped_column(sql.Integer, sql.ForeignKey("orders.id"), nullable=False)
    product_id: orm.Mapped[int] = orm.mapped_column(sql.Integer, sql.ForeignKey("products.id"), nullable=False)

    price: orm.Mapped[float] = orm.mapped_column(sql.Numeric(10, 2), nullable=False)
    quantity: orm.Mapped[int] = orm.mapped_column(sql.Integer, nullable=False, default=1)

    order: orm.Mapped["Order"] = orm.relationship("Order", back_populates="items")
    product: orm.Mapped["Product"] = orm.relationship("Product", back_populates="order_items")

metadata.create_all(engine)