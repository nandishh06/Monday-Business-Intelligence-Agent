"""
Query Planner
Translates extracted intent into Monday.com query parameters
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from intent_extractor import ExtractedIntent


@dataclass
class QueryPlan:
    """Structured query plan for Monday.com API"""
    board_name: str
    board_id: Optional[str]
    required_columns: List[str]
    column_mapping: Dict[str, str]  # internal_name -> monday_column_title
    filters: Dict[str, Any]
    time_range: Dict[str, Any]
    group_by: Optional[str]
    assumptions: List[str]
    query_description: str


class QueryPlanner:
    """Plans Monday.com queries based on extracted intent"""
    
    # Known column patterns for our boards
    DEALS_COLUMNS = {
        "name": "Deal Name",
        "sector": "Sector",
        "stage": "Stage",
        "value": "Deal Value",
        "close_date": "Close Date",
        "status": "Status"
    }
    
    WORK_ORDER_COLUMNS = {
        "name": "Work Order ID",
        "sector": "Sector",
        "status": "Status",
        "created_date": "Created Date",
        "completed_date": "Completed Date",
        "revenue": "Revenue",
        "cost": "Cost"
    }
    
    def __init__(self, board_ids: Optional[Dict[str, str]] = None):
        """
        Initialize with board ID mappings
        board_ids: {"Deals": "123456789", "Work Orders": "987654321"}
        """
        self.board_ids = board_ids or {}
    
    def create_plan(self, intent: ExtractedIntent) -> QueryPlan:
        """Create a query plan from extracted intent"""
        assumptions = list(intent.assumptions)
        
        # Determine board
        board_name = intent.board
        board_id = self.board_ids.get(board_name)
        
        # Build column mapping based on board
        if board_name == "Deals":
            column_mapping = self.DEALS_COLUMNS.copy()
        elif board_name == "Work Orders":
            column_mapping = self.WORK_ORDER_COLUMNS.copy()
        else:
            # For "Both", we'll start with Deals
            column_mapping = self.DEALS_COLUMNS.copy()
            board_id = self.board_ids.get("Deals")
        
        # Determine required columns based on metric
        required_columns = self._get_required_columns(intent.metric, column_mapping)
        
        # Build time range filters
        time_range = self._build_time_range(intent.time_range)
        if intent.time_range != "all_time":
            assumptions.append(f"Time range interpreted as {intent.time_range}")
        
        # Build query description
        query_description = self._build_description(intent)
        
        # Add metric-specific assumptions
        if intent.metric == "pipeline_health":
            assumptions.append("Pipeline health interpreted as total deal value grouped by stage")
        elif intent.metric == "sector_performance":
            assumptions.append("Sector performance measured by deal count and total value")
        elif intent.metric == "stalled_deals":
            assumptions.append("Stalled deals = deals in Qualified stage for >30 days or Won/Lost older than expected")
        
        return QueryPlan(
            board_name=board_name,
            board_id=board_id,
            required_columns=required_columns,
            column_mapping=column_mapping,
            filters=intent.filters,
            time_range=time_range,
            group_by=intent.group_by,
            assumptions=assumptions,
            query_description=query_description
        )
    
    def _get_required_columns(self, metric: str, column_mapping: Dict) -> List[str]:
        """Determine which columns are needed for the metric"""
        base_columns = ["name"]
        
        if metric in ["pipeline_health", "pipeline_value", "revenue_at_risk", "stalled_deals"]:
            base_columns.extend(["stage", "value", "sector", "close_date"])
        elif metric == "sector_performance":
            base_columns.extend(["sector", "value", "stage"])
        elif metric == "conversion_rate":
            base_columns.extend(["stage", "value", "sector"])
        elif metric == "work_order_status":
            base_columns.extend(["status", "sector", "created_date", "completed_date"])
        elif metric == "completion_rate":
            base_columns.extend(["status", "created_date", "completed_date", "revenue"])
        elif metric == "cross_board_insight":
            base_columns.extend(["sector", "status", "value"])
        
        # Map to actual Monday column titles
        return [column_mapping.get(col, col) for col in base_columns]
    
    def _build_time_range(self, time_range_str: str) -> Dict[str, Any]:
        """Convert time range string to date filters"""
        today = datetime.now()
        
        if time_range_str == "current_week":
            start = today - timedelta(days=today.weekday())
            return {"start": start, "end": today, "label": "This Week"}
        
        elif time_range_str == "current_month":
            start = today.replace(day=1)
            return {"start": start, "end": today, "label": "This Month"}
        
        elif time_range_str == "current_quarter":
            quarter = (today.month - 1) // 3
            start_month = quarter * 3 + 1
            start = today.replace(month=start_month, day=1)
            return {"start": start, "end": today, "label": "This Quarter"}
        
        elif time_range_str == "ytd":
            start = today.replace(month=1, day=1)
            return {"start": start, "end": today, "label": "Year to Date"}
        
        else:  # all_time
            return {"start": None, "end": None, "label": "All Time"}
    
    def _build_description(self, intent: ExtractedIntent) -> str:
        """Create human-readable description of the query"""
        parts = [
            f"Querying {intent.board} board",
            f"for {intent.metric.replace('_', ' ')}"
        ]
        
        if intent.time_range != "all_time":
            parts.append(f"during {intent.time_range.replace('_', ' ')}")
        
        if intent.group_by:
            parts.append(f"grouped by {intent.group_by}")
        
        return " ".join(parts)
    
    def get_plan_log(self, plan: QueryPlan) -> Dict[str, Any]:
        """Generate human-readable log of query plan"""
        return {
            "board": plan.board_name,
            "board_id": plan.board_id or "Not configured - will need to be set",
            "required_columns": plan.required_columns,
            "filters": plan.filters,
            "time_range": plan.time_range.get("label"),
            "group_by": plan.group_by,
            "query_description": plan.query_description,
            "assumptions": plan.assumptions
        }
