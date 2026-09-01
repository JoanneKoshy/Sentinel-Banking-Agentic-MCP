"""
Service Agent - calls the Service MCP server. Tracks latency/errors
via observability.py, and history for follow-up questions.
"""

import asyncio
import json
import logging

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import AzureOpenAI

import config
import pii
import observability

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("service_agent")

client = AzureOpenAI(
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
)

SYSTEM_PROMPT = (
    "You are the Service Agent for a bank's customer support system. "
    "You ONLY handle these service requests, for the currently authenticated "
    "customer: requesting a new cheque book, updating an address, and "
    "requesting a KYC update. You cannot act on any other customer's account. "
    "You have three tools available: request_cheque_book, update_address, "
    "and request_kyc_update. Call them directly - you do not need to ask the "
    "user for any IDs or tokens. "
    "Always confirm the request_id back to the customer after submitting a request."
)

HIDDEN_PARAMS = {"customer_id", "auth_token"}


def _strip_hidden_params(schema: dict) -> dict:
    schema = dict(schema)
    properties = dict(schema.get("properties", {}))
    for param in HIDDEN_PARAMS:
        properties.pop(param, None)
    schema["properties"] = properties
    required = schema.get("required", [])
    schema["required"] = [r for r in required if r not in HIDDEN_PARAMS]
    return schema


async def _get_mcp_tools_schema(session: ClientSession) -> list[dict]:
    tools_result = await session.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": _strip_hidden_params(t.inputSchema),
            },
        }
        for t in tools_result.tools
    ]


async def handle_message(
    user_message: str, customer_id: str, token: str, history: list[dict] | None = None
) -> str:
    with observability.track_agent_call("service"):
        url = config.SERVICE_MCP_URL
        logger.info("Handling message for customer_id=%s: %r", customer_id, user_message)

        async with streamablehttp_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_schema = await _get_mcp_tools_schema(session)

                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                messages.extend(history or [])
                messages.append({"role": "user", "content": user_message})

                response = client.chat.completions.create(
                    model=config.AZURE_CHAT_DEPLOYMENT, messages=messages, tools=tools_schema
                )
                choice = response.choices[0].message

                if not choice.tool_calls:
                    return choice.content

                messages.append(choice)
                for tool_call in choice.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    args["customer_id"] = customer_id
                    args["auth_token"] = token

                    logger.info(
                        "Calling tool '%s' with args: %s",
                        tool_call.function.name,
                        pii.redact_for_log(args),
                    )

                    with observability.track_tool_call(tool_call.function.name):
                        result = await session.call_tool(tool_call.function.name, arguments=args)
                        result_text = result.content[0].text

                    logger.info(
                        "Tool '%s' returned: %s",
                        tool_call.function.name,
                        pii.redact_for_log(json.loads(result_text)),
                    )

                    messages.append(
                        {"role": "tool", "tool_call_id": tool_call.id, "content": result_text}
                    )

                final_response = client.chat.completions.create(
                    model=config.AZURE_CHAT_DEPLOYMENT, messages=messages
                )
                return final_response.choices[0].message.content


if __name__ == "__main__":
    print("This module now requires a real token - test via main.py instead.")