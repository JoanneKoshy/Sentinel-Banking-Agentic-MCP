"""
Transactions MCP Server
Exposes transaction-related tools over MCP. Reads data/transactions.csv.

SECURITY: every tool independently verifies the caller's JWT and checks
it matches the customer_id being requested.
"""

from pathlib import Path

import pandas as pd
from mcp.server.fastmcp import FastMCP

import auth

mcp = FastMCP("transactions-server")
mcp.settings.port = 8002

DATA_PATH = Path(__file__).parent.parent / "data" / "transactions.csv"

_df = pd.read_csv(DATA_PATH, dtype={"customer_id": str})
_df["date"] = pd.to_datetime(_df["date"])


def _authorize(customer_id: str, auth_token: str) -> dict | None:
    payload = auth.verify_token(auth_token)
    if not payload:
        return {"error": "Unauthorized: invalid or expired token."}
    if payload["customer_id"] != customer_id:
        return {"error": "Access denied: token does not authorize this customer_id."}
    return None


@mcp.tool()
def get_transactions(customer_id: str, auth_token: str, limit: int = 5) -> dict:
    """
    Get the most recent transactions for a customer.

    Args:
        customer_id: The unique ID of the customer (e.g. 'CUST001')
        auth_token: The caller's JWT, verified independently by this server.
        limit: How many recent transactions to return (default 5)
    """
    auth_error = _authorize(customer_id, auth_token)
    if auth_error:
        return auth_error

    customer_txns = _df[_df["customer_id"] == customer_id].sort_values(
        "date", ascending=False
    )
    if customer_txns.empty:
        return {"error": f"No transactions found for customer_id '{customer_id}'"}

    recent = customer_txns.head(limit)
    transactions = [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "description": row["description"],
            "amount": float(row["amount"]),
            "type": row["type"],
        }
        for _, row in recent.iterrows()
    ]
    return {"transactions": transactions}


@mcp.tool()
def get_statement(customer_id: str, auth_token: str, month: str) -> dict:
    """
    Get a full statement for a customer in a given month ('YYYY-MM').

    Args:
        customer_id: The unique ID of the customer (e.g. 'CUST001')
        auth_token: The caller's JWT, verified independently by this server.
        month: Month in 'YYYY-MM' format
    """
    auth_error = _authorize(customer_id, auth_token)
    if auth_error:
        return auth_error

    customer_txns = _df[_df["customer_id"] == customer_id]
    month_txns = customer_txns[
        customer_txns["date"].dt.strftime("%Y-%m") == month
    ].sort_values("date")

    if month_txns.empty:
        return {
            "error": f"No transactions found for customer_id '{customer_id}' in {month}"
        }

    transactions = [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "description": row["description"],
            "amount": float(row["amount"]),
            "type": row["type"],
        }
        for _, row in month_txns.iterrows()
    ]
    return {"transactions": transactions}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")