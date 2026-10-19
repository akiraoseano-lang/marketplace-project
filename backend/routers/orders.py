from fastapi import APIRouter, Depends
from database.connection import get_connection
from utils.auth import get_current_user


router = APIRouter(
    prefix="/api/orders",
    tags=["orders"]
)

@router.post("/")
def create_order(
    current_user: dict = Depends(get_current_user)
):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            cart_items.id,
            cart_items.product_id,
            cart_items.quantity,
            products.price
        FROM cart_items
        JOIN products
            ON cart_items.product_id = products.id
        WHERE cart_items.user_id = %s
        """,
        (current_user["user_id"],)
    )

    cart_items = cursor.fetchall()

    if not cart_items:
        cursor.close()
        connection.close()

        return {
            "message": "sorry, your cart is empety"
        }

    total_price = 0

    for item in cart_items:
        total_price += item["price"] * item["quantity"]

    cursor.execute(
        """
        INSERT INTO orders (user_id, total_price, status)
        VALUES (%s, %s, %s)\
        """,
        (
            current_user["user_id"],
            total_price,
            "pending"
        )
    )

    order_id =  cursor.lastrowid

    for item in cart_items:

        cursor.execute(
            """
            INSERT INTO order_items
            (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
            """,
            (
                order_id,
                item["product_id"],
                item["quantity"],
                item["price"]
                
            )
        )

    cursor.execute(
        """
        DELETE FROM cart_items
        WHERE user_id = %s
        """,
        (current_user["user_id"],)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Nice, Order created successfully",
        "order": {
            "id": order_id,
            "user_id": current_user["user_id"],
            "total_price": total_price,
            "status": "pending"
        }
    }

@router.get("/")
def get_orders(
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
    """
    SELECT *
    FROM orders
    WHERE user_id = %s
    """,
    (current_user["user_id"],)
    )

    orders = cursor.fetchall()

    cursor.close()
    connection.close()

    return orders

@router.get("/{order_id}")
def get_order_detail(
    order_id: int,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM orders
        WHERE id = %s AND user_id = %s
        """,
        (order_id, current_user["user_id"])
    )

    order = cursor.fetchone()

    if order is None:
        cursor.close()
        connection.close()

        return {
            "message": "Sorry, order not found"
        }

    cursor.execute(
        """
        SELECT
            order_items.id,
            order_items.product_id,
            products.name AS product_name,
            order_items.quantity,
            order_items.price
        FROM order_items
        JOIN products
            ON order_items.product_id = products.id
        WHERE order_items.order_id = %s
        """,
        (order_id,)
    )

    items = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "order": order,
        "items": items
    }