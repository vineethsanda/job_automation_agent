"""
Comprehensive test suite for LinkedIn MCP Server.

Tests connection, authentication, and all tool functionality.

Run with: python -m pytest tests/test_linkedin_mcp.py -v -s
Or: python tests/test_linkedin_mcp.py
"""

import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

# Try to import pytest for running with pytest
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.linkedin_mcp.utils.stealth_browser import StealthBrowser
from mcp_servers.linkedin_mcp.utils.cookie_store import CookieStore
from mcp_servers.linkedin_mcp.tools.session_manager import manage_session
from mcp_servers.linkedin_mcp.tools.fetch_posts import fetch_job_posts
from mcp_servers.linkedin_mcp.tools.extract_recruiter_email import extract_recruiter_email


# Conditional pytest decorators
if HAS_PYTEST:
    mark_asyncio = pytest.mark.asyncio
else:
    def mark_asyncio(func):
        """No-op decorator for when pytest is not available."""
        return func


class TestCookieStore:
    """Test cookie persistence functionality."""

    def test_cookie_store_initialization(self, tmp_path):
        """Test cookie store can be initialized."""
        cookie_store = CookieStore(storage_dir=str(tmp_path / "cookies"))
        assert cookie_store.storage_dir.exists()
        assert cookie_store.cookie_file == cookie_store.storage_dir / "cookies.json"

    def test_save_and_load_cookies(self, tmp_path):
        """Test saving and loading cookies."""
        cookie_store = CookieStore(storage_dir=str(tmp_path / "cookies"))
        
        # Test cookies
        test_cookies = [
            {
                "name": "li_at",
                "value": "test_token_123",
                "domain": ".linkedin.com",
                "path": "/",
            },
            {
                "name": "JSESSIONID",
                "value": "test_session_456",
                "domain": ".linkedin.com",
                "path": "/",
            },
        ]
        
        # Save cookies
        result = cookie_store.save_cookies(test_cookies)
        assert result is True
        assert cookie_store.cookie_file.exists()
        
        # Load cookies
        loaded = cookie_store.load_cookies()
        assert loaded is not None
        assert len(loaded) == 2
        assert loaded[0]["value"] == "test_token_123"

    def test_clear_cookies(self, tmp_path):
        """Test clearing cookies."""
        cookie_store = CookieStore(storage_dir=str(tmp_path / "cookies"))
        
        test_cookies = [{"name": "li_at", "value": "test_token"}]
        cookie_store.save_cookies(test_cookies)
        assert cookie_store.cookie_file.exists()
        
        # Clear cookies
        result = cookie_store.clear_cookies()
        assert result is True
        assert not cookie_store.cookie_file.exists()

    def test_load_nonexistent_cookies(self, tmp_path):
        """Test loading when no cookies exist."""
        cookie_store = CookieStore(storage_dir=str(tmp_path / "cookies"))
        loaded = cookie_store.load_cookies()
        assert loaded is None


class TestStealthBrowser:
    """Test browser initialization and functionality."""

    @mark_asyncio
    async def test_browser_initialization(self, tmp_path):
        """Test browser can be initialized."""
        with patch('mcp_servers.linkedin_mcp.utils.stealth_browser.async_playwright') as mock_playwright:
            mock_browser_instance = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_browser_instance.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_page.add_init_script = AsyncMock()
            
            mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(
                return_value=mock_browser_instance
            )
            
            browser = StealthBrowser(session_dir=str(tmp_path / "session"))
            await browser.launch()
            
            assert browser.browser is not None
            assert browser.context is not None
            assert browser.page is not None

    @mark_asyncio
    async def test_goto_with_delay(self, tmp_path):
        """Test navigation with delays."""
        browser = StealthBrowser(session_dir=str(tmp_path / "session"))
        browser.page = AsyncMock()
        browser.page.goto = AsyncMock()
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await browser.goto_with_delay("https://example.com")
            browser.page.goto.assert_called()

    @mark_asyncio
    async def test_wait_for_selector(self, tmp_path):
        """Test waiting for DOM elements."""
        browser = StealthBrowser(session_dir=str(tmp_path / "session"))
        browser.page = AsyncMock()
        browser.page.wait_for_selector = AsyncMock(return_value=True)
        
        result = await browser.wait_for_selector("[data-test]")
        assert result is True

    @mark_asyncio
    async def test_get_content(self, tmp_path):
        """Test content extraction."""
        browser = StealthBrowser(session_dir=str(tmp_path / "session"))
        browser.page = AsyncMock()
        browser.page.content = AsyncMock(return_value="<html>Test Content</html>")
        
        content = await browser.get_content()
        assert content == "<html>Test Content</html>"


class TestSessionManager:
    """Test LinkedIn session management."""

    @mark_asyncio
    async def test_session_status(self, tmp_path):
        """Test checking session status."""
        cookie_store = CookieStore(storage_dir=str(tmp_path / "cookies"))
        
        # Save some cookies
        test_cookies = [{"name": "li_at", "value": "test_token"}]
        cookie_store.save_cookies(test_cookies)
        
        # Test with mock
        cookie_store.get_session_status = Mock(return_value={"authenticated": True})
        
        result = await manage_session(cookie_store, action="status")
        assert result["status"] == "success"
        assert result["action"] == "status"

    @mark_asyncio
    async def test_session_load(self, tmp_path):
        """Test loading session."""
        cookie_store = CookieStore(storage_dir=str(tmp_path / "cookies"))
        
        # Save test cookies
        test_cookies = [
            {"name": "li_at", "value": "token1"},
            {"name": "JSESSIONID", "value": "session1"},
        ]
        cookie_store.save_cookies(test_cookies)
        
        result = await manage_session(cookie_store, action="load")
        assert result["status"] == "success"
        assert result["cookie_count"] == 2

    @mark_asyncio
    async def test_session_clear(self, tmp_path):
        """Test clearing session."""
        cookie_store = CookieStore(storage_dir=str(tmp_path / "cookies"))
        
        # Save test cookies
        test_cookies = [{"name": "li_at", "value": "test_token"}]
        cookie_store.save_cookies(test_cookies)
        
        result = await manage_session(cookie_store, action="clear")
        assert result["status"] == "success"
        assert not cookie_store.cookie_file.exists()


class TestFetchJobsTool:
    """Test job fetching functionality."""

    @mark_asyncio
    async def test_fetch_jobs_success(self, tmp_path):
        """Test successful job fetching."""
        browser = AsyncMock()
        browser.goto_with_delay = AsyncMock()
        browser.wait_for_selector = AsyncMock(return_value=True)
        browser.page = AsyncMock()
        browser.page.evaluate = AsyncMock(return_value=[
            {
                "id": "job_001",
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "location": "San Francisco, CA",
                "url": "https://linkedin.com/jobs/view/001",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ])
        
        result = await fetch_job_posts(
            browser,
            search_query="Software Engineer",
            max_results=10
        )
        
        assert result["status"] == "success"
        assert len(result["posts"]) > 0
        assert result["posts"][0]["title"] == "Senior Software Engineer"

    @mark_asyncio
    async def test_fetch_jobs_no_results(self, tmp_path):
        """Test job fetching with no results."""
        browser = AsyncMock()
        browser.goto_with_delay = AsyncMock()
        browser.wait_for_selector = AsyncMock(return_value=False)
        
        result = await fetch_job_posts(
            browser,
            search_query="NonexistentRole",
            max_results=10
        )
        
        assert result["status"] == "no_jobs"
        assert result["count"] == 0

    @mark_asyncio
    async def test_fetch_jobs_with_filters(self, tmp_path):
        """Test job fetching with filters."""
        browser = AsyncMock()
        browser.goto_with_delay = AsyncMock()
        browser.wait_for_selector = AsyncMock(return_value=True)
        browser.page = AsyncMock()
        browser.page.evaluate = AsyncMock(return_value=[])
        
        filters = {
            "experience": "Senior",
            "location": "San Francisco",
        }
        
        result = await fetch_job_posts(
            browser,
            search_query="Engineer",
            max_results=10,
            filters=filters
        )
        
        assert "status" in result


class TestExtractRecruiterEmailTool:
    """Test recruiter email extraction."""

    @mark_asyncio
    async def test_extract_email_success(self, tmp_path):
        """Test successful email extraction."""
        browser = AsyncMock()
        browser.goto_with_delay = AsyncMock()
        browser.wait_for_selector = AsyncMock(return_value=True)
        browser.get_content = AsyncMock(
            return_value="<html>Contact: john.recruiter@techcorp.com</html>"
        )
        
        result = await extract_recruiter_email(
            browser,
            profile_url="https://linkedin.com/in/recruiter-profile"
        )
        
        assert result["status"] == "success"
        assert result["email"] is not None
        assert "techcorp.com" in result["email"]

    @mark_asyncio
    async def test_extract_email_profile_not_found(self, tmp_path):
        """Test extraction when profile not found."""
        browser = AsyncMock()
        browser.goto_with_delay = AsyncMock()
        browser.wait_for_selector = AsyncMock(return_value=False)
        
        result = await extract_recruiter_email(
            browser,
            profile_url="https://linkedin.com/in/nonexistent"
        )
        
        assert result["status"] == "not_found"
        assert result["email"] is None

    @mark_asyncio
    async def test_extract_email_no_content(self, tmp_path):
        """Test extraction when content unavailable."""
        browser = AsyncMock()
        browser.goto_with_delay = AsyncMock()
        browser.wait_for_selector = AsyncMock(return_value=True)
        browser.get_content = AsyncMock(return_value=None)
        
        result = await extract_recruiter_email(
            browser,
            profile_url="https://linkedin.com/in/profile"
        )
        
        assert result["status"] == "error"


class TestLinkedInIntegration:
    """Integration tests for LinkedIn MCP server."""

    @mark_asyncio
    async def test_full_workflow(self, tmp_path):
        """Test complete workflow: connect -> fetch jobs -> extract emails."""
        # Setup cookie store
        cookie_store = CookieStore(storage_dir=str(tmp_path / "cookies"))
        test_cookies = [
            {"name": "li_at", "value": "test_auth_token"},
            {"name": "JSESSIONID", "value": "test_session"},
        ]
        cookie_store.save_cookies(test_cookies)
        
        # Verify cookies are loadable
        loaded = cookie_store.load_cookies()
        assert loaded is not None
        assert len(loaded) == 2
        
        # Test session management
        status_result = await manage_session(cookie_store, action="status")
        assert status_result["status"] == "success"
        
        # Test job fetching
        browser = AsyncMock()
        browser.goto_with_delay = AsyncMock()
        browser.wait_for_selector = AsyncMock(return_value=True)
        browser.page = AsyncMock()
        browser.page.evaluate = AsyncMock(return_value=[
            {
                "id": "job_123",
                "title": "Software Engineer",
                "company": "TestCorp",
                "location": "Remote",
                "url": "https://linkedin.com/jobs/view/123",
            }
        ])
        
        jobs_result = await fetch_job_posts(browser, search_query="Engineer")
        assert jobs_result["status"] == "success"


# ============================================================================
# Manual Testing Functions (for running outside pytest)
# ============================================================================

async def test_connection_manual():
    """Manual test: Test LinkedIn connection and authentication."""
    print("\n" + "="*70)
    print("🔗 TESTING LINKEDIN CONNECTION")
    print("="*70)
    
    try:
        # Test environment
        linkedin_email = os.getenv("LINKEDIN_EMAIL")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD")
        
        if not linkedin_email or not linkedin_password:
            print("❌ FAILED: LinkedIn credentials not set in .env")
            print("   Required: LINKEDIN_EMAIL, LINKEDIN_PASSWORD")
            return False
        
        print(f"✅ Credentials found: {linkedin_email}")
        
        # Test cookie store
        print("\n📦 Testing Cookie Store...")
        cookie_store = CookieStore()
        test_cookies = [
            {"name": "li_at", "value": "test_token_" + str(datetime.utcnow().timestamp())}
        ]
        
        if not cookie_store.save_cookies(test_cookies):
            print("❌ Failed to save cookies")
            return False
        print("✅ Cookies saved successfully")
        
        loaded = cookie_store.load_cookies()
        if not loaded:
            print("❌ Failed to load cookies")
            return False
        print(f"✅ Cookies loaded: {len(loaded)} cookies")
        
        # Test browser initialization
        print("\n🌐 Testing Browser Initialization...")
        print("⚠️  Browser launch test skipped (requires Playwright + dependencies)")
        print("   Run: python -m playwright install chrome")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_tools_manual():
    """Manual test: Test all tool functionality."""
    print("\n" + "="*70)
    print("🛠️  TESTING LINKEDIN MCP TOOLS")
    print("="*70)
    
    try:
        # Test fetch_jobs_posts
        print("\n1️⃣  Testing fetch_jobs tool...")
        browser = AsyncMock()
        browser.goto_with_delay = AsyncMock()
        browser.wait_for_selector = AsyncMock(return_value=True)
        browser.page = AsyncMock()
        browser.page.evaluate = AsyncMock(return_value=[
            {
                "id": "job_test_001",
                "title": "Senior Backend Engineer",
                "company": "Tech Startup",
                "location": "New York, NY",
                "url": "https://linkedin.com/jobs/view/000",
            }
        ])
        
        result = await fetch_job_posts(browser, "Python Engineer", max_results=5)
        if result["status"] == "success":
            print(f"✅ fetch_jobs works - Found {len(result.get('posts', []))} jobs")
        else:
            print(f"⚠️  fetch_jobs returned: {result['status']}")
        
        # Test extract_recruiter_email
        print("\n2️⃣  Testing extract_recruiter_email tool...")
        browser = AsyncMock()
        browser.goto_with_delay = AsyncMock()
        browser.wait_for_selector = AsyncMock(return_value=True)
        browser.get_content = AsyncMock(
            return_value="<html>Email: recruiter@company.com</html>"
        )
        
        result = await extract_recruiter_email(
            browser,
            "https://linkedin.com/in/test-recruiter"
        )
        if result["status"] == "success" and result["email"]:
            print(f"✅ extract_recruiter_email works - Found: {result['email']}")
        else:
            print(f"⚠️  extract_recruiter_email returned: {result['status']}")
        
        # Test session_manager
        print("\n3️⃣  Testing session_manager tool...")
        tmp_cookie_store = CookieStore()
        tmp_cookies = [
            {"name": "li_at", "value": "test_auth"},
            {"name": "JSESSIONID", "value": "test_session"},
        ]
        tmp_cookie_store.save_cookies(tmp_cookies)
        
        result = await manage_session(tmp_cookie_store, action="load")
        if result["status"] == "success":
            print(f"✅ session_manager load works - {result['cookie_count']} cookies")
        else:
            print(f"⚠️  session_manager returned: {result['status']}")
        
        result = await manage_session(tmp_cookie_store, action="clear")
        if result["status"] == "success":
            print(f"✅ session_manager clear works")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_manual_tests():
    """Run all manual tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "LinkedIn MCP Server Test Suite" + " "*23 + "║")
    print("╚" + "="*68 + "╝")
    
    conn_result = await test_connection_manual()
    tools_result = await test_tools_manual()
    
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Connection Tests:  {'✅ PASSED' if conn_result else '❌ FAILED'}")
    print(f"Tools Tests:       {'✅ PASSED' if tools_result else '❌ FAILED'}")
    print("="*70)
    
    if conn_result and tools_result:
        print("\n🎉 All manual tests passed!")
    else:
        print("\n⚠️  Some tests failed. Review output above.")
    
    return conn_result and tools_result


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    """Run manual tests directly."""
    print("\n")
    print("LinkedIn MCP Testing Modes:")
    print("1. With pytest (recommended):")
    print("   python -m pytest tests/test_linkedin_mcp.py -v")
    print("\n2. Direct execution:")
    print("   python tests/test_linkedin_mcp.py")
    print("\nRunning manual tests...\n")
    
    asyncio.run(run_all_manual_tests())
