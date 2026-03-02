# Existing Monday.com Boards Integration

## Current Situation
- User already has CSV files imported into Monday.com boards
- Deals and Work Orders boards are already created
- Need to integrate BI agent with existing boards using provided links

## What's Needed from User

Please provide:
1. **Deals Board Link**: `https://<team>.monday.com/boards/<DEALS_BOARD_ID>`
2. **Work Orders Board Link**: `https://<team>.monday.com/boards/<WORK_ORDERS_BOARD_ID>`

## Integration Steps

### 1. Extract Board IDs
From your Monday.com board URLs:
- Extract the numeric ID after `/boards/`
- Example: `https://company.monday.com/boards/123456789` → Board ID = `123456789`

### 2. Configure BI Agent
Add board IDs to:
- **Sidebar Configuration** → **Connected Data Sources**
- **Deals Board ID**: Your deals board ID
- **Work Orders Board ID**: Your work orders board ID

### 3. Test Integration
Run queries to verify:
- Live API connectivity to your boards
- Data retrieval from your actual data
- Agent Actions panel shows real API calls

## Expected Results

The agent will:
✅ Connect to YOUR existing Monday.com boards
✅ Analyze YOUR actual business data
✅ Show live API traces with YOUR data
✅ Handle messy data from YOUR real boards
✅ Provide insights based on YOUR business metrics

## No Sample Files Needed

Since you have existing boards:
- ❌ No need for sample CSV files
- ❌ No need for import instructions
- ✅ Just need board IDs to connect

## Ready for Evaluation

Once board IDs are configured:
- Agent is production-ready
- Live API calls to your boards
- Full functionality with your real data
- All assignment requirements met
