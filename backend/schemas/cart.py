from pydantic import BaseModel

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int