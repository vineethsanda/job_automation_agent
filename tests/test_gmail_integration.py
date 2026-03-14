"""Integration test for Gmail MCP client and orchestrator."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from mcp_clients.gmail_client import GmailMCPClient
from dotenv import load_dotenv


async def test_gmail_connection():
    """Test Gmail connection."""
    print("\n" + "="*70)
    print("TEST 1: Gmail Connection")
    print("="*70)
    
    load_dotenv()
    
    email = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not email or not password:
        print("❌ FAIL: Gmail credentials not found in environment")
        print("   Please set GMAIL_ADDRESS and GMAIL_APP_PASSWORD")
        return False
    
    print(f"Connecting to: {email}")
    
    client = GmailMCPClient(email, password)
    result = await client.connect()
    
    if result:
        print("✅ PASS: Gmail connection successful")
        await client.disconnect()
        return True
    else:
        print("❌ FAIL: Failed to connect to Gmail")
        return False


async def test_fetch_unread_emails():
    """Test fetching unread emails."""
    print("\n" + "="*70)
    print("TEST 2: Fetch Unread Emails")
    print("="*70)
    
    load_dotenv()
    
    email = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not email or not password:
        print("❌ FAIL: Gmail credentials not found")
        return False
    
    client = GmailMCPClient(email, password)
    
    if not await client.connect():
        print("❌ FAIL: Could not connect to Gmail")
        return False
    
    result = await client.fetch_unread_emails(mailbox="INBOX", max_results=5)
    
    if result["status"] == "success":
        count = result["count"]
        print(f"✅ PASS: Fetched {count} unread emails")
        
        if count > 0:
            for i, email_data in enumerate(result["emails"][:2], 1):
                print(f"\n   Email {i}:")
                print(f"   From: {email_data.get('from', 'Unknown')}")
                print(f"   Subject: {email_data.get('subject', 'No subject')}")
                print(f"   Body preview: {email_data.get('body', '')[:100]}...")
        
        await client.disconnect()
        return True
    else:
        print(f"❌ FAIL: {result.get('error', 'Unknown error')}")
        await client.disconnect()
        return False


async def test_read_email_thread():
    """Test reading email thread."""
    print("\n" + "="*70)
    print("TEST 3: Read Email Thread")
    print("="*70)
    
    load_dotenv()
    
    email = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not email or not password:
        print("❌ FAIL: Gmail credentials not found")
        return False
    
    client = GmailMCPClient(email, password)
    
    if not await client.connect():
        print("❌ FAIL: Could not connect to Gmail")
        return False
    
    # First get an email to read its thread
    result = await client.fetch_unread_emails(mailbox="INBOX", max_results=1)
    
    if result["status"] != "success" or result["count"] == 0:
        print("⚠️  SKIP: No unread emails to test thread reading")
        await client.disconnect()
        return True
    
    subject = result["emails"][0].get("subject", "Test")
    
    thread_result = await client.read_email_thread(subject, max_messages=3)
    
    if thread_result["status"] == "success":
        count = thread_result["count"]
        print(f"✅ PASS: Read thread with {count} messages")
        print(f"   Subject: {subject}")
        
        await client.disconnect()
        return True
    else:
        print(f"❌ FAIL: {thread_result.get('error', 'Unknown error')}")
        await client.disconnect()
        return False


async def test_send_reply():
    """Test sending an email reply."""
    print("\n" + "="*70)
    print("TEST 4: Send Email Reply")
    print("="*70)
    
    load_dotenv()
    
    email = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    test_recipient = os.getenv("TEST_RECIPIENT_EMAIL")
    
    if not email or not password:
        print("❌ FAIL: Gmail credentials not found")
        return False
    
    if not test_recipient:
        print("⚠️  SKIP: TEST_RECIPIENT_EMAIL not set")
        print("   Set it in .env to test sending emails")
        return True
    
    client = GmailMCPClient(email, password)
    
    if not await client.connect():
        print("❌ FAIL: Could not connect to Gmail")
        return False
    
    result = await client.send_email_reply(
        to_address=test_recipient,
        subject="Test Reply",
        body="This is a test email sent from the Gmail integration test.\n\nBest regards"
    )
    
    if result["status"] == "success":
        print(f"✅ PASS: Email sent successfully")
        print(f"   To: {test_recipient}")
        print(f"   Subject: {result['subject']}")
        
        await client.disconnect()
        return True
    else:
        print(f"❌ FAIL: {result.get('error', 'Unknown error')}")
        await client.disconnect()
        return False


async def run_all_tests():
    """Run all integration tests."""
    print("\n")
    logger.info("Starting Gmail Integration Tests")
    
    results = []
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<level>{level: <8}</level> | {message}",
        level="INFO",
    )
    
    # Run tests
    results.append(("Gmail Connection", await test_gmail_connection()))
    results.append(("Fetch Unread Emails", await test_fetch_unread_emails()))
    results.append(("Read Email Thread", await test_read_email_thread()))
    results.append(("Send Email Reply", await test_send_reply()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
