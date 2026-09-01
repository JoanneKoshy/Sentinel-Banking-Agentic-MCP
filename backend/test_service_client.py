"""
Quick test script - acts as an MCP client to call the Service server.
Run this while service_server.py is running in another terminal.
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    url = "http://127.0.0.1:8003/mcp"

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            result = await session.call_tool(
                "request_cheque_book", arguments={"customer_id": "CUST001", "num_leaves": 50}
            )
            print("\nCheque book request:", result.content[0].text)

            result2 = await session.call_tool(
                "update_address",
                arguments={"customer_id": "CUST002", "new_address": "221B Baker Street, Bangalore"},
            )
            print("\nAddress update request:", result2.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
