"""
Combined MCP Server Launcher
Runs Accounts, Transactions, and Service MCP servers all in ONE process,
mounted at different paths under a single port (8000).

Each FastMCP server needs its internal session manager explicitly started -
normally mcp.run() does this automatically, but since we are mounting multiple
servers under one Starlette app, we combine their startup routines into one
shared lifespan function.
"""

import contextlib

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount

from mcp_servers.accounts_server import mcp as accounts_mcp
from mcp_servers.transactions_server import mcp as transactions_mcp
from mcp_servers.service_server import mcp as service_mcp


@contextlib.asynccontextmanager
async def lifespan(app):
    # Start all three MCP servers' session managers together when the
    # combined app starts, and clean them up together when it stops.
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(accounts_mcp.session_manager.run())
        await stack.enter_async_context(transactions_mcp.session_manager.run())
        await stack.enter_async_context(service_mcp.session_manager.run())
        yield


app = Starlette(
    routes=[
        Mount("/accounts", app=accounts_mcp.streamable_http_app()),
        Mount("/transactions", app=transactions_mcp.streamable_http_app()),
        Mount("/service", app=service_mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)