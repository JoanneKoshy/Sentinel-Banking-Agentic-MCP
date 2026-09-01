"""
Quick test script — acts as an MCP client to call the Accounts server.
Run this while accounts_server.py is running in another terminal.
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    url = "http://127.0.0.1:8001/mcp"

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools - proves the server is exposing get_balance correctly
            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            # Actually call the tool
            result = await session.call_tool(
                "get_balance", arguments={"customer_id": "CUST001"}
            )
            print("Result:", result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
