from datetime import datetime, timedelta

from sqlalchemy.orm import sessionmaker

from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from .structure import *

JWT_SECRET = "YOUR_SECRET_KEY"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Auth:
    def __init__(self):
        pass

    def hash_password(self, password: str) -> str:
        from hashlib import sha256
        return sha256(password.encode("utf8")).hexdigest()

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self.hash_password(plain) == hashed

    def create_token(self, user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": str(user_id), "exp": expire}
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def decode_token(self, token: str) -> int:
        from jose import JWTError
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return int(payload.get("sub"))
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

class Users:
    def get(self, username: str = None, email: str = None) -> User | Exception:
        session = SessionLocal()
        try:
            if username:
                user = session.query(User).filter(User.username == username).one()
            elif email:
                user = session.query(User).filter(User.email == email).one()
            else:
                return Exception("No filter provided")
            return user
        except Exception as e:
            return e
        finally:
            session.close()

    def register(self, username: str, password: str, email: str):
        session = SessionLocal()
        try:
            auth = Auth()
            new_user = User(username=username, email=email)
            new_user.password = password  # will hash inside setter
            session.add(new_user)
            session.commit()
            return new_user
        except Exception as e:
            session.rollback()
            return e
        finally:
            session.close()

    def login(self, email: str, password: str) -> str | Exception:
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.email == email).first()
            if not user or not Auth().verify_password(password, user.password):
                raise Exception("Invalid credentials")
            token = Auth().create_token(user.id)
            return token
        except Exception as e:
            return e
        finally:
            session.close()

    def get_current(self, token: str = Depends(oauth2_scheme)) -> User:
        user_id = Auth().decode_token(token)
        session = SessionLocal()
        user = session.query(User).get(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user


class Catalog:
    def list_categories(self):
        session = SessionLocal()
        cats = session.query(Category).all()
        session.close()
        return cats

    def create_category(self, name: str, description: str, slug: str):
        session = SessionLocal()
        try:
            cat = Category(name=name, description=description, slug=slug)
            session.add(cat)
            session.commit()
            return cat
        except Exception as e:
            session.rollback()
            return e
        finally:
            session.close()

    def list_products(self):
        session = SessionLocal()
        products = session.query(Product).all()
        session.close()
        return products

    def get_product(self, pid: int):
        session = SessionLocal()
        product = session.query(Product).get(pid)
        session.close()
        return product

    def create_product(self, **kwargs):
        session = SessionLocal()
        try:
            product = Product(**kwargs)
            session.add(product)
            session.commit()
            return product
        except Exception as e:
            session.rollback()
            return e
        finally:
            session.close()

class Cart:
    def view(self, user_id: int):
        session = SessionLocal()
        items = session.query(CartItem).filter(CartItem.user_id == user_id).all()
        session.close()
        return items

    def add_item(self, user_id: int, product_id: int, quantity: int):
        session = SessionLocal()
        try:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            session.add(item)
            session.commit()
            return item
        except Exception as e:
            session.rollback()
            return e
        finally:
            session.close()

class Orders:
    def place(self, user_id: int):
        session = SessionLocal()
        try:
            cart_items = session.query(CartItem).filter(CartItem.user_id == user_id).all()
            if not cart_items:
                raise Exception("Cart empty")

            total = sum(ci.quantity * session.query(Product).get(ci.product_id).price for ci in cart_items)
            order = Order(user_id=user_id, total=total, status="pending")
            session.add(order)
            session.flush()

            for ci in cart_items:
                oi = OrderItem(order_id=order.id,
                               product_id=ci.product_id,
                               price=session.query(Product).get(ci.product_id).price,
                               quantity=ci.quantity)
                session.add(oi)

            session.query(CartItem).filter(CartItem.user_id == user_id).delete()
            session.commit()
            return order
        except Exception as e:
            session.rollback()
            return e
        finally:
            session.close()

    def history(self, user_id: int):
        session = SessionLocal()
        orders = session.query(Order).filter(Order.user_id == user_id).all()
        session.close()
        return orders
