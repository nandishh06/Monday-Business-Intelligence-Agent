"""
Monday.com MCP Client
Handles MCP-based integration with Monday.com using Model Context Protocol
Replaces direct GraphQL API calls with standardized MCP tool calls
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.types import CallToolResult
except ImportError:
    logging.warning("MCP package not installed. Falling back to API client.")
    ClientSession = None
    StdioServerParameters = None
    CallToolResult = None


class MondayMCPClient:
    """Client for Monday.com MCP integration with same interface as MondayClient"""
    
    def __init__(self, api_token: Optional[str] = None, mcp_server_url: Optional[str] = None):
        self.api_token = api_token or os.getenv("MONDAY_API_TOKEN")
        self.mcp_server_url = mcp_server_url or os.getenv("MONDAY_MCP_SERVER_URL", "https://api.monday.com/mcp")
        
        if not self.api_token:
            raise ValueError("Monday.com API token required")
        
        self.session = None
        self.last_call_log = {}
        self._is_connected = False
        
        # Initialize MCP session if available
        if ClientSession:
            asyncio.create_task(self._initialize_mcp_session())
    
    async def _initialize_mcp_session(self):
        """Initialize MCP session with Monday.com server"""
        try:
            # Connect to Monday.com MCP server
            server_params = StdioServerParameters(
                command="node",
                args=["@mondaydotcomorg/monday-api-mcp"],
                env={
                    "MONDAY_API_TOKEN": self.api_token,
                    "MONDAY_MCP_SERVER_URL": self.mcp_server_url
                }
            )
            
            self.session = ClientSession(server_params)
            await self.session.initialize()
            self._is_connected = True
            
        except Exception as e:
            logging.error(f"Failed to initialize MCP session: {e}")
            self._is_connected = False
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call MCP tool with logging"""
        if not self._is_connected or not self.session:
            raise RuntimeError("MCP session not initialized")
        
        # Log the MCP call
        self.last_call_log = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "arguments": arguments,
            "method": "mcp"
        }
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            
            self.last_call_log["status"] = "success"
            self.last_call_log["response_size"] = len(str(result))
            
            # Extract content from MCP result
            if hasattr(result, 'content') and result.content:
                return json.loads(result.content[0].text) if result.content else {}
            
            return result
            
        except Exception as e:
            self.last_call_log["status"] = "error"
            self.last_call_log["error"] = str(e)
            raise
    
    def get_boards(self) -> List[Dict]:
        """Fetch all accessible boards using MCP"""
        if not self._is_connected:
            return asyncio.run(self._fallback_get_boards())
        
        return asyncio.run(self._mcp_get_boards())
    
    async def _mcp_get_boards(self) -> List[Dict]:
        """Get boards via MCP"""
        arguments = {
            "include_columns": True,
            "include_items": False
        }
        
        result = await self._call_mcp_tool("list_boards", arguments)
        return result.get("boards", [])
    
    async def _fallback_get_boards(self) -> List[Dict]:
        """Fallback to direct API if MCP not available"""
        # Import here to avoid circular dependency
        from monday_client import MondayClient
        client = MondayClient(self.api_token)
        return client.get_boards()
    
    def get_board_items(self, board_id: str, limit: int = 500) -> List[Dict]:
        """Fetch all items from a specific board using MCP"""
        if not self._is_connected:
            return asyncio.run(self._fallback_get_board_items(board_id, limit))
        
        return asyncio.run(self._mcp_get_board_items(board_id, limit))
    
    async def _mcp_get_board_items(self, board_id: str, limit: int) -> List[Dict]:
        """Get board items via MCP"""
        arguments = {
            "board_id": board_id,
            "limit": limit,
            "include_column_values": True
        }
        
        result = await self._call_mcp_tool("get_board_items", arguments)
        items = result.get("items", [])
        
        # Update log with board info
        self.last_call_log["board_queried"] = result.get("board_name", "Unknown")
        self.last_call_log["items_fetched"] = len(items)
        
        return items
    
    async def _fallback_get_board_items(self, board_id: str, limit: int) -> List[Dict]:
        """Fallback to direct API if MCP not available"""
        from monday_client import MondayClient
        client = MondayClient(self.api_token)
        return client.get_board_items(board_id, limit)
    
    def get_board_columns(self, board_id: str) -> List[Dict]:
        """Get column metadata for a board using MCP"""
        if not self._is_connected:
            return asyncio.run(self._fallback_get_board_columns(board_id))
        
        return asyncio.run(self._mcp_get_board_columns(board_id))
    
    async def _mcp_get_board_columns(self, board_id: str) -> List[Dict]:
        """Get board columns via MCP"""
        arguments = {
            "board_id": board_id
        }
        
        result = await self._call_mcp_tool("get_board_columns", arguments)
        return result.get("columns", [])
    
    async def _fallback_get_board_columns(self, board_id: str) -> List[Dict]:
        """Fallback to direct API if MCP not available"""
        from monday_client import MondayClient
        client = MondayClient(self.api_token)
        return client.get_board_columns(board_id)
    
    def get_last_call_log(self) -> Dict:
        """Return log of the most recent MCP call"""
        return self.last_call_log
    
    def is_connected(self) -> bool:
        """Check if MCP session is connected"""
        return self._is_connected
    
    async def test_connection(self) -> bool:
        """Test MCP connection"""
        try:
            await self._call_mcp_tool("ping", {})
            return True
        except:
            return False


# Factory function to create appropriate client
def create_monday_client(use_mcp: bool = True, **kwargs) -> 'MondayMCPClient':
    """Create Monday client with MCP or API fallback"""
    if use_mcp and ClientSession:
        return MondayMCPClient(**kwargs)
    else:
        # Fallback to original API client
        from monday_client import MondayClient
        return MondayClient(**kwargs)
