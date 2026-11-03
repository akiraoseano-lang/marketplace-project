import json
import hashlib
import hmac
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Request

from database.connection import get_connection
from utils.auth import get_current_user
from utils.midtrans import snap, SERVER_KEY
from schemas.payment import PaymentCreate


router = APIRouter(
    prefix="/api/payment",
    tags=["Payment"]
)

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
            WHERE id = %s AND user_id = %s
        """, (
            payment.order_id,
            current_user["user_id"]
        ))

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

        transaction_data = {
            "transaction_details": {
                "order_id": midtrans_order_id,
                "gross_amount": int(order["total_price"])
            }
        }

        result = snap.create_transaction(transaction_data)

        cursor.execute("""
            UPDATE orders
            SET payment_method = %s,
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

        print("ERROR NOTIFICATION:", repr(error))

        raise HTTPException(
            status_code=502,
            detail="Gagal memproses notifikasi pembayaran"
        ) from error

    finally:
        cursor.close()
        connection.close()

@router.post("/notification")
async def payment_notification(request: Request):

    body = await request.body()

    if not body:
        raise HTTPException(
            status_code=400,
            detail="Body notifikasi kosong"
        )

    try:
        notification = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Format notifikasi bukan JSON yang valid"
        )

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
        """, (
            local_order_id,
            notification_user_id
        ))

        order = cursor.fetchone()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order tidak ditemukan"
            )

        try:
            gross = Decimal(gross_amount)
        except (InvalidOperation, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Nominal pembayaran tidak valid"
            )

        print("DEBUG MIDTRANS:", repr(gross_amount))
        print("DEBUG MYSQL:", repr(order["total_price"]))
        print("DEBUG TYPE MYSQL:", type(order["total_price"]))
        print("DEBUG GROSS:", repr(gross))
        print("DEBUG DB DECIMAL:", repr(Decimal(str(order["total_price"]))))
 
        if gross != Decimal(str(order["total_price"])):
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
                    payment_method = %s,
                    status = CASE
                        WHEN %s = 'paid' THEN 'processing'
                        WHEN %s = 'failed' THEN 'cancelled'
                        ELSE status
                    END
                WHERE id = %s AND user_id = %s
            """, (
                new_status,
                notification.get("payment_type", "midtrans"),
                new_status,
                new_status,
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


@router.post("/test-notification")
def test_notification(
    order_id: str,
    status_code: str = "200",
    gross_amount: str = "0",
    transaction_status: str = "settlement",
    fraud_status: str = "accept",
    payment_type: str = "bank_transfer",
    current_user: dict = Depends(get_current_user)
):
    """
    Simulate a Midtrans webhook notification locally.
    No signature verification — for development/testing only.
    """
    parts = order_id.split("-")

    if (
        len(parts) != 3
        or parts[0] != "marketplace"
        or not parts[1].isdigit()
        or not parts[2].isdigit()
    ):
        raise HTTPException(
            status_code=400,
            detail="Order ID must be in format: marketplace-{order_id}-{user_id}"
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
        """, (
            local_order_id,
            notification_user_id
        ))

        order = cursor.fetchone()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

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
                    payment_method = %s,
                    status = CASE
                        WHEN %s = 'paid' THEN 'processing'
                        WHEN %s = 'failed' THEN 'cancelled'
                        ELSE status
                    END
                WHERE id = %s AND user_id = %s
            """, (
                new_status,
                payment_type,
                new_status,
                new_status,
                local_order_id,
                notification_user_id
            ))

            connection.commit()

        return {
            "message": "Test notification processed",
            "order_id": local_order_id,
            "payment_status": (
                order["payment_status"]
                if order["payment_status"] == "paid"
                else new_status
            ),
            "status": "processing" if new_status == "paid" else ("cancelled" if new_status == "failed" else order.get("status"))
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception as error:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail="Gagal memproses notifikasi uji coba"
        ) from error

    finally:
        cursor.close()
        connection.close()
