"""Report generation orchestrator."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from src.monitoring.logger import get_logger
from src.schemas.report import ReportType, ReportFormat

logger = get_logger(__name__)


@dataclass
class ReportData:
    """Container for report data and metadata."""
    title: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    sections: List[str]
    report_type: ReportType
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "sections": self.sections,
            "report_type": self.report_type.value,
            "created_at": self.created_at.isoformat(),
        }


class ReportGenerator:
    """Generate reports from query results."""
    
    def __init__(self):
        """Initialize report generator."""
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load available report templates."""
        try:
            from src.report.templates.default import DEFAULT_TEMPLATE
            self.templates["default"] = DEFAULT_TEMPLATE
            logger.debug("Loaded default report template")
        except ImportError:
            logger.warning("Could not load default template")
    
    async def generate(
        self,
        title: str,
        data: Dict[str, Any],
        report_type: ReportType = ReportType.SUMMARY,
        customization: Optional[Dict[str, Any]] = None,
        template_name: str = "default"
    ) -> ReportData:
        """
        Generate a report from data.
        
        Args:
            title: Report title
            data: Report data/content
            report_type: Type of report (summary, detailed, comparison)
            customization: Custom requirements/styling
            template_name: Template to use
            
        Returns:
            Generated ReportData
        """
        logger.info(f"Generating {report_type.value} report: {title}")
        
        try:
            # Get template
            template = self.templates.get(template_name, self.templates.get("default", {}))
            
            # Aggregate data
            aggregated = await self._aggregate_data(data, report_type)
            
            # Select sections based on report type
            sections = self._select_sections(report_type)
            
            # Generate content for each section
            content = {}
            for section in sections:
                section_content = await self._generate_section(
                    section,
                    aggregated,
                    report_type,
                    customization or {}
                )
                content[section] = section_content
            
            # Build metadata
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "template": template_name,
                "sections_count": len(sections),
            }
            
            if customization:
                metadata["customizations"] = list(customization.keys())
            
            report = ReportData(
                title=title,
                content=content,
                metadata=metadata,
                sections=sections,
                report_type=report_type,
                created_at=datetime.now()
            )
            
            logger.info(f"Report generated successfully with {len(sections)} sections")
            return report
        
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            raise
    
    async def _aggregate_data(
        self,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Dict[str, Any]:
        """
        Aggregate data based on report type.
        
        Args:
            data: Raw report data
            report_type: Type of report
            
        Returns:
            Aggregated data
        """
        aggregated = {
            "raw": data,
            "summary": {},
            "details": {},
            "insights": [],
        }
        
        # Generate summary
        if "records" in data:
            aggregated["summary"]["total_records"] = len(data["records"])
            aggregated["summary"]["data_sources"] = data.get("sources", [])
        
        # Extract insights for different report types
        if report_type == ReportType.SUMMARY:
            aggregated["insights"] = self._extract_summary_insights(data)
        elif report_type == ReportType.DETAILED:
            aggregated["insights"] = self._extract_detailed_insights(data)
        elif report_type == ReportType.COMPARISON:
            aggregated["insights"] = self._extract_comparison_insights(data)
        
        return aggregated
    
    def _select_sections(self, report_type: ReportType) -> List[str]:
        """
        Select sections based on report type.
        
        Args:
            report_type: Type of report
            
        Returns:
            List of section names
        """
        base_sections = ["executive_summary", "methodology"]
        
        if report_type == ReportType.SUMMARY:
            return base_sections + ["key_findings", "conclusion"]
        elif report_type == ReportType.DETAILED:
            return base_sections + ["data_overview", "detailed_analysis", "insights", "recommendations"]
        elif report_type == ReportType.COMPARISON:
            return base_sections + ["comparison_framework", "comparative_analysis", "advantages", "conclusion"]
        else:
            return base_sections
    
    async def _generate_section(
        self,
        section: str,
        data: Dict[str, Any],
        report_type: ReportType,
        customization: Dict[str, Any]
    ) -> str:
        """
        Generate content for a section.
        
        Args:
            section: Section name
            data: Aggregated data
            report_type: Report type
            customization: Custom requirements
            
        Returns:
            Section content
        """
        logger.debug(f"Generating section: {section}")
        
        # Use LLM to generate section content
        try:
            from src.chains.llm import get_llm
            
            llm = get_llm()
            
            prompt = f"""Generate the {section} section for a {report_type.value} report.
            
Data:
{data.get('raw', {})}

Keep it concise but informative. Use clear formatting."""
            
            if customization:
                prompt += f"\n\nCustomization requirements: {customization}"
            
            response = await llm.ainvoke({"messages": [{"role": "user", "content": prompt}]})
            return response.content
        
        except Exception as e:
            logger.warning(f"Failed to generate section {section}: {str(e)}")
            return f"[Error generating {section}]"
    
    def _extract_summary_insights(self, data: Dict[str, Any]) -> List[str]:
        """Extract key insights for summary report."""
        insights = []
        if "records" in data and data["records"]:
            insights.append(f"Total records analyzed: {len(data['records'])}")
        if "sources" in data:
            insights.append(f"Data sources: {', '.join(data['sources'])}")
        return insights
    
    def _extract_detailed_insights(self, data: Dict[str, Any]) -> List[str]:
        """Extract detailed insights."""
        insights = self._extract_summary_insights(data)
        if "statistics" in data:
            insights.append("Statistical analysis available")
        return insights
    
    def _extract_comparison_insights(self, data: Dict[str, Any]) -> List[str]:
        """Extract comparison insights."""
        insights = []
        if "comparison_items" in data:
            insights.append(f"Comparing {len(data['comparison_items'])} items")
        if "metrics" in data:
            insights.append(f"Metrics compared: {', '.join(data['metrics'])}")
        return insights


# Global generator instance
_generator: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """Get or create global report generator."""
    global _generator
    if _generator is None:
        _generator = ReportGenerator()
    return _generator
