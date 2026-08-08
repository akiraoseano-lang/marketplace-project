from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    return {'message': 'Marketplace API is Running'}

@app.get('/api/products')
def get_products():
    return [
        {
            "id": 1,
            "name": "Laptop",
            "price": 3000000
        },
        {
            "id": 2,
            "name": "Mouse",
            "price": 100000
        }
    ]