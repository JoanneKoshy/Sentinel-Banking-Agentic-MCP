"""
Quick test script - acts as an MCP client to call the Transactions server.
Run this while transactions_server.py is running in another terminal.
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    url = "http://127.0.0.1:8002/mcp"

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            # Test get_transactions
            result = await session.call_tool(
                "get_transactions", arguments={"customer_id": "CUST001", "limit": 3}
            )
            print("\nRecent transactions:", result.content[0].text)

            # Test get_statement
            result2 = await session.call_tool(
                "get_statement", arguments={"customer_id": "CUST001", "month": "2026-08"}
            )
            print("\nAugust statement:", result2.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
