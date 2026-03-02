"""
Intent Extraction using LLM-Assisted Reasoning
Parses user questions into structured intent for query planning
Supports OpenAI, Anthropic, and Ollama (local LLM)
"""

import os
import json
import re
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Try to import OpenAI, Anthropic
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class ExtractedIntent:
    """Structured representation of user intent"""
    metric: str
    board: str
    time_range: str
    group_by: Optional[str]
    filters: Dict[str, Any]
    comparison: Optional[str]
    assumptions: list
    raw_question: str
    llm_provider: str = "unknown"


class IntentExtractor:
    """Extracts structured intent using LLM-Assisted Reasoning"""
    
    AVAILABLE_METRICS = [
        "pipeline_health", "pipeline_value", "deal_count", "conversion_rate",
        "sector_performance", "revenue_at_risk", "stalled_deals",
        "work_order_status", "completion_rate", "revenue_by_sector",
        "cross_board_insight"
    ]
    
    AVAILABLE_BOARDS = ["Deals", "Work Orders", "Both"]
    
    TIME_RANGES = ["current_week", "current_month", "current_quarter", "ytd", "all_time", "custom"]
    
    GROUP_BY_OPTIONS = ["sector", "stage", "status", "month", "quarter"]
    
    def __init__(self, preferred_provider: str = "auto"):
        self.openai_client = None
        self.anthropic_client = None
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.preferred_provider = preferred_provider
        
        # Initialize available clients
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def _get_available_provider(self) -> str:
        """Determine which LLM provider is available"""
        if self.openai_client:
            return "openai"
        elif self.anthropic_client:
            return "anthropic"
        elif self._check_ollama():
            return "ollama"
        return "local"
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def extract_intent(self, question: str) -> ExtractedIntent:
        """Main entry point for LLM-Assisted intent extraction"""
        provider = self._get_available_provider()
        
        # Try LLM-based extraction first
        if provider in ["openai", "anthropic", "ollama"]:
            try:
                return self._llm_extraction(question, provider)
            except Exception as e:
                # Fall back to local reasoning on error
                pass
        
        # Local LLM-Assisted fallback
        return self._local_llm_extraction(question)
    
    def _llm_extraction(self, question: str, provider: str) -> ExtractedIntent:
        """Use LLM to extract structured intent - supports OpenAI, Anthropic, Ollama"""
        
        prompt = f"""You are a business intelligence query parser.

Convert the user question into structured JSON with:
- metric: the business metric to analyze
- board: which board (deals, work_orders, or both)
- time_range: time period for analysis
- grouping: how to group results
- assumptions: list of assumptions made

User question:
"{question}"

Available metrics: {', '.join(self.AVAILABLE_METRICS)}
Available boards: {', '.join(self.AVAILABLE_BOARDS)}
Time ranges: {', '.join(self.TIME_RANGES)}
Group by options: {', '.join(self.GROUP_BY_OPTIONS)}

Respond with ONLY a JSON object in this exact format:
{{
    "metric": "...",
    "board": "...",
    "time_range": "...",
    "grouping": "...",
    "assumptions": ["..."]
}}

Rules:
- "pipeline" questions = "deals" board, metric = "pipeline_health"
- "work order" questions = "work_orders" board
- "sector" questions = grouping = "sector"
- "this quarter" = "current_quarter"
- "underperforming" or "stuck" = look for stalled/low conversion
- Make reasonable assumptions if ambiguous, document them
"""
        
        content = ""
        
        if provider == "openai" and self.openai_client:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise BI intent parser."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content
            
        elif provider == "anthropic" and self.anthropic_client:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text
            
        elif provider == "ollama":
            # Call Ollama API
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    },
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                content = result.get("response", "")
            except Exception as e:
                raise ValueError(f"Ollama error: {e}")
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            raise ValueError("No valid JSON found in LLM response")
        
        # Normalize board name
        board = parsed.get("board", "Deals")
        if board.lower() in ["deals", "deal"]:
            board = "Deals"
        elif board.lower() in ["work_orders", "work_order", "work orders"]:
            board = "Work Orders"
        elif board.lower() == "both":
            board = "Both"
        
        # Map grouping to group_by
        group_by = parsed.get("grouping") or parsed.get("group_by")
        
        return ExtractedIntent(
            metric=parsed.get("metric", "pipeline_health"),
            board=board,
            time_range=parsed.get("time_range", "current_quarter"),
            group_by=group_by,
            filters=parsed.get("filters", {}),
            comparison=parsed.get("comparison"),
            assumptions=parsed.get("assumptions", []),
            raw_question=question,
            llm_provider=provider
        )
    
    def _local_llm_extraction(self, question: str) -> ExtractedIntent:
        """Local LLM-Assisted reasoning when no external LLM available"""
        q_lower = question.lower()
        assumptions = []
        
        # Determine board using structured reasoning
        if "work order" in q_lower:
            board = "Work Orders"
            reasoning = "Explicit 'work order' mention detected"
        elif "deal" in q_lower or "pipeline" in q_lower:
            board = "Deals"
            reasoning = "Explicit 'deal' or 'pipeline' mention detected"
        else:
            board = "Deals"  # default
            reasoning = "No explicit board mentioned, defaulting to Deals"
            assumptions.append(f"No board specified - assumed Deals (reasoning: {reasoning})")
        
        # Determine metric using keyword patterns
        if "pipeline" in q_lower and "health" in q_lower:
            metric = "pipeline_health"
        elif "pipeline" in q_lower:
            metric = "pipeline_health"
        elif "sector" in q_lower and "underperform" in q_lower:
            metric = "sector_performance"
        elif "stuck" in q_lower or "stalled" in q_lower:
            metric = "stalled_deals"
        elif "revenue" in q_lower and "risk" in q_lower:
            metric = "revenue_at_risk"
        elif "cross" in q_lower or "both" in q_lower:
            metric = "cross_board_insight"
        elif "sector" in q_lower:
            metric = "sector_performance"
        else:
            metric = "pipeline_health"
            assumptions.append(f"Metric ambiguous - assumed pipeline_health based on context")
        
        # Determine time range
        if "this quarter" in q_lower or "quarter" in q_lower:
            time_range = "current_quarter"
        elif "this month" in q_lower or "month" in q_lower:
            time_range = "current_month"
        elif "ytd" in q_lower or "year to date" in q_lower:
            time_range = "ytd"
        elif "week" in q_lower:
            time_range = "current_week"
        else:
            time_range = "all_time"
            assumptions.append("No time range specified - defaulting to all time")
        
        # Determine grouping
        if "sector" in q_lower:
            group_by = "sector"
        elif "stage" in q_lower:
            group_by = "stage"
        elif "status" in q_lower:
            group_by = "status"
        elif board == "Deals":
            group_by = "stage"
        else:
            group_by = "status"
        
        return ExtractedIntent(
            metric=metric,
            board=board,
            time_range=time_range,
            group_by=group_by,
            filters={},
            comparison=None,
            assumptions=assumptions,
            raw_question=question,
            llm_provider="local"
        )
    
    def get_extraction_log(self, intent: ExtractedIntent) -> Dict:
        """Generate human-readable log of extraction with LLM provider info"""
        return {
            "parsed_intent": {
                "metric": intent.metric,
                "board": intent.board,
                "time_range": intent.time_range,
                "group_by": intent.group_by,
                "filters": intent.filters,
                "comparison": intent.comparison
            },
            "assumptions": intent.assumptions,
            "llm_provider": intent.llm_provider,
            "llm_assisted": intent.llm_provider != "local"
        }
