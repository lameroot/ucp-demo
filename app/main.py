from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from app.db import get_session, init_db
from app.models import Merchant, Order, OrderItem, Product
from app.services.llm import IntentDetector, LLMService
from app.services.ucp_client import UCPMockClient

app = FastAPI(title="UCP Demo")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
llm_service = LLMService()
ucp_client = UCPMockClient()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def root() -> RedirectResponse:
    return RedirectResponse(url="/chat", status_code=302)


@app.get("/merchants", response_class=HTMLResponse)
def merchants_page(request: Request) -> HTMLResponse:
    with get_session() as session:
        merchants = session.exec(select(Merchant)).all()
        products = session.exec(select(Product)).all()
    return templates.TemplateResponse(
        "merchants.html",
        {"request": request, "merchants": merchants, "products": products},
    )


@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request) -> HTMLResponse:
    with get_session() as session:
        merchants = session.exec(select(Merchant)).all()
    return templates.TemplateResponse("chat.html", {"request": request, "merchants": merchants})


@app.post("/api/merchants")
def create_merchant(name: str = Form(...), description: str = Form("")) -> RedirectResponse:
    with get_session() as session:
        merchant = Merchant(name=name, description=description)
        session.add(merchant)
        session.commit()
    return RedirectResponse(url="/merchants", status_code=303)


@app.post("/api/merchants/{merchant_id}/products")
def create_product(
    merchant_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price_cents: int = Form(...),
) -> RedirectResponse:
    with get_session() as session:
        product = Product(
            merchant_id=merchant_id,
            name=name,
            description=description,
            price_cents=price_cents,
        )
        session.add(product)
        session.commit()
    return RedirectResponse(url="/merchants", status_code=303)


@app.get("/api/merchants")
def list_merchants() -> List[Merchant]:
    with get_session() as session:
        return session.exec(select(Merchant)).all()


@app.get("/api/merchants/{merchant_id}/products")
def list_products(merchant_id: int) -> List[Product]:
    with get_session() as session:
        return session.exec(select(Product).where(Product.merchant_id == merchant_id)).all()


@app.post("/api/orders")
def create_order(payload: Dict) -> Dict:
    merchant_id = payload.get("merchant_id")
    items = payload.get("items", [])
    if not merchant_id or not items:
        raise HTTPException(status_code=400, detail="merchant_id and items required")
    with get_session() as session:
        products = {
            product.id: product
            for product in session.exec(select(Product).where(Product.merchant_id == merchant_id)).all()
        }
        order = Order(merchant_id=merchant_id, status="created", total_cents=0)
        session.add(order)
        session.commit()
        total_cents = 0
        for item in items:
            product_id = item.get("product_id")
            quantity = int(item.get("quantity", 1))
            product = products.get(product_id)
            if not product:
                continue
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price_cents=product.price_cents,
            )
            session.add(order_item)
            total_cents += product.price_cents * quantity
        order.total_cents = total_cents
        session.add(order)
        session.commit()
        session.refresh(order)
    return {"order_id": order.id, "total_cents": order.total_cents}


@app.post("/api/orders/{order_id}/purchase")
def purchase_order(order_id: int) -> Dict:
    with get_session() as session:
        order = session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        order.status = "pending_payment"
        session.add(order)
        session.commit()
        payment_payload = {
            "order_id": order.id,
            "merchant_id": order.merchant_id,
            "total_cents": order.total_cents,
            "currency": "RUB",
            "timestamp": datetime.utcnow().isoformat(),
        }
        payment_result = ucp_client.process_payment(payment_payload)
        order.status = "paid" if payment_result.get("status") == "ok" else "payment_failed"
        session.add(order)
        session.commit()
    return {"order_id": order.id, "status": order.status, "ucp": payment_result}


@app.post("/api/chat")
def chat(payload: Dict) -> Dict:
    merchant_id = payload.get("merchant_id")
    message = payload.get("message", "")
    if not merchant_id or not message:
        raise HTTPException(status_code=400, detail="merchant_id and message required")
    with get_session() as session:
        merchant = session.get(Merchant, merchant_id)
        if not merchant:
            raise HTTPException(status_code=404, detail="Merchant not found")
        products = session.exec(select(Product).where(Product.merchant_id == merchant_id)).all()

    intent = IntentDetector.detect(message)
    if intent == "catalog":
        catalog_lines = [
            f"{product.id}. {product.name} — {product.price_cents / 100:.2f} ₽"
            for product in products
        ]
        return {
            "reply": "Каталог товаров:\n" + "\n".join(catalog_lines),
            "intent": "catalog",
        }
    if intent == "purchase" and products:
        product = products[0]
        order_response = create_order(
            {"merchant_id": merchant_id, "items": [{"product_id": product.id, "quantity": 1}]}
        )
        return {
            "reply": (
                f"Создал заказ #{order_response['order_id']} на {product.name}. "
                "Нажмите 'Оплатить заказ', чтобы завершить покупку."
            ),
            "intent": "purchase",
            "order_id": order_response["order_id"],
        }

    system_prompt = (
        "Ты ассистент магазина. Помогай клиенту выбрать товары, "
        "отвечай кратко и по делу."
    )
    response = llm_service.generate_reply(system_prompt, [{"role": "user", "content": message}])
    return {"reply": response, "intent": "chat"}


# A2A protocol endpoints
@app.get("/a2a/{merchant_id}/info")
def a2a_info(merchant_id: int) -> Dict:
    with get_session() as session:
        merchant = session.get(Merchant, merchant_id)
        if not merchant:
            raise HTTPException(status_code=404, detail="Merchant not found")
    return {
        "merchant_id": merchant.id,
        "name": merchant.name,
        "description": merchant.description,
        "capabilities": ["catalog", "order", "purchase"],
    }


@app.get("/a2a/{merchant_id}/catalog")
def a2a_catalog(merchant_id: int) -> Dict:
    with get_session() as session:
        products = session.exec(select(Product).where(Product.merchant_id == merchant_id)).all()
    return {
        "merchant_id": merchant_id,
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price_cents": product.price_cents,
            }
            for product in products
        ],
    }


@app.post("/a2a/{merchant_id}/order")
def a2a_order(merchant_id: int, payload: Dict) -> Dict:
    payload["merchant_id"] = merchant_id
    return create_order(payload)


@app.post("/a2a/{merchant_id}/purchase")
def a2a_purchase(merchant_id: int, payload: Dict) -> Dict:
    order_id = payload.get("order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id required")
    return purchase_order(order_id)
