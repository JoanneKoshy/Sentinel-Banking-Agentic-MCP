"""
Simulated Bank Identity Provider.

Handles: OTP generation + verification (tied to phone numbers from
accounts.csv), and issuing/verifying JWT tokens once a customer proves
who they are.

NOTE: OTP delivery is simulated - in a real system this would call an
SMS gateway (e.g. Twilio). Here, the OTP is returned directly in the
API response so it can be entered manually for testing.
"""

import random
import time
from pathlib import Path

import jwt
import pandas as pd

import config

DATA_PATH = Path(__file__).parent / "data" / "accounts.csv"
_accounts_df = pd.read_csv(DATA_PATH, dtype={"customer_id": str, "phone_number": str})

OTP_TTL_SECONDS = 300
JWT_TTL_SECONDS = 3600

_otp_store: dict[str, dict] = {}


def _find_customer_by_phone(phone_number: str) -> dict | None:
    match = _accounts_df[_accounts_df["phone_number"] == phone_number]
    if match.empty:
        return None
    row = match.iloc[0]
    return {"customer_id": row["customer_id"], "name": row["name"]}


def send_otp(phone_number: str) -> dict:
    customer = _find_customer_by_phone(phone_number)
    if not customer:
        return {"error": "No account found for this phone number."}

    otp = f"{random.randint(0, 999999):06d}"
    _otp_store[phone_number] = {
        "otp": otp,
        "expires_at": time.time() + OTP_TTL_SECONDS,
    }

    return {
        "message": f"OTP sent to {phone_number}.",
        "demo_otp": otp,
    }


def verify_otp(phone_number: str, otp: str) -> dict:
    record = _otp_store.get(phone_number)
    if not record:
        return {"error": "No OTP was requested for this phone number."}

    if time.time() > record["expires_at"]:
        del _otp_store[phone_number]
        return {"error": "OTP has expired. Please request a new one."}

    if otp != record["otp"]:
        return {"error": "Incorrect OTP."}

    del _otp_store[phone_number]
    customer = _find_customer_by_phone(phone_number)

    token = jwt.encode(
        {
            "customer_id": customer["customer_id"],
            "name": customer["name"],
            "exp": time.time() + JWT_TTL_SECONDS,
        },
        config.JWT_SECRET,
        algorithm="HS256",
    )

    return {
        "token": token,
        "customer_id": customer["customer_id"],
        "name": customer["name"],
    }


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None