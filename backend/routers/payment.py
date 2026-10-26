import hashlib
import hmac
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from database.connection import get_connection
from utils.auth import get_current_user
from utils.midtrans import snap, SERVER_KEY
from schemas.payment import PaymentCreate

router = APIRouter
prefix="/api/payment",
tags=["payment"]


@router.post("/notification")
async def payment_notification(request: Request):
    notification = await request.json()

    
    order_id = notification.get("order_id", "")
    status_code = notification.get("status_code", "")
    gross_amount = notification.get("gross_amount", "")
    signature_key = notification.get("signature_key", "")

    if not all([order_id, status_code, gross_amount, signature_key]):
        raise HTTPException(
            status_code=400,
            detail="Data notifikasi tidak lengkap"
        )

   
    signature_input = (
        order_id + status_code + gross_amount + SERVER_KEY
    )
    expected_signature = hashlib.sha512(
        signature_input.encode("utf-8")
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature_key):
        raise HTTPException(
            status_code=403,
            detail="Signature notifikasi tidak valid"
        )

    parts = order_id.split("-")

    if (
        len(parts) != 3
        or parts[0] != "marketplace"
        or not parts[1].isdigit()
        or not parts[2].isdigit()
    ):
        raise HTTPException(
            status_code=400,
            detail="Order ID tidak valid"
        )

    local_order_id = int(parts[1])
    notification_user_id = int(parts[2])

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
    
        cursor.execute("""
            SELECT id, user_id, total_price, payment_status
            FROM orders
            WHERE id = %s AND user_id = %s
        """, (local_order_id, notification_user_id))

        order = cursor.fetchone()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order tidak ditemukan"
            )

        
        if Decimal(gross_amount) != Decimal(str(order["total_price"])):
            raise HTTPException(
                status_code=400,
                detail="Nominal pembayaran tidak cocok"
            )

        transaction_status = notification.get("transaction_status")
        fraud_status = notification.get("fraud_status")

       
        if (
            transaction_status == "settlement"
            or (
                transaction_status == "capture"
                and fraud_status == "accept"
            )
        ):
            new_status = "paid"

        elif transaction_status in ("deny", "cancel", "expire"):
            new_status = "failed"

        else:
            new_status = "pending"

        if order["payment_status"] != "paid":
            cursor.execute("""
                UPDATE orders
                SET payment_status = %s,
                    payment_method = %s
                WHERE id = %s AND user_id = %s
            """, (
                new_status,
                notification.get("payment_type", "midtrans"),
                local_order_id,
                notification_user_id
            ))

            connection.commit()

        return {
            "message": "Notifikasi berhasil diproses",
            "order_id": local_order_id,
            "payment_status": (
                order["payment_status"]
                if order["payment_status"] == "paid"
                else new_status
            )
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception as error:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail="Gagal memproses notifikasi pembayaran"
        ) from error

    finally:
        cursor.close()
        connection.close()
