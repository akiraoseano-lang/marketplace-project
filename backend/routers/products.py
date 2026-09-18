from fastapi import APIRouter
from schemas.product import Product
from database.connection import get_connection

router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)

@router.get("/")
def get_products():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return products

@router.post("/")
def create_product(product: Product):

    connection = get_connection()
    cursor = connection.cursor()

    sql = "INSERT INTO products (name, price) VALUES (%s, %s)"

    cursor.execute(sql, (product.name, product.price))

    connection.commit()

    product_id = cursor.lasrowid

    cursor.close()
    connection.close()

    return {
        "id": product_id,
        "name": product.name,
        "price": product.price
    }

@router.get("/{product_id}")
def get_product(product_id: int):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM products WHERE id = %s",
        (product_id,)
    )

    product = cursor.fetchone()

    cursor.close()
    connection.close()

    if product is None:
        return {"message": "Sorry, product not found"}

    return product

@router.put("/{product_id}")
def update_product(product_id: int, product: Product):

    connection = get_connection()
    cursor = connection.cursor()

    sql = """
        UPDATE products
        SET name = %s, price = %s
        WHERE id = %s
    """

    cursor.execute(
        sql,
        (product.name, product.price, product_id)
    )

    connection.commit()

    if cursor.rowcount == 0:
        cursor.close()
        connection.close()

        return {"message": "Sorry, product not found"}

    cursor.close()
    connection.close()

    return {
        "id": product_id,
        "name": product.name,
        "price":  product.price
    }

@router.delete("/{product_id}")
def delete_product(product_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM products WHERE id = %s",
        (product_id,)
    )

    connection.commit()

    if cursor.rowcount  == 0:
        cursor.close()
        connection.close()

        return {"message" : "Sorry, product not found"}

    cursor.close()
    connection.close()

    return {
        "message": "Product detected successfully"
    }