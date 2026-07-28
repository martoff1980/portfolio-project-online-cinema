import os
import stripe
from fastapi import HTTPException

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
stripe.api_key = STRIPE_API_KEY

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def create_payment_session(
    order_id: int,
    total_amount: float,
    email: str
) -> str | None:
    """
    Generates a payment session.
    Returns a placeholder link if STRIPE_API_KEY is missing.
    """
    if not STRIPE_API_KEY:
        # Stub mode for local testing
        return f"{BASE_URL}/orders/{order_id}/mock-payment?status=success"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name":
                                f"Order #{order_id} - Online Cinema Access",
                        },
                        # Stripe accepts cents.
                        "unit_amount": round(total_amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            customer_email=email,
            success_url=(
                f"{BASE_URL}/orders/{order_id}/payment-success?"
                f"session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{BASE_URL}/orders/{order_id}/payment-cancel",
            metadata={"order_id": str(order_id)},
        )
        return session.url
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stripe payment initiation failed: {str(e)}"
        )
