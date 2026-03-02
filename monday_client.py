"""
Monday.com GraphQL API Client
Handles LIVE API calls to Monday.com - no caching or preloading
"""

import requests
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class MondayClient:
    """Client for Monday.com GraphQL API with full logging"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("MONDAY_API_TOKEN")
        if not self.api_token:
            raise ValueError("Monday.com API token required")
        
        self.base_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "API-Version": "2024-01"
        }
        self.last_call_log = {}
    
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query with full logging"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        # Log the API call
        self.last_call_log = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:500] + "..." if len(query) > 500 else query,
            "variables": variables
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            self.last_call_log["status"] = "success"
            self.last_call_log["response_size"] = len(str(result))
            
            if "errors" in result:
                self.last_call_log["errors"] = result["errors"]
                
            return result
            
        except requests.exceptions.RequestException as e:
            self.last_call_log["status"] = "error"
            self.last_call_log["error"] = str(e)
            raise
    
    def get_boards(self) -> List[Dict]:
        """Fetch all accessible boards"""
        query = """
        query {
            boards {
                id
                name
                description
                columns {
                    id
                    title
                    type
                }
            }
        }
        """
        result = self._execute_query(query)
        return result.get("data", {}).get("boards", [])
    
    def get_board_items(self, board_id: str, limit: int = 500) -> List[Dict]:
        """Fetch all items from a specific board with column values"""
        query = """
        query GetBoardItems($boardId: [ID!], $limit: Int) {
            boards(ids: $boardId) {
                id
                name
                items_page(limit: $limit) {
                    items {
                        id
                        name
                        column_values {
                            id
                            text
                            value
                            column {
                                title
                                type
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {"boardId": board_id, "limit": limit}
        result = self._execute_query(query, variables)
        
        boards = result.get("data", {}).get("boards", [])
        if not boards:
            return []
        
        items = boards[0].get("items_page", {}).get("items", [])
        self.last_call_log["board_queried"] = boards[0].get("name", "Unknown")
        self.last_call_log["items_fetched"] = len(items)
        
        return items
    
    def get_board_columns(self, board_id: str) -> List[Dict]:
        """Get column metadata for a board"""
        query = """
        query GetBoardColumns($boardId: [ID!]) {
            boards(ids: $boardId) {
                columns {
                    id
                    title
                    type
                    settings_str
                }
            }
        }
        """
        variables = {"boardId": board_id}
        result = self._execute_query(query, variables)
        
        boards = result.get("data", {}).get("boards", [])
        if boards:
            return boards[0].get("columns", [])
        return []
    
    def get_last_call_log(self) -> Dict:
        """Return log of the most recent API call"""
        return self.last_call_log
