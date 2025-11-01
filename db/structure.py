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
    registred_at: orm.Mapped[datetime] = orm.mapped_column(sql.DateTime(), default=datetime.now)

    username: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False, unique=True)
    _email: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False, unique=True, name="email")
    _password_hash: orm.Mapped[str] = orm.mapped_column(sql.String(64), nullable=False, name="password_hash")
    
    orders: orm.Mapped[List["Order"]] = orm.relationship(back_populates="user")
    
    @hybrid_property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if "@" not in value:
            raise ValueError("wrong email")
        self._email = value.lower()
    
    @hybrid_property
    def password(self):
        return self._password_hash
    
    @password.setter
    def password(self, value: str):
        '''
        value - password, NOT password hash
        '''
        self._password_hash = sha256(value.encode("utf-8")).hexdigest()
        
    def is_password(self, password_check: str):
        check_hash = sha256(password_check.encode("utf-8")).hexdigest()
        return check_hash == self._password_hash

import secrets

def generate_hex_token(length: int) -> str:
    return secrets.token_hex(length // 2)

class Token(Base):
    __tablename__ = "tokens"
    
    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    
    string: orm.Mapped[str] = orm.mapped_column(sql.String(32), nullable=False, default=generate_hex_token(32))
    user_id: orm.Mapped[int] = orm.mapped_column(sql.Integer, nullable=False)
    
    created_at: orm.Mapped[datetime] = orm.mapped_column(sql.DateTime(), default=datetime.now)
    expires_at: orm.Mapped[datetime] = orm.mapped_column(sql.DateTime(), default=lambda: datetime.now() + timedelta(hours=24))
    
    is_active: orm.Mapped[bool] = orm.mapped_column(sql.Boolean, nullable=False, default=True)
    
class Product(Base):
    __tablename__ = "products"

    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    
    name: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sql.Text)
    price: orm.Mapped[float] = orm.mapped_column(sql.Float, nullable=False, default=0)
    
    orders: orm.Mapped[List["Order"]] = orm.relationship(secondary=orders_products_junction, back_populates="products")
     
class Order(Base):
    __tablename__ = "orders"
    
    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    
    products: orm.Mapped[List["Product"]] = orm.relationship(secondary=orders_products_junction, back_populates="orders")
    
    _user_id: orm.Mapped[int] = orm.mapped_column(sql.ForeignKey("users.id"))
    user: orm.Mapped["User"] = orm.relationship(back_populates="orders")


metadata.create_all(engine)