"""
Monday.com Business Intelligence Agent
Main Streamlit Application
"""

import streamlit as st
import os
import json
from datetime import datetime

# Component imports
from monday_client import MondayClient
from intent_extractor import IntentExtractor, ExtractedIntent
from query_planner import QueryPlanner, QueryPlan
from data_normalizer import DataNormalizer, DataWarning
from bi_engine import BIEngine, BIResult

# Page configuration
st.set_page_config(
    page_title="Monday.com BI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #1f77b4;
    }
    .log-box {
        background-color: #f8f9fa;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 4px 4px 0;
    }
    .insight-card {
        background-color: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .risk-high { border-left: 4px solid #dc3545; }
    .risk-medium { border-left: 4px solid #ffc107; }
    .risk-low { border-left: 4px solid #28a745; }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 4px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #28a745;
        border-radius: 4px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "execution_log" not in st.session_state:
        st.session_state.execution_log = []
    if "api_calls" not in st.session_state:
        st.session_state.api_calls = []
    if "last_result" not in st.session_state:
        st.session_state.last_result = None


def log_step(step_name: str, details: dict):
    """Log a step in the execution pipeline"""
    st.session_state.execution_log.append({
        "timestamp": datetime.now().isoformat(),
        "step": step_name,
        "details": details
    })


def render_sidebar():
    """Render the sidebar with configuration"""
    with st.sidebar:
        st.markdown("### 🔌 Monday.com Connection")
        
        api_token = st.text_input(
            "API Token",
            type="password",
            value=os.getenv("MONDAY_API_TOKEN", ""),
            help="Your Monday.com API token"
        )
        
        if api_token:
            os.environ["MONDAY_API_TOKEN"] = api_token
        
        # Connection Method Selection
        st.markdown("### 🚀 Connection Method")
        connection_method = st.radio(
            "Choose Integration Method",
            ["Direct API (Recommended)", "MCP (Alternative)"],
            help="Direct API provides proven reliability with your existing boards"
        )
        
        # API Configuration (when API is selected)
        if connection_method == "Direct API (Recommended)":
            st.markdown('<div class="success-box">✅ Using Direct GraphQL API</div>', unsafe_allow_html=True)
            st.markdown("<small>🔗 Proven reliability with live Monday.com boards</small>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">⚠️ Using Model Context Protocol (MCP)</div>', unsafe_allow_html=True)
            st.markdown("<small>� Alternative integration method (experimental)</small>", unsafe_allow_html=True)
            
            mcp_server_url = st.text_input(
                "MCP Server URL (Optional)",
                value=os.getenv("MONDAY_MCP_SERVER_URL", ""),
                help="Leave blank for Monday.com hosted MCP service"
            )
            
            if mcp_server_url:
                os.environ["MONDAY_MCP_SERVER_URL"] = mcp_server_url
        
        st.markdown("---")
        
        # Board ID configuration
        st.markdown("### 📋 Connected Data Sources")
        
        deals_board = st.text_input(
            "Deals Board ID",
            value=os.getenv("DEALS_BOARD_ID", ""),
            help="Monday.com board ID for Deals"
        )
        
        work_orders_board = st.text_input(
            "Work Orders Board ID",
            value=os.getenv("WORK_ORDERS_BOARD_ID", ""),
            help="Monday.com board ID for Work Orders"
        )
        
        if deals_board:
            os.environ["DEALS_BOARD_ID"] = deals_board
        if work_orders_board:
            os.environ["WORK_ORDERS_BOARD_ID"] = work_orders_board
        
        st.markdown("---")
        st.markdown("<small>🔗 Connect your Monday.com boards to enable live analysis</small>", unsafe_allow_html=True)
        
        llm_provider = st.selectbox(
            "LLM Provider",
            ["LLM-Assisted (Local)", "OpenAI", "Anthropic", "Ollama"]
        )
        
        if llm_provider == "OpenAI":
            openai_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=os.getenv("OPENAI_API_KEY", "")
            )
            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key
        elif llm_provider == "Anthropic":
            anthropic_key = st.text_input(
                "Anthropic API Key",
                type="password",
                value=os.getenv("ANTHROPIC_API_KEY", "")
            )
            if anthropic_key:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        elif llm_provider == "Ollama":
            st.markdown("<small>Ollama URL: `http://localhost:11434`</small>", unsafe_allow_html=True)
            ollama_model = st.text_input(
                "Ollama Model",
                value=os.getenv("OLLAMA_MODEL", "llama3.2")
            )
            if ollama_model:
                os.environ["OLLAMA_MODEL"] = ollama_model
        
        st.markdown("---")
        st.markdown("#### 📊 Board Links")
        st.markdown("Configure your Monday.com board IDs above to connect.")
        
        return {
            "api_token": api_token,
            "deals_board": deals_board,
            "work_orders_board": work_orders_board,
            "llm_provider": llm_provider,
            "connection_method": connection_method,
            "mcp_server_url": mcp_server_url if connection_method == "MCP (Alternative)" else None
        }


def render_agent_actions_panel(intent, plan, api_log, warnings, valid_records, result):
    """Render the Agent Actions panel with all execution steps"""
    st.markdown('<div class="section-header">🤖 Agent Actions</div>', unsafe_allow_html=True)
    
    # Step 1: Parsed Intent
    with st.expander("🧠 Parsed Intent", expanded=True):
        st.markdown("**LLM Provider:** " + ("Local (LLM-Assisted)" if intent.llm_provider == "local" else intent.llm_provider.title()))
        st.json({
            "metric": intent.metric,
            "board": intent.board,
            "time_range": intent.time_range,
            "grouping": intent.group_by,
            "assumptions": intent.assumptions
        })
    
    # Step 2: Query Plan
    with st.expander("🗺️ Query Plan", expanded=True):
        st.markdown(f"**Query:** {plan.query_description}")
        st.code(f"""
Board: {plan.board_name} (ID: {plan.board_id})
Columns: {', '.join(plan.required_columns)}
Time Range: {plan.time_range.get('label')}
Group By: {plan.group_by}
        """.strip(), language="yaml")
    
    # Step 3: API Calls
    with st.expander("🔌 Monday.com API Calls", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            method = api_log.get("method", "API")
            method_emoji = "🔗" if method == "MCP" else "📡"
            st.markdown(f"**Method:** {method_emoji} {method}")
            
            st.json({
                "timestamp": api_log.get("timestamp"),
                "board": api_log.get("board_queried"),
                "items_fetched": api_log.get("items_fetched"),
                "status": api_log.get("status")
            })
        with col2:
            if api_log.get("status") == "success":
                st.success("✅ Live API Success")
            else:
                st.error("❌ API Failed")
    
    # Step 4: Data Quality Warnings
    with st.expander("⚠️ Data Quality Warnings", expanded=True):
        total_items = api_log.get("items_fetched", 0)
        valid_count = len(valid_records) if valid_records else 0
        excluded = total_items - valid_count
        
        st.markdown(f"**Records:** {valid_count} valid / {total_items} total ({excluded} excluded)")
        
        if warnings:
            for warning in warnings:
                st.warning(f"{warning.description}")
        else:
            st.success("✅ No data quality issues")
    
    # Step 5: Final Answer
    with st.expander("📊 Final Answer", expanded=True):
        st.markdown(f"### {result.summary}")
        
        st.markdown("**Key Insights:**")
        for insight in result.insights[:5]:
            emoji = "🚨" if insight.risk_level == "high" else "⚠️" if insight.risk_level == "medium" else "📊"
            st.markdown(f"{emoji} **{insight.title}:** {insight.value} — {insight.context}")
        
        # Data Caveats - EXPLICIT
        st.markdown("---")
        st.markdown("**Data Notes:**")
        if warnings:
            for warning in warnings:
                st.markdown(f"• {warning.description}")
        else:
            st.markdown("• All records passed validation")
        st.markdown(f"• Analysis based on {len(valid_records) if valid_records else 0} valid records")
        
        if result.recommendations:
            st.markdown("**Recommendations:**")
            for rec in result.recommendations:
                st.markdown(f"• {rec}")


def process_query(question: str, config: dict) -> tuple:
    """
    Execute the full BI pipeline
    Returns: (intent, plan, api_log, warnings, valid_records, result, cross_board_result)
    """
    # Initialize components
    intent_extractor = IntentExtractor()
    query_planner = QueryPlanner({
        "Deals": config["deals_board"],
        "Work Orders": config["work_orders_board"]
    })
    
    # Step 1: Intent Extraction
    intent = intent_extractor.extract_intent(question)
    log_step("Intent Extraction", intent_extractor.get_extraction_log(intent))
    
    # Step 2: Query Planning
    plan = query_planner.create_plan(intent)
    log_step("Query Planning", query_planner.get_plan_log(plan))
    
    # Step 3: API Call - Choose MCP or Direct API
    if not config["api_token"]:
        raise ValueError("Monday.com API token required")
    
    if not plan.board_id:
        raise ValueError(f"Board ID not configured for {plan.board_name}")
    
    # Use MCP if selected and available
    if config.get("connection_method") == "MCP (Alternative)":
        try:
            from monday_mcp_client import MondayMCPClient
            monday_client = MondayMCPClient(
                api_token=config["api_token"],
                mcp_server_url=config.get("mcp_server_url")
            )
            log_step("Connection Method", {"method": "MCP", "server": config.get("mcp_server_url", "Monday.com Hosted")})
        except ImportError:
            # Fallback to API client if MCP not available
            from monday_client import MondayClient
            monday_client = MondayClient(config["api_token"])
            log_step("Connection Method", {"method": "Direct API (MCP unavailable)"})
    else:
        from monday_client import MondayClient
        monday_client = MondayClient(config["api_token"])
        log_step("Connection Method", {"method": "Direct API"})
    
    raw_items = monday_client.get_board_items(plan.board_id)
    api_log = monday_client.get_last_call_log()
    log_step("API Call", api_log)
    
    # Step 4: Data Normalization
    normalizer = DataNormalizer()
    valid_records, warnings = normalizer.normalize_items(
        raw_items,
        plan.column_mapping,
        plan.time_range
    )
    log_step("Data Normalization", {"records_processed": len(raw_items), "valid_records": len(valid_records), "warnings": len(warnings)})
    
    # Step 5: BI Analysis
    bi_engine = BIEngine()
    result = bi_engine.analyze(intent.metric, valid_records, intent.group_by)
    log_step("BI Analysis", {"metric": result.metric, "insights_generated": len(result.insights)})
    
    # Step 6: Cross-board insight (if both boards available)
    cross_board_result = None
    if intent.metric == "cross_board_insight" and config["deals_board"] and config["work_orders_board"]:
        log_step("Cross-Board Analysis", {"status": "Fetching second board data"})
        # Fetch work orders data
        work_orders_raw = monday_client.get_board_items(config["work_orders_board"])
        work_orders_log = monday_client.get_last_call_log()
        
        work_orders_mapping = query_planner.WORK_ORDER_COLUMNS
        work_orders_valid, work_orders_warnings = normalizer.normalize_items(
            work_orders_raw, work_orders_mapping, plan.time_range
        )
        
        # Generate cross-board insight
        cross_board_result = bi_engine.analyze_cross_board(valid_records, work_orders_valid)
        log_step("Cross-Board Analysis", {"insight": cross_board_result.summary if cross_board_result else None})
    
    return intent, plan, api_log, warnings, valid_records, result, cross_board_result


def main():
    """Main application"""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">📊 Monday.com BI Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Production-ready Business Intelligence for founders and executives</div>', unsafe_allow_html=True)
    
    # Sidebar
    config = render_sidebar()
    
    # Main content
    st.markdown("---")
    
    # Example questions
    st.markdown("### 💬 Ask a Business Question")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        question = st.text_input(
            "Your question:",
            placeholder="e.g., How is our pipeline looking this quarter?",
            key="question_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.button("🔍 Run Live Analysis", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # Process query
    if submit and question:
        if not config["api_token"]:
            st.error("⚠️ Please configure your Monday.com API token in the sidebar")
            return
        
        if not config["deals_board"] and not config["work_orders_board"]:
            st.error("⚠️ Please configure at least one board ID in the sidebar")
            return
        
        with st.spinner("Analyzing... (Live API calls in progress)"):
            try:
                intent, plan, api_log, warnings, valid_records, result, cross_board_result = process_query(question, config)
                
                # Render Agent Actions Panel
                render_agent_actions_panel(intent, plan, api_log, warnings, valid_records, result)
                
                # Cross-board insight (if available)
                if cross_board_result:
                    st.markdown("---")
                    st.markdown('<div class="section-header">🔗 Cross-Board Insight</div>', unsafe_allow_html=True)
                    with st.expander("🎯 Pipeline → Execution Analysis", expanded=True):
                        st.markdown(f"### {cross_board_result.summary}")
                        for insight in cross_board_result.insights:
                            emoji = "🚨" if insight.risk_level == "high" else "⚠️" if insight.risk_level == "medium" else "💡"
                            st.markdown(f"{emoji} **{insight.title}:** {insight.value}")
                            st.markdown(f"   <small>{insight.context}</small>", unsafe_allow_html=True)
                
                # Store result
                st.session_state.last_result = {
                    "intent": intent,
                    "plan": plan,
                    "result": result,
                    "cross_board": cross_board_result,
                    "warnings": warnings,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    # Footer
    st.markdown("---")
    st.markdown("<small>🔒 All queries execute LIVE against Monday.com API — no caching or preloading</small>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
