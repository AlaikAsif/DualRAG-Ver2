"""
Report Generation Schemas.

Defines Pydantic models for report generation including sections, templates,
styling, and complete report structures.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ReportFormat(str, Enum):
    """Output format for reports."""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    MARKDOWN = "markdown"
    EXCEL = "excel"


class ChartType(str, Enum):
    """Types of charts for report visualization."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    TABLE = "table"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class ReportSection(BaseModel):
    """Single section in a report."""
    
    title: str = Field(..., min_length=1, description="Section title")
    content: str = Field(..., min_length=1, description="Section text content")
    section_order: int = Field(default=0, ge=0, description="Order of section in report")
    subsections: List["ReportSection"] = Field(default_factory=list, description="Nested subsections")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Executive Summary",
                "content": "This report summarizes...",
                "section_order": 1,
                "subsections": []
            }
        }


class ChartData(BaseModel):
    """Data for a chart in report."""
    
    chart_type: ChartType = Field(..., description="Type of chart")
    title: str = Field(..., description="Chart title")
    labels: List[str] = Field(..., description="X-axis or category labels")
    datasets: List[Dict[str, Any]] = Field(..., description="Data series")
    description: Optional[str] = Field(None, description="Chart description for accessibility")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chart_type": "bar",
                "title": "Quarterly Revenue",
                "labels": ["Q1", "Q2", "Q3", "Q4"],
                "datasets": [
                    {"label": "2024", "data": [100, 150, 200, 250]},
                    {"label": "2023", "data": [80, 120, 160, 200]}
                ],
                "description": "Revenue comparison across quarters"
            }
        }


class ReportVisualization(BaseModel):
    """Visualization element in report."""
    
    visualization_type: str = Field(..., description="Type (chart, table, image)")
    title: Optional[str] = Field(None, description="Visualization title")
    data: ChartData = Field(..., description="Data for visualization")
    position: str = Field(default="inline", description="Position (inline, sidebar, full-width)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "visualization_type": "chart",
                "title": "Revenue Trend",
                "data": {
                    "chart_type": "line",
                    "title": "Revenue Over Time",
                    "labels": ["Jan", "Feb", "Mar"],
                    "datasets": [{"label": "Revenue", "data": [100, 150, 200]}]
                },
                "position": "inline"
            }
        }


class ReportTemplate(BaseModel):
    """Template configuration for report styling."""
    
    template_name: str = Field(..., description="Name of template (default, professional, creative)")
    title_style: Dict[str, str] = Field(default_factory=dict, description="CSS styles for titles")
    body_style: Dict[str, str] = Field(default_factory=dict, description="CSS styles for body text")
    color_scheme: Dict[str, str] = Field(default_factory=dict, description="Color palette")
    fonts: Dict[str, str] = Field(default_factory=dict, description="Font selections")
    include_header: bool = Field(default=True, description="Include report header")
    include_footer: bool = Field(default=True, description="Include report footer")
    include_toc: bool = Field(default=True, description="Include table of contents")
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "professional",
                "title_style": {"font-size": "24px", "font-weight": "bold"},
                "body_style": {"font-size": "12px", "font-family": "Arial"},
                "color_scheme": {"primary": "#1e3a8a", "secondary": "#60a5fa"},
                "fonts": {"heading": "Arial", "body": "Arial"},
                "include_header": True,
                "include_footer": True,
                "include_toc": True
            }
        }


class ReportMetadata(BaseModel):
    """Metadata about a report."""
    
    title: str = Field(..., description="Report title")
    author: Optional[str] = Field(None, description="Report author name")
    description: Optional[str] = Field(None, description="Report description/abstract")
    created_at: datetime = Field(default_factory=datetime.now, description="When report was created")
    generated_at: datetime = Field(default_factory=datetime.now, description="When report was generated")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    keywords: List[str] = Field(default_factory=list, description="Keywords for search")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Q3 Sales Report",
                "author": "John Doe",
                "description": "Comprehensive sales analysis for Q3 2024",
                "created_at": "2025-12-04T15:50:00Z",
                "tags": ["sales", "quarterly"],
                "keywords": ["revenue", "pipeline", "forecast"]
            }
        }


class Report(BaseModel):
    """Complete report structure."""
    
    metadata: ReportMetadata = Field(..., description="Report metadata")
    template: ReportTemplate = Field(..., description="Report template/styling")
    sections: List[ReportSection] = Field(..., description="Report sections in order")
    visualizations: List[ReportVisualization] = Field(default_factory=list, description="Charts and visualizations")
    format: ReportFormat = Field(default=ReportFormat.HTML, description="Output format")
    file_path: Optional[str] = Field(None, description="Where report was saved")
    content_hash: Optional[str] = Field(None, description="Hash of report content for versioning")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "title": "Q3 Report",
                    "author": "Analytics Team",
                    "description": "Q3 analysis"
                },
                "template": {
                    "template_name": "professional",
                    "include_toc": True
                },
                "sections": [
                    {
                        "title": "Summary",
                        "content": "Key findings...",
                        "section_order": 1
                    }
                ],
                "visualizations": [],
                "format": "html"
            }
        }


class ReportGenerationRequest(BaseModel):
    """Request to generate a report."""
    
    user_query: str = Field(..., description="User's report request")
    data_sources: List[str] = Field(default_factory=list, description="Data sources to include (static_rag, sql_rag, etc.)")
    template_name: str = Field(default="default", description="Report template to use")
    output_format: ReportFormat = Field(default=ReportFormat.HTML, description="Desired output format")
    customization: Dict[str, Any] = Field(default_factory=dict, description="Custom report options")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_query": "Generate a sales report for Q3",
                "data_sources": ["sql_rag"],
                "template_name": "professional",
                "output_format": "pdf",
                "customization": {"include_charts": True, "color_scheme": "blue"}
            }
        }


class ReportGenerationResponse(BaseModel):
    """Response from report generation."""
    
    report: Report = Field(..., description="Generated report")
    generation_time_ms: float = Field(default=0.0, ge=0.0, description="Time to generate report")
    data_sources_used: List[str] = Field(default_factory=list, description="Data sources actually used")
    success: bool = Field(default=True, description="Whether generation was successful")
    warnings: List[str] = Field(default_factory=list, description="Warnings during generation")
    errors: List[str] = Field(default_factory=list, description="Errors during generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report": {
                    "metadata": {"title": "Q3 Report"},
                    "template": {"template_name": "professional"},
                    "sections": [],
                    "format": "pdf"
                },
                "generation_time_ms": 1234.5,
                "data_sources_used": ["sql_rag"],
                "success": True,
                "warnings": ["Some data was truncated"]
            }
        }
