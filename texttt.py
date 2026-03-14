import asyncio
from mcp_clients.gmail_client import GmailMCPClient
import os
from dotenv import load_dotenv
load_dotenv()

async def test():
    email = os.getenv('GMAIL_ADDRESS')
    password = os.getenv('GMAIL_APP_PASSWORD')
    
    print(f'Email: {email}')
    print(f'Password: {password}')
    
    if not email or not password:
        print('❌ Credentials missing in environment!')
        return
    
    client = GmailMCPClient(email, password)
    result = await client.connect()
    
    if result:
        print('✅ Gmail connection SUCCESS!')
        await client.disconnect()
    else:
        print('❌ Gmail connection FAILED - check credentials')

asyncio.run(test())

