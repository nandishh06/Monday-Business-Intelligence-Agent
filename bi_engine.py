"""
Business Intelligence Engine
Computes decision-grade insights from normalized data
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class Insight:
    """A single business insight"""
    type: str
    title: str
    value: Any
    context: str
    risk_level: Optional[str]  # "high", "medium", "low", None


@dataclass
class BIResult:
    """Complete result of BI analysis"""
    metric: str
    summary: str
    insights: List[Insight]
    data_quality_notes: List[str]
    recommendations: List[str]


class BIEngine:
    """Computes business intelligence metrics and insights"""
    
    def __init__(self):
        self.computation_log: List[str] = []
    
    def analyze(
        self,
        metric: str,
        records: List[Any],
        group_by: Optional[str] = None
    ) -> BIResult:
        """
        Main entry point: analyze records and produce insights
        """
        self.computation_log = []
        self.computation_log.append(f"Analyzing {len(records)} records for metric: {metric}")
        
        if metric == "pipeline_health":
            return self._analyze_pipeline_health(records, group_by)
        elif metric == "sector_performance":
            return self._analyze_sector_performance(records)
        elif metric == "stalled_deals":
            return self._analyze_stalled_deals(records)
        elif metric == "revenue_at_risk":
            return self._analyze_revenue_at_risk(records)
        elif metric == "conversion_rate":
            return self._analyze_conversion_rate(records, group_by)
        elif metric == "work_order_status":
            return self._analyze_work_order_status(records, group_by)
        elif metric == "completion_rate":
            return self._analyze_completion_rate(records)
        else:
            return self._generic_analysis(records, metric)
    
    def _analyze_pipeline_health(
        self,
        records: List[Any],
        group_by: Optional[str]
    ) -> BIResult:
        """Analyze pipeline health: total value, distribution by stage"""
        
        # Group by stage
        stage_data = defaultdict(lambda: {"count": 0, "value": 0.0, "records": []})
        total_value = 0.0
        total_count = 0
        
        for record in records:
            stage = record.fields.get("stage", "Unknown")
            value = record.fields.get("value", 0) or 0
            
            stage_data[stage]["count"] += 1
            stage_data[stage]["value"] += value
            stage_data[stage]["records"].append(record)
            total_value += value
            total_count += 1
        
        # Sort stages in logical pipeline order
        stage_order = ["Lead", "Qualified", "Proposal", "Negotiation", "Won", "Lost"]
        sorted_stages = sorted(
            stage_data.keys(),
            key=lambda s: stage_order.index(s) if s in stage_order else 99
        )
        
        # Build insights
        insights = []
        
        # Total pipeline
        insights.append(Insight(
            type="metric",
            title="Total Pipeline Value",
            value=f"₹{total_value/1_000_000:.2f}M" if total_value >= 1_000_000 else f"₹{total_value:,.0f}",
            context=f"Across {total_count} active deals",
            risk_level=None
        ))
        
        # Distribution by stage
        stuck_value = 0.0
        stuck_count = 0
        
        for stage in sorted_stages:
            data = stage_data[stage]
            pct_value = (data["value"] / total_value * 100) if total_value > 0 else 0
            pct_count = (data["count"] / total_count * 100) if total_count > 0 else 0
            
            # Identify stuck deals (Qualified or Proposal with high value)
            early_stage_keywords = ["qualified", "proposal", "feasibility", "commercial"]

            if any(k in stage.lower() for k in early_stage_keywords):
                stuck_value += data["value"]
                stuck_count += data["count"]
            
            insights.append(Insight(
                type="breakdown",
                title=f"{stage} Stage",
                value=f"₹{data['value']/1_000_000:.2f}M ({pct_value:.0f}%)",
                context=f"{data['count']} deals ({pct_count:.0f}%)",
                risk_level="medium" if stage == "Qualified" and pct_value > 50 else None
            ))
        
        # Risk identification
        recommendations = []
        if stuck_value / total_value > 0.5 if total_value > 0 else False:
            stuck_pct = stuck_value / total_value * 100
            insights.append(Insight(
                type="risk",
                title="Pipeline Bottleneck",
                value=f"{stuck_pct:.0f}% of value stuck in early stages",
                context=f"₹{stuck_value/1_000_000:.2f}M in Qualified/Proposal",
                risk_level="high"
            ))
            recommendations.append("Focus on moving Qualified deals to Proposal stage")
        
        # Won/Lost analysis
        won_data = stage_data.get("Won", {"value": 0, "count": 0})
        lost_data = stage_data.get("Lost", {"value": 0, "count": 0})
        
        closed_value = won_data["value"] + lost_data["value"]
        if closed_value > 0:
            win_rate = won_data["value"] / closed_value * 100
            insights.append(Insight(
                type="metric",
                title="Win Rate",
                value=f"{win_rate:.0f}%",
                context=f"₹{won_data['value']/1_000_000:.2f}M won, ₹{lost_data['value']/1_000_000:.2f}M lost",
                risk_level="high" if win_rate < 30 else "medium" if win_rate < 50 else None
            ))
        
        # Build summary
        summary = (
            f"Current pipeline value is ₹{total_value/1_000_000:.2f}M across {total_count} deals. "
            f"{stuck_value/total_value*100:.0f}% of value is in early stages (Qualified/Proposal)."
        ) if total_value > 0 else "No pipeline value found in specified period."
        
        return BIResult(
            metric="pipeline_health",
            summary=summary,
            insights=insights,
            data_quality_notes=[],
            recommendations=recommendations
        )
    
    def _analyze_sector_performance(self, records: List[Any]) -> BIResult:
        """Analyze performance by sector"""
        
        sector_data = defaultdict(lambda: {"count": 0, "value": 0.0, "won": 0, "lost": 0, "open": 0})
        
        for record in records:
            sector = record.fields.get("sector", "Unknown")
            value = record.fields.get("value", 0) or 0
            stage = record.fields.get("stage", "Unknown")
            
            sector_data[sector]["count"] += 1
            sector_data[sector]["value"] += value
            
            if stage == "Won":
                sector_data[sector]["won"] += value
            elif stage == "Lost":
                sector_data[sector]["lost"] += value
            else:
                sector_data[sector]["open"] += value
        
        # Sort by value
        sorted_sectors = sorted(
            sector_data.keys(),
            key=lambda s: sector_data[s]["value"],
            reverse=True
        )
        
        insights = []
        total_value = sum(d["value"] for d in sector_data.values())
        
        # Top and bottom performers
        if sorted_sectors:
            top_sector = sorted_sectors[0]
            top_data = sector_data[top_sector]
            insights.append(Insight(
                type="metric",
                title=f"Top Sector: {top_sector}",
                value=f"₹{top_data['value']/1_000_000:.2f}M",
                context=f"{top_data['count']} deals, {top_data['value']/total_value*100:.0f}% of total",
                risk_level=None
            ))
            
            if len(sorted_sectors) > 1:
                bottom_sector = sorted_sectors[-1]
                bottom_data = sector_data[bottom_sector]
                insights.append(Insight(
                    type="metric",
                    title=f"Lowest Sector: {bottom_sector}",
                    value=f"₹{bottom_data['value']/1_000_000:.2f}M",
                    context=f"{bottom_data['count']} deals",
                    risk_level="medium" if bottom_data["value"] > 0 else None
                ))
        
        # Sector breakdown
        for sector in sorted_sectors[:5]:  # Top 5
            data = sector_data[sector]
            closed_value = data["won"] + data["lost"]
            if closed_value > 0:
                conversion = data["won"] / closed_value * 100
            else:
                conversion = 0
            
            insights.append(Insight(
                type="breakdown",
                title=f"{sector}",
                value=f"₹{data['value']/1_000_000:.2f}M",
                context=f"{data['count']} deals, {conversion:.0f}% conversion",
                risk_level="high" if conversion < 20 and closed_value > 0 else None
            ))
        
        # Identify underperforming
        underperforming = []
        for sector, data in sector_data.items():
            closed = data["won"] + data["lost"]
            if closed > 0 and data["won"] / closed < 0.3:
                underperforming.append(sector)
        
        summary = (
            f"{len(sorted_sectors)} sectors analyzed. "
            f"Top performer is {sorted_sectors[0] if sorted_sectors else 'N/A'} "
            f"with ₹{sector_data[sorted_sectors[0]]['value']/1_000_000:.2f}M."
        ) if sorted_sectors else "No sector data available."
        
        recommendations = []
        if underperforming:
            recommendations.append(f"Investigate low conversion in: {', '.join(underperforming)}")
        
        return BIResult(
            metric="sector_performance",
            summary=summary,
            insights=insights,
            data_quality_notes=[],
            recommendations=recommendations
        )
    
    def _analyze_stalled_deals(self, records: List[Any]) -> BIResult:
        """Identify deals that appear stuck"""
        
        today = datetime.now()
        stalled = []
        
        for record in records:
            stage = record.fields.get("stage", "")
            close_date = record.fields.get("close_date")
            value = record.fields.get("value", 0) or 0
            
            # Define stall criteria
            is_stalled = False
            stall_reason = ""
            
            if stage == "Qualified":
                # Qualified deals older than expected
                if close_date and (today - close_date).days > 30:
                    is_stalled = True
                    stall_reason = f"Qualified for {(today - close_date).days} days"
            elif stage in ["Proposal", "Negotiation"]:
                if close_date and (today - close_date).days > 60:
                    is_stalled = True
                    stall_reason = f"In {stage} for {(today - close_date).days} days"
            elif stage == "Won" or stage == "Lost":
                # Skip closed deals
                continue
            elif stage == "Lead":
                if close_date and (today - close_date).days > 90:
                    is_stalled = True
                    stall_reason = f"Lead for {(today - close_date).days} days"
            
            if is_stalled:
                stalled.append({
                    "name": record.name,
                    "stage": stage,
                    "value": value,
                    "reason": stall_reason,
                    "sector": record.fields.get("sector", "Unknown")
                })
        
        # Sort by value
        stalled.sort(key=lambda x: x["value"], reverse=True)
        
        total_stalled_value = sum(s["value"] for s in stalled)
        
        insights = []
        insights.append(Insight(
            type="metric",
            title="Stalled Deals",
            value=len(stalled),
            context=f"Total value at risk: ₹{total_stalled_value/1_000_000:.2f}M",
            risk_level="high" if len(stalled) > 5 else "medium" if len(stalled) > 0 else None
        ))
        
        # Top stalled deals
        for deal in stalled[:5]:
            insights.append(Insight(
                type="breakdown",
                title=deal["name"][:40],
                value=f"₹{deal['value']/1_000_000:.2f}M" if deal["value"] >= 1_000_000 else f"₹{deal['value']:,.0f}",
                context=f"{deal['sector']} - {deal['reason']}",
                risk_level="high" if deal["value"] > 500_000 else "medium"
            ))
        
        summary = (
            f"{len(stalled)} stalled deals identified with ₹{total_stalled_value/1_000_000:.2f}M at risk. "
            f"{len([s for s in stalled if s['value'] > 500_000])} high-value deals need immediate attention."
        ) if stalled else "No stalled deals identified."
        
        return BIResult(
            metric="stalled_deals",
            summary=summary,
            insights=insights,
            data_quality_notes=[],
            recommendations=["Schedule follow-up for top stalled deals"] if stalled else []
        )
    
    def _analyze_revenue_at_risk(self, records: List[Any]) -> BIResult:
        """Calculate revenue at risk based on stalled deals and lost deals"""
        
        today = datetime.now()
        
        at_risk = []
        lost_value = 0
        
        for record in records:
            stage = record.fields.get("stage", "")
            value = record.fields.get("value", 0) or 0
            close_date = record.fields.get("close_date")
            
            if stage == "Lost":
                lost_value += value
            elif stage in ["Qualified", "Proposal", "Negotiation"]:
                # At risk if overdue
                if close_date and today > close_date:
                    days_overdue = (today - close_date).days
                    at_risk.append({
                        "name": record.name,
                        "value": value,
                        "days_overdue": days_overdue,
                        "stage": stage,
                        "sector": record.fields.get("sector", "Unknown")
                    })
        
        total_at_risk = sum(a["value"] for a in at_risk)
        
        insights = []
        insights.append(Insight(
            type="metric",
            title="Revenue at Risk",
            value=f"₹{total_at_risk/1_000_000:.2f}M",
            context=f"{len(at_risk)} overdue active deals",
            risk_level="high" if total_at_risk > 1_000_000 else "medium"
        ))
        
        insights.append(Insight(
            type="metric",
            title="Lost Revenue (Period)",
            value=f"₹{lost_value/1_000_000:.2f}M",
            context="Closed lost deals",
            risk_level=None
        ))
        
        # Top at-risk deals
        for deal in sorted(at_risk, key=lambda x: x["value"], reverse=True)[:5]:
            insights.append(Insight(
                type="breakdown",
                title=deal["name"][:40],
                value=f"₹{deal['value']/1_000_000:.2f}M" if deal["value"] >= 1_000_000 else f"₹{deal['value']:,.0f}",
                context=f"{deal['days_overdue']} days overdue - {deal['stage']}",
                risk_level="high" if deal["days_overdue"] > 30 else "medium"
            ))
        
        summary = (
            f"₹{total_at_risk/1_000_000:.2f}M in overdue deals at immediate risk. "
            f"Plus ₹{lost_value/1_000_000:.2f}M already lost in period."
        )
        
        return BIResult(
            metric="revenue_at_risk",
            summary=summary,
            insights=insights,
            data_quality_notes=[],
            recommendations=["Urgent: Contact overdue deals immediately"] if at_risk else []
        )
    
    def _analyze_conversion_rate(
        self,
        records: List[Any],
        group_by: Optional[str]
    ) -> BIResult:
        """Analyze conversion rates overall or by group"""
        
        if group_by:
            groups = defaultdict(lambda: {"won": 0, "lost": 0, "total_value": 0})
            
            for record in records:
                group_val = record.fields.get(group_by, "Unknown")
                stage = record.fields.get("stage", "")
                value = record.fields.get("value", 0) or 0
                
                groups[group_val]["total_value"] += value
                if stage == "Won":
                    groups[group_val]["won"] += value
                elif stage == "Lost":
                    groups[group_val]["lost"] += value
            
            insights = []
            for group, data in groups.items():
                closed = data["won"] + data["lost"]
                if closed > 0:
                    rate = data["won"] / closed * 100
                    insights.append(Insight(
                        type="breakdown",
                        title=f"{group}",
                        value=f"{rate:.0f}%",
                        context=f"₹{data['won']/1_000:.0f}K won of ₹{closed/1_000:.0f}K closed",
                        risk_level="high" if rate < 25 else "medium" if rate < 40 else None
                    ))
            
            summary = f"Conversion rates by {group_by} calculated from {len(records)} deals."
        else:
            won = sum(r.fields.get("value", 0) or 0 for r in records if r.fields.get("stage") == "Won")
            lost = sum(r.fields.get("value", 0) or 0 for r in records if r.fields.get("stage") == "Lost")
            closed = won + lost
            rate = won / closed * 100 if closed > 0 else 0
            
            insights = [Insight(
                type="metric",
                title="Overall Conversion Rate",
                value=f"{rate:.0f}%",
                context=f"₹{won/1_000_000:.2f}M won of ₹{closed/1_000_000:.2f}M closed",
                risk_level="high" if rate < 25 else "medium" if rate < 40 else None
            )]
            
            summary = f"Overall conversion rate: {rate:.0f}% based on ₹{closed/1_000_000:.2f}M in closed deals."
        
        return BIResult(
            metric="conversion_rate",
            summary=summary,
            insights=insights,
            data_quality_notes=[],
            recommendations=[]
        )
    
    def _analyze_work_order_status(
        self,
        records: List[Any],
        group_by: Optional[str]
    ) -> BIResult:
        """Analyze work order completion status"""
        
        if group_by == "sector":
            sectors = defaultdict(lambda: {"total": 0, "completed": 0, "in_progress": 0, "pending": 0})
            
            for record in records:
                sector = record.fields.get("sector", "Unknown")
                status = record.fields.get("status", "Unknown")
                
                sectors[sector]["total"] += 1
                if "Complete" in status or "Done" in status or "Closed" in status:
                    sectors[sector]["completed"] += 1
                elif "Progress" in status or "Working" in status:
                    sectors[sector]["in_progress"] += 1
                else:
                    sectors[sector]["pending"] += 1
            
            insights = []
            for sector, data in sectors.items():
                completion_rate = data["completed"] / data["total"] * 100 if data["total"] > 0 else 0
                insights.append(Insight(
                    type="breakdown",
                    title=f"{sector}",
                    value=f"{completion_rate:.0f}%",
                    context=f"{data['completed']}/{data['total']} completed, {data['in_progress']} in progress",
                    risk_level="high" if completion_rate < 30 else "medium" if completion_rate < 60 else None
                ))
            
            summary = f"Work order completion analyzed across {len(sectors)} sectors."
        else:
            total = len(records)
            completed = sum(1 for r in records if "Complete" in r.fields.get("status", ""))
            rate = completed / total * 100 if total > 0 else 0
            
            insights = [Insight(
                type="metric",
                title="Completion Rate",
                value=f"{rate:.0f}%",
                context=f"{completed} of {total} work orders completed",
                risk_level="high" if rate < 50 else None
            )]
            
            summary = f"{completed} of {total} work orders completed ({rate:.0f}%)."
        
        return BIResult(
            metric="work_order_status",
            summary=summary,
            insights=insights,
            data_quality_notes=[],
            recommendations=["Review pending work orders"] if completed < len(records) else []
        )
    
    def _analyze_completion_rate(self, records: List[Any]) -> BIResult:
        """Analyze completion rate with timing"""
        return self._analyze_work_order_status(records, None)
    
    def _generic_analysis(self, records: List[Any], metric: str) -> BIResult:
        """Generic fallback analysis"""
        return BIResult(
            metric=metric,
            summary=f"Analyzed {len(records)} records for {metric}.",
            insights=[Insight(
                type="metric",
                title="Records Processed",
                value=len(records),
                context="Total records matching criteria",
                risk_level=None
            )],
            data_quality_notes=[],
            recommendations=[]
        )
    
    def analyze_cross_board(self, deals_records: List[Any], work_orders_records: List[Any]) -> BIResult:
        """
        Analyze correlation between Deals (pipeline) and Work Orders (execution)
        Example insight: "Energy sector has high pipeline value but lowest completion rate"
        """
        
        from collections import defaultdict
        
        # Aggregate deals by sector
        sector_pipeline = defaultdict(lambda: {"value": 0.0, "count": 0, "won": 0, "lost": 0})
        for record in deals_records:
            sector = record.fields.get("sector", "Unknown")
            value = record.fields.get("value", 0) or 0
            stage = record.fields.get("stage", "")
            
            sector_pipeline[sector]["value"] += value
            sector_pipeline[sector]["count"] += 1
            if stage == "Won":
                sector_pipeline[sector]["won"] += value
            elif stage == "Lost":
                sector_pipeline[sector]["lost"] += value
        
        # Aggregate work orders by sector
        sector_execution = defaultdict(lambda: {"total": 0, "completed": 0, "revenue": 0.0})
        for record in work_orders_records:
            sector = record.fields.get("sector", "Unknown")
            status = record.fields.get("status", "")
            revenue = record.fields.get("revenue", 0) or 0
            
            sector_execution[sector]["total"] += 1
            sector_execution[sector]["revenue"] += revenue
            if "Complete" in status or "Done" in status or "Closed" in status:
                sector_execution[sector]["completed"] += 1
        
        # Find insights
        insights = []
        
        # Calculate completion rates and identify mismatches
        sector_analysis = []
        for sector in set(list(sector_pipeline.keys()) + list(sector_execution.keys())):
            pipe = sector_pipeline.get(sector, {"value": 0, "count": 0})
            exec_ = sector_execution.get(sector, {"total": 0, "completed": 0})
            
            completion_rate = (exec_["completed"] / exec_["total"] * 100) if exec_["total"] > 0 else 0
            
            closed_value = pipe.get("won", 0) + pipe.get("lost", 0)
            conversion_rate = (pipe.get("won", 0) / closed_value * 100) if closed_value > 0 else 0
            
            sector_analysis.append({
                "sector": sector,
                "pipeline_value": pipe.get("value", 0),
                "deal_count": pipe.get("count", 0),
                "work_orders": exec_.get("total", 0),
                "completion_rate": completion_rate,
                "conversion_rate": conversion_rate
            })
        
        # Find the insight: high pipeline + low completion = bottleneck
        high_pipeline_sectors = [s for s in sector_analysis if s["pipeline_value"] > 1000000]
        if high_pipeline_sectors:
            # Sort by completion rate (ascending) to find the bottleneck
            bottleneck = min(high_pipeline_sectors, key=lambda x: x["completion_rate"])
            
            insights.append(Insight(
                type="cross_board",
                title=f"Operational Bottleneck: {bottleneck['sector']} Sector",
                value=f"{bottleneck['completion_rate']:.0f}% completion",
                context=f"High pipeline (₹{bottleneck['pipeline_value']/1_000_000:.2f}M) but poor execution ({bottleneck['work_orders']} work orders, only {bottleneck['completion_rate']:.0f}% completed)",
                risk_level="high" if bottleneck["completion_rate"] < 50 else "medium"
            ))
        
        # Find best performing sector
        if sector_analysis:
            best = max(sector_analysis, key=lambda x: x["completion_rate"] if x["work_orders"] > 0 else -1)
            insights.append(Insight(
                type="cross_board",
                title=f"Best Execution: {best['sector']} Sector",
                value=f"{best['completion_rate']:.0f}% completion",
                context=f"Pipeline: ₹{best['pipeline_value']/1_000_000:.2f}M, {best['work_orders']} work orders",
                risk_level=None
            ))
        
        # Summary
        total_pipeline = sum(s["pipeline_value"] for s in sector_analysis)
        total_work_orders = sum(s["work_orders"] for s in sector_analysis)
        avg_completion = sum(s["completion_rate"] for s in sector_analysis) / len(sector_analysis) if sector_analysis else 0
        
        summary = (
            f"Cross-board analysis of {len(sector_analysis)} sectors: "
            f"Total pipeline ₹{total_pipeline/1_000_000:.2f}M, "
            f"{total_work_orders} work orders with {avg_completion:.0f}% avg completion rate. "
            f"{bottleneck['sector'] if high_pipeline_sectors else 'N/A'} shows operational bottleneck."
        )
        
        return BIResult(
            metric="cross_board_insight",
            summary=summary,
            insights=insights,
            data_quality_notes=[],
            recommendations=[
                f"Investigate {bottleneck['sector']} sector execution delays" if high_pipeline_sectors else "Review sector execution processes"
            ]
        )
    
    def get_computation_log(self) -> List[str]:
        """Get log of BI computations performed"""
        return self.computation_log
