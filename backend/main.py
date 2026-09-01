"""
FastAPI entry point.
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import auth
import session_store
import observability
from agents import coordinator_agent

app = FastAPI(title="Bank Agentic Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SendOtpRequest(BaseModel):
    phone_number: str


class VerifyOtpRequest(BaseModel):
    phone_number: str
    otp: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.post("/auth/send-otp")
async def send_otp(request: SendOtpRequest):
    result = auth.send_otp(request.phone_number)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/auth/verify-otp")
async def verify_otp(request: VerifyOtpRequest):
    result = auth.verify_otp(request.phone_number, request.otp)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    session_store.clear_history(result["customer_id"])
    return result


def _get_authenticated_customer(authorization: str | None) -> tuple[dict, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")

    token = authorization.removeprefix("Bearer ").strip()
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token. Please log in again.")

    return payload, token


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, authorization: str | None = Header(default=None)):
    customer, token = _get_authenticated_customer(authorization)
    customer_id = customer["customer_id"]

    history = session_store.get_history(customer_id)

    reply = await coordinator_agent.handle_message(
        user_message=request.message,
        customer_id=customer_id,
        token=token,
        history=history,
    )

    session_store.append_turn(customer_id, "user", request.message)
    session_store.append_turn(customer_id, "assistant", reply)

    return ChatResponse(reply=reply)


@app.get("/metrics")
async def metrics():
    return observability.get_metrics()


@app.get("/health")
async def health():
    return {"status": "ok"}