"""Agent tool registry for Claude Code integration."""
from typing import Dict, Callable, List, Any

# Import all tool definitions
from .gemini import ALL_GEMINI_TOOLS
from .kimi import ALL_KIMI_TOOLS

# Import execution functions
from .gemini.multimodal import (
    gemini_analyze_image,
    gemini_analyze_video,
    gemini_extract_document
)
from .gemini.code_execution import gemini_execute_code
from .kimi.long_context import kimi_load_codebase


class AgentRegistry:
    """Registry for all agent tools."""

    def __init__(self):
        self.tools: List[Dict[str, Any]] = []
        self.executors: Dict[str, Callable] = {}

        # Register all tools
        self._register_gemini_tools()
        self._register_kimi_tools()

    def _register_gemini_tools(self):
        """Register Gemini tools."""
        # Add tool definitions
        self.tools.extend(ALL_GEMINI_TOOLS)

        # Register executors
        self.executors["gemini_analyze_image"] = gemini_analyze_image
        self.executors["gemini_analyze_video"] = gemini_analyze_video
        self.executors["gemini_extract_document"] = gemini_extract_document
        self.executors["gemini_execute_code"] = gemini_execute_code

    def _register_kimi_tools(self):
        """Register Kimi tools."""
        # Add tool definitions
        self.tools.extend(ALL_KIMI_TOOLS)

        # Register executors
        self.executors["kimi_load_codebase"] = kimi_load_codebase

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for Claude Code.

        Returns:
            List of tool definition dicts
        """
        return self.tools

    def execute_tool(self, tool_name: str, **params) -> Dict[str, Any]:
        """Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            **params: Tool parameters

        Returns:
            Dict with result

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self.executors:
            return {
                "success": False,
                "output": f"Tool not found: {tool_name}",
                "error": "Tool not registered or not implemented yet"
            }

        try:
            return self.executors[tool_name](**params)
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }

    def list_tools(self) -> List[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return [tool["name"] for tool in self.tools]

    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get information about a specific tool.

        Args:
            tool_name: Name of tool

        Returns:
            Tool definition dict or None
        """
        for tool in self.tools:
            if tool["name"] == tool_name:
                return tool
        return None


# Singleton instance
_registry = None


def get_registry() -> AgentRegistry:
    """Get singleton AgentRegistry instance."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
