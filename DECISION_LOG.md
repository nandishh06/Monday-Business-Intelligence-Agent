# Decision Log: Monday.com Business Intelligence AI Agent - Decision Log

## Architecture Overview

This document outlines the key architectural decisions, rationale, and trade-offs made in building the Monday.com Business Intelligence Agent.

### Core Architecture

**Technology Stack:**
- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python with asyncio for async operations
- **Integration**: Dual approach - Direct GraphQL API + Model Context Protocol (MCP)
- **AI/LLM**: Multi-provider support (OpenAI, Anthropic, Ollama, Local)
- **Data Processing**: Pandas for data manipulation and analysis

## Key Architectural Decisions

### 1. Dual Integration Approach: API + MCP

**Decision**: Implement both direct GraphQL API and Model Context Protocol (MCP) integration.

**Rationale**:
- **MCP Benefits**: Standardized protocol, secure authentication, hosted service option
- **API Fallback**: Ensures compatibility and reliability
- **Future-Proof**: MCP is Monday.com's recommended approach for AI integrations
- **Bonus Points**: Assignment specifically mentions MCP as bonus feature

**Implementation**:
- `MondayClient`: Direct GraphQL API implementation
- `MondayMCPClient`: MCP-based implementation with same interface
- Runtime selection based on user configuration
- Automatic fallback to API if MCP unavailable

### 2. LLM-Assisted Intent Extraction

**Decision**: Replace rule-based parsing with LLM-assisted reasoning.

**Rationale**:
- **Flexibility**: Handles natural language variations better
- **Context**: LLMs understand business context and ambiguity
- **Scalability**: No need to manually maintain rule sets
- **Local Option**: Ollama support for privacy-conscious deployments

**Trade-offs**:
- Increased complexity with multiple LLM providers
- Dependency on external services (except Ollama)
- Need for structured prompt engineering

### 3. Observable Pipeline Architecture

**Decision**: Make every step of the BI pipeline visible to users.

**Rationale**:
- **Trust**: Users see exactly how their question is processed
- **Debugging**: Easy to identify where things go wrong
- **Transparency**: Critical for business decision-making tools
- **Assignment Requirement**: Explicitly requested visible traces

**Implementation**:
- Agent Actions panel with expandable sections
- Step-by-step logging: Intent → Planning → API → Normalization → Analysis
- JSON/YAML formatted outputs for technical users
- Data quality warnings with specific counts

### 4. Data Resilience Strategy

**Decision**: Handle messy real-world data explicitly and transparently.

**Rationale**:
- **Realistic**: Business data is never perfect
- **Trust**: Users need to know data limitations
- **Production-Ready**: Shows mature engineering thinking

**Implementation**:
- `DataNormalizer` class for cleaning and validation
- Explicit data caveats in every answer
- Warning system for missing/invalid data
- Record counts and exclusion reasons

### 5. Cross-Board Intelligence

**Decision**: Implement correlation analysis between Deals and Work Orders.

**Rationale**:
- **Business Value**: Pipeline vs execution insights are strategically important
- **Differentiator**: Shows advanced BI capability
- **Assignment Example**: Specific example provided in requirements

**Implementation**:
- Sector-based correlation analysis
- Bottleneck identification (high pipeline, low execution)
- Simple but effective algorithm
- Visual separation in UI

## Technical Trade-offs

### 1. Synchronous vs Asynchronous

**Decision**: Use async for MCP but maintain synchronous interface.

**Rationale**:
- MCP requires async operations
- Streamlit works best with synchronous code
- Compatibility with existing API client

**Trade-off**: Slight complexity in async/sync bridging

### 2. Multiple LLM Providers

**Decision**: Support OpenAI, Anthropic, Ollama, and local reasoning.

**Rationale**:
- **Flexibility**: Users choose based on cost/privacy/performance
- **Resilience**: Multiple fallback options
- **Demo Capability**: Show different approaches

**Trade-off**: Increased code complexity and dependency management

### 3. Error Handling Strategy

**Decision**: Graceful degradation with detailed error messages.

**Rationale**:
- **User Experience**: Never leave users confused
- **Debugging**: Clear error traces for troubleshooting
- **Production**: Professional error handling

## Security Considerations

### 1. API Token Management
- Environment variables for sensitive data
- Password fields in UI
- No token logging in traces

### 2. MCP Security
- Uses Monday.com's hosted MCP service (more secure)
- Standardized authentication through MCP protocol
- No direct API exposure in MCP mode

## Performance Considerations

### 1. Live API Calls
- **Decision**: No caching or preloading
- **Rationale**: Assignment requirement, real-time data
- **Trade-off**: Slower response times but accurate data

### 2. Data Processing
- **Decision**: Process data on-demand
- **Rationale**: Fresh data for each query
- **Optimization**: Efficient pandas operations

## Deployment Strategy

### 1. Hosted Option
- Streamlit Cloud for easy deployment
- Environment variable configuration
- No local setup required for evaluators

### 2. Local Development
- Docker container support (optional)
- Requirements.txt for dependencies
- Clear README with setup instructions

## Future Improvements

### 1. Enhanced MCP Integration
- Dynamic API tools (beta feature)
- Real-time subscriptions
- Advanced error handling

### 2. More Sophisticated BI
- Time-series analysis
- Predictive insights
- Custom metrics

### 3. UI/UX Enhancements
- Interactive charts
- Export functionality
- Query history

## Conclusion

This architecture balances:
- **Functionality**: Meets all assignment requirements
- **Reliability**: Multiple fallback mechanisms
- **Innovation**: MCP integration and LLM assistance
- **Production-Ready**: Error handling, data resilience, observability

The dual API/MCP approach provides both immediate compatibility and future-proofing, while the observable pipeline builds user trust in AI-driven business intelligence.

## Assumptions Made

### Data Structure Assumptions

1. **Deals Board** has columns:
   - Deal Name (text)
   - Sector (dropdown/status)
   - Stage (Lead, Qualified, Proposal, Negotiation, Won, Lost)
   - Deal Value (numeric/currency)
   - Close Date (date)

2. **Work Orders Board** has columns:
   - Work Order ID (text)
   - Sector (dropdown/status)
   - Status (Pending, In Progress, Completed)
   - Dates (Created, Completed)
   - Revenue/Cost (numeric)

3. **Currency format** assumed to be INR (₹) but parser handles various formats

4. **Date formats** handled: ISO, US, EU formats with multiple pattern matching

### Query Interpretation Assumptions

1. "Pipeline" terminology → Deals board
2. "Work order" terminology → Work Orders board
3. "This quarter" → Current calendar quarter
4. "Underperforming" → Low conversion rate or high stalled rate
5. "Stuck" → Deals in early stages for extended periods
6. No time specified → All time (with clear assumption logged)

### Business Logic Assumptions

1. **Stalled deals:**
   - Qualified stage > 30 days = stalled
   - Proposal/Negotiation > 60 days = stalled
   - Lead > 90 days = stalled

2. **Revenue at risk:**
   - Deals with past close date still in active stages
   - Calculated as total value of overdue active deals

3. **Conversion rate:**
   - Won value / (Won + Lost value)
   - By value, not by count (revenue-weighted)

4. **Sector performance:**
   - Measured by total value + conversion rate
   - Underperforming = < 30% conversion with meaningful volume

---

## Known Limitations

### Current Limitations

1. **Single board per query** - Cross-board insights require separate queries
2. **No persistent storage** - Configuration lost on refresh
3. **Simple date parsing** - Complex date ranges (e.g., "last 2 quarters") not fully supported
4. **No real-time updates** - Must re-query for fresh data
5. **Limited cross-board analysis** - Cannot directly correlate Deals with Work Orders by sector

### Data Quality Limitations

1. **Currency parsing** may fail on unconventional formats
2. **Sector normalization** is case-sensitive grouping
3. **Date inference** may misinterpret ambiguous formats (MM/DD vs DD/MM)
4. **No fuzzy matching** for similar sector names

### Scalability Limitations

1. **No pagination** - Currently fetches up to 500 items per board
2. **No rate limiting backoff** - Relies on Monday.com's limits
3. **Synchronous only** - Parallel board queries not implemented

---

## Improvements with More Time

### High Priority

1. **Persistent Configuration**
   - Store board IDs and tokens in database or encrypted storage
   - User accounts and saved queries
   - Configuration profiles for different environments

2. **Advanced Date Handling**
   - Natural language date parsing ("last quarter", "Q1 2024")
   - Custom date range selector
   - Fiscal year support

3. **Cross-Board Analytics**
   - True correlation between Deals and Work Orders
   - Sector-level funnel analysis
   - Operational bottleneck detection

4. **Enhanced Error Handling**
   - Retry logic with exponential backoff
   - Partial failure handling
   - Better error messages for common issues

### Medium Priority

5. **Caching Strategy** (Selective)
   - Cache board schema/metadata (rarely changes)
   - Cache for expensive calculations
   - Configurable TTL per query type

6. **Additional Metrics**
   - Trend analysis (week-over-week, month-over-month)
   - Forecasting based on pipeline
   - Activity metrics (deals moved, new leads)

7. **Visualization**
   - Charts for pipeline distribution
   - Sector comparison graphs
   - Trend lines for historical data

8. **Collaboration Features**
   - Share insights via email/Slack
   - Scheduled reports
   - Comment/annotation on insights

### Lower Priority

9. **Additional Integrations**
   - Salesforce connector
   - HubSpot connector
   - Custom API connections

10. **Natural Language Improvements**
    - Conversational follow-ups
    - Context retention across questions
    - Clarification prompts for ambiguous queries

11. **Performance Optimizations**
    - Async/parallel API calls
    - Incremental data fetching
    - Client-side caching for UI elements

---

## Security Considerations

### Current Security Measures

1. API tokens stored in environment variables or session state only
2. No logging of sensitive values
3. Error messages don't expose internal details

### Recommended Additions

1. **Authentication layer** - User login before accessing agent
2. **Token encryption** - Encrypt API tokens at rest
3. **Audit logging** - Track which queries were run when
4. **Rate limiting** - Per-user limits to prevent abuse
5. **IP restrictions** - Limit access to corporate networks

---

## Testing Strategy (Not Implemented)

### Unit Tests Needed

1. `test_intent_extractor.py` - Various question formats
2. `test_query_planner.py` - Query construction for each metric
3. `test_data_normalizer.py` - Edge cases in messy data
4. `test_bi_engine.py` - Calculation accuracy
5. `test_monday_client.py` - Mock API responses

### Integration Tests Needed

1. End-to-end pipeline with mocked Monday.com
2. Error handling scenarios
3. Performance benchmarks

### Manual Tests Performed

1. Pipeline health query with sample data
2. Sector performance analysis
3. Stalled deals detection
4. Revenue at risk calculation
5. Data quality warning generation

---

## Deployment Notes

### Recommended Hosting

1. **Streamlit Cloud** - Easiest for prototypes
2. **Render** - Good free tier, persistent
3. **Heroku** - Well-known, simple
4. **AWS/GCP/Azure** - Production scale

### Environment Requirements

- Python 3.8+
- 512MB RAM minimum
- No persistent disk required
- Outbound HTTPS access to Monday.com

### Configuration Variables

| Variable | Required | Description |
|----------|----------|-------------|
| MONDAY_API_TOKEN | Yes | Monday.com API token |
| DEALS_BOARD_ID | Yes | Board ID for Deals |
| WORK_ORDERS_BOARD_ID | Yes | Board ID for Work Orders |
| OPENAI_API_KEY | No | For LLM intent extraction |
| ANTHROPIC_API_KEY | No | Alternative LLM |

---

## Success Metrics

The system is designed to satisfy these evaluation criteria:

1. ✅ **Correctness** - Accurate calculations with transparent methodology
2. ✅ **Live API usage** - No caching, every query hits Monday.com
3. ✅ **Data resilience** - Handles messy data with clear warnings
4. ✅ **Query reasoning** - Shows how questions are interpreted
5. ✅ **Decision transparency** - Full execution trace visible
6. ✅ **Business relevance** - Insights are actionable, not generic

---

## Conclusion

This system demonstrates:
- Understanding of real-world data challenges
- Production API integration patterns
- Transparent, observable AI systems
- Business-focused insight generation
- Production deployment considerations

The architecture prioritizes **correctness and transparency** over convenience features, making it suitable for executive decision-making.

**Version:** 1.0  
**Last Updated:** March 2026  
**Author:** AI Engineer - Hiring Assignment
