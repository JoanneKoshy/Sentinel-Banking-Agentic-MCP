"""
Service MCP Server
Exposes service-request tools over MCP. Writes to data/service_requests.csv.

SECURITY: every tool independently verifies the caller's JWT and checks
it matches the customer_id being requested.
"""

import csv
import uuid
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

import auth

mcp = FastMCP("service-server")
mcp.settings.port = 8003

DATA_PATH = Path(__file__).parent.parent / "data" / "service_requests.csv"


def _authorize(customer_id: str, auth_token: str) -> dict | None:
    payload = auth.verify_token(auth_token)
    if not payload:
        return {"error": "Unauthorized: invalid or expired token."}
    if payload["customer_id"] != customer_id:
        return {"error": "Access denied: token does not authorize this customer_id."}
    return None


def _log_request(customer_id: str, request_type: str, details: str) -> str:
    request_id = f"REQ{uuid.uuid4().hex[:8].upper()}"
    file_exists = DATA_PATH.exists() and DATA_PATH.stat().st_size > 0

    with open(DATA_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["request_id", "customer_id", "request_type", "details", "status", "created_at"]
            )
        writer.writerow(
            [request_id, customer_id, request_type, details, "pending", datetime.now().isoformat()]
        )
    return request_id


@mcp.tool()
def request_cheque_book(customer_id: str, auth_token: str, num_leaves: int = 25) -> dict:
    """
    Request a new cheque book for a customer.

    Args:
        customer_id: The unique ID of the customer (e.g. 'CUST001')
        auth_token: The caller's JWT, verified independently by this server.
        num_leaves: Number of cheque leaves requested (default 25)
    """
    auth_error = _authorize(customer_id, auth_token)
    if auth_error:
        return auth_error

    request_id = _log_request(customer_id, "cheque_book", f"{num_leaves} leaves requested")
    return {
        "request_id": request_id,
        "status": "pending",
        "message": f"Cheque book request for {num_leaves} leaves has been submitted.",
    }


@mcp.tool()
def update_address(customer_id: str, auth_token: str, new_address: str) -> dict:
    """
    Submit an address change request for a customer.

    Args:
        customer_id: The unique ID of the customer (e.g. 'CUST001')
        auth_token: The caller's JWT, verified independently by this server.
        new_address: The new address to update to
    """
    auth_error = _authorize(customer_id, auth_token)
    if auth_error:
        return auth_error

    request_id = _log_request(customer_id, "address_change", new_address)
    return {
        "request_id": request_id,
        "status": "pending",
        "message": "Address change request submitted for verification.",
    }


@mcp.tool()
def request_kyc_update(customer_id: str, auth_token: str) -> dict:
    """
    Submit a KYC update request for a customer.

    Args:
        customer_id: The unique ID of the customer (e.g. 'CUST001')
        auth_token: The caller's JWT, verified independently by this server.
    """
    auth_error = _authorize(customer_id, auth_token)
    if auth_error:
        return auth_error

    request_id = _log_request(customer_id, "kyc_update", "Full KYC re-verification requested")
    return {
        "request_id": request_id,
        "status": "pending",
        "message": "KYC update request submitted. You will be contacted for document verification.",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")