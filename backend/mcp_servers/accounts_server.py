"""
Accounts MCP Server
Exposes account-related tools (balance enquiry) over MCP.
Reads fake customer data from data/accounts.csv.

SECURITY: every tool independently verifies the caller's JWT and checks
it matches the customer_id being requested - it does NOT trust that the
calling agent already did this check.
"""

from pathlib import Path

import pandas as pd
from mcp.server.fastmcp import FastMCP

import auth

mcp = FastMCP("accounts-server")
mcp.settings.port = 8001

DATA_PATH = Path(__file__).parent.parent / "data" / "accounts.csv"

_df = pd.read_csv(DATA_PATH, dtype={"customer_id": str, "account_number": str})
_df = _df.set_index("customer_id")


def _authorize(customer_id: str, auth_token: str) -> dict | None:
    """
    Returns an error dict if the token is invalid or doesn't match the
    requested customer_id. Returns None if authorization passes.
    """
    payload = auth.verify_token(auth_token)
    if not payload:
        return {"error": "Unauthorized: invalid or expired token."}
    if payload["customer_id"] != customer_id:
        return {"error": "Access denied: token does not authorize this customer_id."}
    return None


@mcp.tool()
def get_balance(customer_id: str, auth_token: str) -> dict:
    """
    Get the current account balance for a customer.

    Args:
        customer_id: The unique ID of the customer (e.g. 'CUST001')
        auth_token: The caller's JWT, verified independently by this server.

    Returns:
        A dict with account_number, balance, and currency,
        or an error message if unauthorized or not found.
    """
    auth_error = _authorize(customer_id, auth_token)
    if auth_error:
        return auth_error

    if customer_id not in _df.index:
        return {"error": f"No account found for customer_id '{customer_id}'"}

    row = _df.loc[customer_id]
    return {
        "account_number": row["account_number"],
        "balance": float(row["balance"]),
        "currency": row["currency"],
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")