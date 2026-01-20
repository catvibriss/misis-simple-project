# routers.py
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel

from db import tools, structure

users_svc = tools.Users()
catalog_svc = tools.Catalog()
cart_svc = tools.Cart()
orders_svc = tools.Orders()
auth_svc = tools.Auth()

def serialize_user(u: structure.User) -> Dict[str, Any]:
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "registered_at": u.registered_at.isoformat() if u.registered_at else None,
    }

def serialize_category(c: structure.Category) -> Dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "slug": c.slug,
    }

def serialize_product(p: structure.Product) -> Dict[str, Any]:
    sess = structure.session
    cat = None
    if p.category_id is not None:
        cat = sess.query(structure.Category).get(p.category_id)
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": float(p.price) if p.price is not None else None,
        "stock": p.stock,
        "image": p.image,
        "category": serialize_category(cat) if cat else None,
    }

def serialize_cart_item(ci: structure.CartItem) -> Dict[str, Any]:
    sess = structure.session
    prod = sess.query(structure.Product).get(ci.product_id)
    return {
        "id": ci.id,
        "product": serialize_product(prod) if prod else {"id": ci.product_id},
        "quantity": ci.quantity,
        "user_id": ci.user_id,
    }

def serialize_order_item(oi: structure.OrderItem) -> Dict[str, Any]:
    sess = structure.session
    prod = sess.query(structure.Product).get(oi.product_id)
    return {
        "id": oi.id,
        "product": serialize_product(prod) if prod else {"id": oi.product_id},
        "price": float(oi.price),
        "quantity": oi.quantity,
    }

def serialize_order(o: structure.Order) -> Dict[str, Any]:
    sess = structure.session
    items = sess.query(structure.OrderItem).filter(structure.OrderItem.order_id == o.id).all()
    return {
        "id": o.id,
        "user_id": o.user_id,
        "status": o.status,
        "total": float(o.total),
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "items": [serialize_order_item(i) for i in items],
    }

class RegisterIn(BaseModel):
    username: str
    email: str
    password: str
    name: Optional[str] = None

class LoginIn(BaseModel):
    email: str
    password: str

class ProductCreateIn(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    image: Optional[str] = None
    category_id: Optional[int] = None

class CategoryCreateIn(BaseModel):
    name: str
    description: Optional[str] = None
    slug: str

class CartAddIn(BaseModel):
    product_id: int
    quantity: int = 1

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/register", status_code=201)
def register(payload: RegisterIn):
    res = users_svc.register(username=payload.username, password=payload.password, email=payload.email)
    if isinstance(res, Exception):
        # Возврат 400 с текстом ошибки
        raise HTTPException(status_code=400, detail=str(res))
    # При необходимости установить имя
    if payload.name:
        sess = structure.session
        try:
            res.name = payload.name
            sess.add(res)
            sess.commit()
            sess.refresh(res)
        except Exception:
            sess.rollback()
        # не закрываем глобальную session
    return serialize_user(res)

@auth_router.post("/login")
def login(payload: LoginIn):
    token = users_svc.login(email=payload.email, password=payload.password)
    if isinstance(token, Exception):
        raise HTTPException(status_code=401, detail=str(token))
    return {"access_token": token, "token_type": "bearer"}

@auth_router.get("/me")
def me(current_user: structure.User = Depends(users_svc.get_current)):
    return serialize_user(current_user)

categories_router = APIRouter(prefix="/categories", tags=["categories"])

@categories_router.get("", response_model=List[Dict])
def list_categories():
    cats = catalog_svc.list_categories()
    if isinstance(cats, Exception):
        raise HTTPException(status_code=500, detail=str(cats))
    return [serialize_category(c) for c in cats]

@categories_router.post("", status_code=201)
def create_category(payload: CategoryCreateIn, current_user: structure.User = Depends(users_svc.get_current)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    res = catalog_svc.create_category(name=payload.name, description=payload.description or "", slug=payload.slug)
    if isinstance(res, Exception):
        raise HTTPException(status_code=400, detail=str(res))
    return serialize_category(res)

products_router = APIRouter(prefix="/products", tags=["products"])

@products_router.get("", response_model=List[Dict])
def list_products(category_id: Optional[int] = None, q: Optional[str] = None):
    prods = catalog_svc.list_products()
    if isinstance(prods, Exception):
        raise HTTPException(status_code=500, detail=str(prods))
    # простой фильтр на уровне приложения
    filtered = prods
    if category_id is not None:
        filtered = [p for p in filtered if p.category_id == category_id]
    if q:
        filtered = [p for p in filtered if q.lower() in (p.name or "").lower() or q.lower() in (p.description or "").lower()]
    return [serialize_product(p) for p in filtered]

@products_router.get("/{product_id}")
def get_product(product_id: int):
    p = catalog_svc.get_product(product_id)
    if isinstance(p, Exception) or p is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(p)

@products_router.post("", status_code=201)
def create_product(payload: ProductCreateIn, current_user: structure.User = Depends(users_svc.get_current)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    body = payload.dict()
    res = catalog_svc.create_product(**body)
    if isinstance(res, Exception):
        raise HTTPException(status_code=400, detail=str(res))
    return serialize_product(res)

@products_router.put("/{product_id}")
def update_product(product_id: int, payload: ProductCreateIn, current_user: structure.User = Depends(users_svc.get_current)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    sess = structure.session
    p = sess.query(structure.Product).get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in payload.dict().items():
        setattr(p, k, v)
    try:
        sess.add(p)
        sess.commit()
        sess.refresh(p)
    except Exception as e:
        sess.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_product(p)

@products_router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, current_user: structure.User = Depends(users_svc.get_current)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    sess = structure.session
    p = sess.query(structure.Product).get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        sess.delete(p)
        sess.commit()
    except Exception as e:
        sess.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "deleted"}

cart_router = APIRouter(prefix="/cart", tags=["cart"])

@cart_router.get("", response_model=List[Dict])
def view_cart(current_user: structure.User = Depends(users_svc.get_current)):
    items = cart_svc.view(current_user.id)
    if isinstance(items, Exception):
        raise HTTPException(status_code=500, detail=str(items))
    return [serialize_cart_item(i) for i in items]

@cart_router.post("", status_code=201)
def add_to_cart(payload: CartAddIn, current_user: structure.User = Depends(users_svc.get_current)):
    res = cart_svc.add_item(user_id=current_user.id, product_id=payload.product_id, quantity=payload.quantity)
    if isinstance(res, Exception):
        raise HTTPException(status_code=400, detail=str(res))
    return serialize_cart_item(res)

@cart_router.delete("/{cart_item_id}", status_code=204)
def remove_from_cart(cart_item_id: int, current_user: structure.User = Depends(users_svc.get_current)):
    sess = structure.session
    ci = sess.query(structure.CartItem).get(cart_item_id)
    if not ci or ci.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cart item not found")
    try:
        sess.delete(ci)
        sess.commit()
    except Exception as e:
        sess.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "deleted"}

orders_router = APIRouter(prefix="/orders", tags=["orders"])

@orders_router.post("", status_code=201)
def create_order(current_user: structure.User = Depends(users_svc.get_current)):
    res = orders_svc.place(user_id=current_user.id)
    if isinstance(res, Exception):
        raise HTTPException(status_code=400, detail=str(res))
    return serialize_order(res)

@orders_router.get("", response_model=List[Dict])
def order_history(current_user: structure.User = Depends(users_svc.get_current)):
    res = orders_svc.history(user_id=current_user.id)
    if isinstance(res, Exception):
        raise HTTPException(status_code=500, detail=str(res))
    return [serialize_order(o) for o in res]

all_routers = [
    auth_router,
    categories_router,
    products_router,
    cart_router,
    orders_router,
]
