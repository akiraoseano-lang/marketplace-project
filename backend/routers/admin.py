from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal

from database.connection import get_connection
from utils.auth import get_current_admin

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)

class OrderStatusUpdate(BaseModel):
    status: Literal[
        "processing",
        "shipped",
        "completed",
        "cancelled"
    ]

@router.get("/orders")
def get_all_orders(
    current_admin: dict = Depends(get_current_admin)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                orders.id,
                orders.user_id,
                users.name AS customer_name,
                users.email AS customer_email,
                orders.total_price,
                orders.status,
                orders.payment_method,
                orders.payment_status,
                orders.created_at
            FROM orders
            JOIN users ON orders.user_id = users.id
            ORDER BY orders.created_at DESC
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

@router.get("/orders/{order_id}")
def get_admin_order_detail(
    order_id:int,
    current_admin: dict = Depends(get_current_admin)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                orders.*,
                users.name AS customer_name,
                users.email AS customer_email
            FROM orders
            JOIN users ON orders.user_id = users.id
            WHERE orders.id = %s
        """, (order_id,))

        order = cursor.fetchone()

        if order is None:
            raise HTTPException(
                status_code = 404,
                detail = "Sorry, order is not found"
            )

        cursor.execute("""
            SELECT
                order_items.id,
                order_items.product_id,
                products.name AS product_name,
                order_items.quantity,
                order_items.price,
                order_items.created_at
            FROM order_items
            LEFT JOIN products
                ON order_items.product_id = products.id
            WHERE orders_items.order_id = %s
        """, (order_id,))

        items = cursor.fetchall()

        return {
            "order": order,
            "items": items
        }

    finally:
        cursor.close()
        connection.close()

@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, status, payment_status
            FROM orders
            WHERE id = %s
            FOR UPDATE
        """, (order_id,))

        order = cursor.fetchone()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Sorry, your order is not found"
            )

        current_status = order["status"]
        new_status = data.status
        payment_status = order["payment_status"]

        allowed_transitions = {
            "pending"
        }