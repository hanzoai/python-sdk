"""Tests for AI tool detection functionality."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hanzo.tools.detector import AITool, ToolDetector


class TestToolDetector(unittest.TestCase):
    """Test AI tool detection functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = ToolDetector()
    
    def test_tool_initialization(self):
        """Test that tools are properly initialized."""
        # Check that we have tools defined
        self.assertGreater(len(self.detector.TOOLS), 0)
        
        # Check that each tool has required attributes
        for tool in self.detector.TOOLS:
            self.assertIsInstance(tool.name, str)
            self.assertIsInstance(tool.display_name, str)
            self.assertIsInstance(tool.provider, str)
            self.assertIsInstance(tool.priority, int)
            self.assertIsInstance(tool.detected, bool)
    
    def test_priority_ordering(self):
        """Test that tools have correct priority ordering."""
        tools = self.detector.TOOLS
        
        # Find specific tools
        hanzod = next((t for t in tools if t.name == "hanzod"), None)
        hanzo_router = next((t for t in tools if t.name == "hanzo-router"), None)
        claude_code = next((t for t in tools if t.name == "claude-code"), None)
        
        # Hanzo Node should have highest priority (0)
        if hanzod:
            self.assertEqual(hanzod.priority, 0)
        
        # Router should have high priority
        if hanzo_router:
            self.assertLessEqual(hanzo_router.priority, 2)
        
        # Claude Code should have reasonable priority
        if claude_code:
            self.assertLessEqual(claude_code.priority, 5)
    
    @patch('hanzo.tools.detector.httpx.post')
    def test_hanzod_detection_success(self, mock_post):
        """Test successful Hanzo Node detection."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response
        
        hanzod = AITool(
            name="hanzod",
            command="hanzo node",
            display_name="Hanzo Node",
            provider="hanzo-local",
            priority=0,
            api_endpoint="http://localhost:3690/health"
        )
        
        result = self.detector.detect_tool(hanzod)
        self.assertTrue(result)
        self.assertTrue(hanzod.detected)
    
    @patch('hanzo.tools.detector.httpx.post')
    def test_hanzod_detection_failure_404(self, mock_post):
        """Test Hanzo Node detection fails on 404."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response
        
        hanzod = AITool(
            name="hanzod",
            command="hanzo node",
            display_name="Hanzo Node",
            provider="hanzo-local",
            priority=0,
            api_endpoint="http://localhost:3690/health"
        )
        
        result = self.detector.detect_tool(hanzod)
        self.assertFalse(result)
        self.assertFalse(hanzod.detected)
    
    @patch('hanzo.tools.detector.httpx.post')
    def test_hanzod_detection_connection_refused(self, mock_post):
        """Test Hanzo Node detection handles connection refused."""
        import httpx
        # Mock connection error
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        hanzod = AITool(
            name="hanzod",
            command="hanzo node",
            display_name="Hanzo Node",
            provider="hanzo-local",
            priority=0,
            api_endpoint="http://localhost:3690/health"
        )
        
        result = self.detector.detect_tool(hanzod)
        self.assertFalse(result)
        self.assertFalse(hanzod.detected)
    
    @patch('hanzo.tools.detector.shutil.which')
    def test_command_detection(self, mock_which):
        """Test command-based tool detection."""
        # Mock command exists
        mock_which.return_value = "/usr/local/bin/claude"
        
        claude_tool = AITool(
            name="claude-code",
            command="claude",
            display_name="Claude Code",
            provider="anthropic",
            priority=3,
            check_command="claude"
        )
        
        result = self.detector.detect_tool(claude_tool)
        self.assertTrue(result)
        self.assertTrue(claude_tool.detected)
        
        # Mock command doesn't exist
        mock_which.return_value = None
        claude_tool.detected = False
        
        result = self.detector.detect_tool(claude_tool)
        self.assertFalse(result)
        self.assertFalse(claude_tool.detected)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('hanzo.tools.detector.shutil.which')
    def test_env_var_detection(self, mock_which):
        """Test environment variable based detection."""
        mock_which.return_value = "/usr/local/bin/openai"
        
        openai_tool = AITool(
            name="openai",
            command="openai",
            display_name="OpenAI Codex",
            provider="openai",
            priority=4,
            check_command="openai",
            env_var="OPENAI_API_KEY"
        )
        
        result = self.detector.detect_tool(openai_tool)
        self.assertTrue(result)
        self.assertTrue(openai_tool.detected)
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all env vars
    @patch('hanzo.tools.detector.shutil.which')
    def test_env_var_missing(self, mock_which):
        """Test that tool is still detected when command exists but env var is missing.
        
        The tool detection logic checks for command existence first,
        and env_var is only a fallback. A tool can be "detected" but
        may not be fully functional without the API key.
        """
        mock_which.return_value = "/usr/local/bin/openai"
        
        openai_tool = AITool(
            name="openai",
            command="openai",
            display_name="OpenAI Codex",
            provider="openai",
            priority=4,
            check_command="openai",
            env_var="OPENAI_API_KEY"
        )
        
        result = self.detector.detect_tool(openai_tool)
        # Tool is detected because command exists, even without API key
        self.assertTrue(result)
        self.assertTrue(openai_tool.detected)
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all env vars
    @patch('hanzo.tools.detector.shutil.which')
    def test_no_command_no_env_var(self, mock_which):
        """Test detection fails when neither command nor env var exists."""
        mock_which.return_value = None  # Command doesn't exist
        
        openai_tool = AITool(
            name="openai",
            command="openai",
            display_name="OpenAI Codex",
            provider="openai",
            priority=4,
            check_command="openai",
            env_var="OPENAI_API_KEY"
        )
        
        result = self.detector.detect_tool(openai_tool)
        self.assertFalse(result)
        self.assertFalse(openai_tool.detected)
    
    @patch('hanzo.tools.detector.subprocess.run')
    @patch('hanzo.tools.detector.shutil.which')
    def test_version_detection(self, mock_which, mock_run):
        """Test version detection for tools."""
        mock_which.return_value = "/usr/local/bin/hanzo"
        
        # Mock version command output
        mock_result = Mock()
        mock_result.stdout = "hanzo version 0.3.23\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        hanzo_tool = AITool(
            name="hanzo-dev",
            command="hanzo dev",
            display_name="Hanzo Dev",
            provider="hanzo",
            priority=2,
            check_command="hanzo"
        )
        
        result = self.detector.detect_tool(hanzo_tool)
        self.assertTrue(result)
        self.assertIn("0.3.23", hanzo_tool.version or "")
    
    @patch('hanzo.tools.detector.httpx.post')
    @patch('hanzo.tools.detector.shutil.which')
    def test_detect_all(self, mock_which, mock_post):
        """Test detecting all available tools."""
        # Mock some tools as available
        def which_side_effect(cmd):
            if cmd in ["claude", "hanzo", "openai"]:
                return f"/usr/local/bin/{cmd}"
            return None
        
        mock_which.side_effect = which_side_effect
        
        # Mock Hanzo Node as not running
        import httpx
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        # Set OpenAI API key for testing
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            detected_tools = self.detector.detect_all()
        
        # Should have detected some tools
        self.assertGreater(len(detected_tools), 0)
        
        # Check that detected tools are marked as such
        for tool in detected_tools:
            if tool.name in ["claude-code", "hanzo-dev", "openai"]:
                self.assertTrue(tool.detected, f"{tool.name} should be detected")
            elif tool.name == "hanzod":
                self.assertFalse(tool.detected, "hanzod should not be detected")
    
    def test_get_default_tool(self):
        """Test getting the default tool."""
        # Create mock tools with different priorities (already sorted)
        tools = [
            AITool("tool2", "cmd2", "Tool 2", "provider2", priority=2, detected=True),
            AITool("tool4", "cmd4", "Tool 4", "provider4", priority=3, detected=True),
            AITool("tool1", "cmd1", "Tool 1", "provider1", priority=5, detected=True),
        ]
        
        self.detector.detected_tools = tools
        
        # Default should be the first tool (tool2 with priority 2)
        default = self.detector.get_default_tool()
        self.assertIsNotNone(default)
        self.assertEqual(default.name, "tool2")
        self.assertEqual(default.priority, 2)
    
    def test_get_default_tool_none_detected(self):
        """Test get_default_tool returns None when no tools detected."""
        # Empty detected_tools list
        self.detector.detected_tools = []
        
        # Mock detect_all to return empty list
        with patch.object(self.detector, 'detect_all', return_value=[]):
            default = self.detector.get_default_tool()
            self.assertIsNone(default)
    
    @patch('hanzo.tools.detector.httpx.post')
    def test_port_fallback_for_hanzod(self, mock_post):
        """Test that Hanzo Node tries both port 3690 and 8000."""
        import httpx
        
        # First call to port 3690 fails, second to 8000 succeeds
        responses = [
            httpx.ConnectError("Connection refused"),  # Port 3690 fails
            Mock(status_code=200)  # Port 8000 succeeds
        ]
        mock_post.side_effect = responses
        
        hanzod = AITool(
            name="hanzod",
            command="hanzo node",
            display_name="Hanzo Node",
            provider="hanzo-local",
            priority=0,
            api_endpoint="http://localhost:3690/health"
        )
        
        result = self.detector.detect_tool(hanzod)
        
        # Should have tried both ports
        self.assertEqual(mock_post.call_count, 2)
        
        # Check that both ports were tried
        calls = mock_post.call_args_list
        urls = [call[0][0] for call in calls]
        self.assertIn("http://localhost:3690/v1/chat/completions", urls)
        self.assertIn("http://localhost:8000/v1/chat/completions", urls)


if __name__ == "__main__":
    unittest.main()