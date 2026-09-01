"""
Central config - loads environment variables once, everything else imports from here.
"""

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env', encoding='utf-8-sig')

AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
AZURE_CHAT_DEPLOYMENT = os.getenv('AZURE_CHAT_DEPLOYMENT')
JWT_SECRET = os.getenv('JWT_SECRET')

_required = {
    'AZURE_OPENAI_ENDPOINT': AZURE_OPENAI_ENDPOINT,
    'AZURE_OPENAI_API_KEY': AZURE_OPENAI_API_KEY,
    'AZURE_OPENAI_API_VERSION': AZURE_OPENAI_API_VERSION,
    'AZURE_CHAT_DEPLOYMENT': AZURE_CHAT_DEPLOYMENT,
    'JWT_SECRET': JWT_SECRET,
}
missing = [k for k, v in _required.items() if not v]
if missing:
    raise RuntimeError(f'Missing required environment variables: {missing}')

ACCOUNTS_MCP_URL = 'http://127.0.0.1:8000/accounts/mcp'
TRANSACTIONS_MCP_URL = 'http://127.0.0.1:8000/transactions/mcp'
SERVICE_MCP_URL = 'http://127.0.0.1:8000/service/mcp'