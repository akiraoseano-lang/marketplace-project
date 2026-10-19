from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import payment

from routers.products import router as products_router
from routers.login import router as login_router
from routers.register import router as register_router
from routers.cart import router as cart_router
from routers.orders import router as orders_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {'message': 'Good job bro, marketplace API is Running'}

app.include_router(products_router)
app.include_router(login_router)
app.include_router(register_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payment.router)