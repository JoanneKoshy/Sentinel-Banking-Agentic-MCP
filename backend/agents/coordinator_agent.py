"""
Coordinator Agent - decides which sub-agent(s) handle a message, forwards
the caller's JWT and conversation history to each one.
"""

import asyncio
import json

from openai import AzureOpenAI

import config
from agents import accounts_agent, transaction_agent, service_agent

client = AzureOpenAI(
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
)

ROUTING_SYSTEM_PROMPT = (
    "You are a routing coordinator for a bank's customer support system. "
    "You do not answer questions yourself. Your only job is to decide which "
    "of the following agents should handle the user's message:\n\n"
    "- accounts: handles account balance questions\n"
    "- transaction: handles recent transactions and monthly statements\n"
    "- service: handles cheque book requests, address changes, and KYC updates\n\n"
    "A message may need MORE THAN ONE agent. Pick only the agents that are "
    "actually needed. Use the conversation history to understand follow-up "
    "questions like 'what about last month' or 'what was the biggest one'."
)

ROUTING_TOOL = {
    "type": "function",
    "function": {
        "name": "route_to_agents",
        "description": "Decide which domain agent(s) should handle this message.",
        "parameters": {
            "type": "object",
            "properties": {
                "agents": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["accounts", "transaction", "service"],
                    },
                }
            },
            "required": ["agents"],
        },
    },
}

AGENT_HANDLERS = {
    "accounts": accounts_agent.handle_message,
    "transaction": transaction_agent.handle_message,
    "service": service_agent.handle_message,
}


async def _decide_routing(user_message: str, history: list[dict]) -> list[str]:
    messages = [{"role": "system", "content": ROUTING_SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=config.AZURE_CHAT_DEPLOYMENT,
        messages=messages,
        tools=[ROUTING_TOOL],
        tool_choice={"type": "function", "function": {"name": "route_to_agents"}},
    )
    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    return args["agents"]


async def handle_message(
    user_message: str, customer_id: str, token: str, history: list[dict]
) -> str:
    agent_names = await _decide_routing(user_message, history)

    tasks = [
        AGENT_HANDLERS[name](user_message, customer_id, token, history)
        for name in agent_names
    ]
    results = await asyncio.gather(*tasks)

    if len(results) == 1:
        return results[0]

    combined = "\n\n".join(
        f"[{name}]: {answer}" for name, answer in zip(agent_names, results)
    )
    merge_response = client.chat.completions.create(
        model=config.AZURE_CHAT_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": (
                    "Combine these separate answers from different bank support "
                    "agents into ONE natural, coherent reply to the customer. "
                    "Do not mention the internal agent names."
                ),
            },
            {"role": "user", "content": combined},
        ],
    )
    return merge_response.choices[0].message.content