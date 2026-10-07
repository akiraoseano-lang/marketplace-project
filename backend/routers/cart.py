from fastapi import APIRouter, Depends
from schemas.cart import CartItemCreate
from database.connection import get_connection
from utils.auth import get_current_user

router = APIRouter(
    prefix="/api/cart",
    tags=["Cart"]
)

@router.post("/")
def add_to_cart(
    item: CartItemCreate,
    current_user: dict = Depends(get_current_user)
):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM products WHERE id = %s",
        (item.product_id,)
    )

    product = cursor.fetchone()

    if product is None:
        cursor.close()
        connection.close()

        return {
            "message": "Sorry, product not found"
        }

    cursor.execute(
    """
    INSERT INTO cart_items (user_id, product_id, quantity)
    VALUES (%s, %s, %s)
    """,
    (
        current_user["user_id"],
        item.product_id,
        item.quantity
    )
)

    connection.commit()

    cart_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return { 
        "message": "Product added to cart",
        "cart": {
            "id": cart_id,
            "user_id": current_user["user_id"],
            "product_id": item.product_id,
            "quantity": item.quantity
        }
    }

@router.get("/")
def get_cart(
    current_user: dict = Depends(get_current_user)
):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            cart_items.id,
            cart_items.product_id,
            products.name,
            products.price,
            cart_items.quantity
        FROM cart_items
        JOIN products
            ON cart_items.product_id = products.id
        WHERE cart_items.user_id = %s
        """,
        (current_user["user_id"],)
    )

    cart_items =  cursor.fetchall()

    cursor.close()
    connection.close()

    return cart_items

@router.put("/[cart_id]")
def update_cart(
    cart_id: int,
    item: CartItemCreate,
    current_user: dict = Depends(get_current_user)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE cart_items
        SET quantity = %s
        WHERE id = %s
        AND user_id = %s
        """,
        (
            item.quantity,
            cart_id,
            current_user["user_id"]
        )
    )

    connection.commit()

    if cursor.rowcount == 0:
        cursor.close()
        connection.close()

        return {
            "message": "Sorry, cart item not found"
        }

    cursor.close()
    connection.close()

    return {
        "message": "Nice, Cart update successfully",
        "cart": {
            "id": cart_id,
            "user_id": current_user["user_id"],
            "quantity": item.quantity
        }
    }

@router.delete("/{cart_id}")
def delete_cart(
    cart_id: int,
    current_user: dict = Depends(get_current_user)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM cart_items
        WHERE id = %s
        AND user_id = %s
        """,
        (
            cart_id,
            current_user["user_id"]
        )
    )

    connection.commit()

    if cursor.rowcount == 0:
        cursor.close()
        connection.close()

        return {
            "message": "sorry, cart item not found"
        }

    cursor.close()
    connection.close()

    return {
        "message": "cart item deleted successfully",
        "cart_id": cart_id
    }
