from fastapi import APIRouter, Depends, HTTPException
from database.connection import get_connection
from utils.auth import get_current_user
from utils.midtrans import snap
from schemas.payment import PaymentCreate

router = APIRouter(prefix="/api/payment", tags=["Payment"])

@router.post("/")
def create_payment(
    payment: PaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
        SELECT id, total_price, status, payment_status
        FROM orders
        WHERE id = %s AND user_id = %s""",
    (payment.order_id, current_user["user_id"]))

        order = cursor.fetchone()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Sorry, order is not found"
            )

        if order["payment_status"] == "paid":
            raise HTTPException(
                status_code=400,
                detail="Order already paid"
            )

        if order["status"] != "pending":
            raise HTTPException(
                status_code=400,
                detail="Sorry, order cannot paid"
            )

        midtrans_order_id = (
            f"marketplace-{order['id']}-{current_user['user_id']}"
        )

        transaction_data =  {
            "transaction_details": {
                "order_id": midtrans_order_id,
                "gross_amount": int(order["total_price"]),
                "quantity": 1,
                "name": f"Marketplace Order #{order['id']}"
            }
        }

        result = snap.create_transaction(transaction_data)

        cursor.execute("""
            UPDATE orders
            SET payment_method  = %s,
                payment_status = %s
            WHERE id = %s AND user_id = %s
            """, (
                "midtrans",
                "pending",
                order["id"],
                current_user["user_id"]
            ))

        connection.commit()

        return {
            "message": "Token pembayaran berhasil dibuat",
            "order_id": order["id"],
            "total_price": order["total_price"],
            "payment_status": "pending",
            "snap_token": result["token"],
            "redirect_url": result["redirect_url"]
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception as error:
        connection.rollback()
        raise HTTPException(
            status_code=502,
            detail="Gagal membuat transaksi Midtrans. Periksa konfigurasi dan log backend."
        ) from error

    finally:
        cursor.close()
        connection.close()