"""Render final HTML reports."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Template

from src.monitoring.logger import get_logger
from src.report.generator import ReportData
from src.schemas.report import ReportFormat

logger = get_logger(__name__)


class ReportRenderer:
    """Render reports to HTML/PDF."""
    
    def __init__(self):
        """Initialize renderer."""
        self.base_css = self._get_base_css()
    
    def _get_base_css(self) -> str:
        """Get base CSS styling."""
        return """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #fff;
            }
            
            .container {
                max-width: 900px;
                margin: 0 auto;
                padding: 40px;
            }
            
            h1 {
                color: #1e40af;
                margin-bottom: 10px;
                font-size: 28px;
            }
            
            h2 {
                color: #1e40af;
                margin-top: 30px;
                margin-bottom: 15px;
                font-size: 20px;
                border-bottom: 2px solid #1e40af;
                padding-bottom: 8px;
            }
            
            h3 {
                color: #3b82f6;
                margin-top: 20px;
                margin-bottom: 10px;
                font-size: 16px;
            }
            
            p {
                margin-bottom: 15px;
            }
            
            .metadata {
                background-color: #f0f9ff;
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 30px;
                font-size: 12px;
                color: #666;
            }
            
            .section {
                margin-bottom: 30px;
            }
            
            .insight {
                background-color: #ecfdf5;
                border-left: 4px solid #10b981;
                padding: 12px;
                margin: 10px 0;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }
            
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            
            th {
                background-color: #f0f9ff;
                font-weight: bold;
                color: #1e40af;
            }
            
            tr:nth-child(even) {
                background-color: #f9fafb;
            }
            
            .footer {
                border-top: 1px solid #ddd;
                padding-top: 20px;
                margin-top: 40px;
                font-size: 12px;
                color: #999;
            }
        </style>
        """
    
    def render_html(
        self,
        report: ReportData,
        styling: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Render report as HTML.
        
        Args:
            report: ReportData instance
            styling: Optional custom CSS
            
        Returns:
            HTML string
        """
        logger.info(f"Rendering HTML report: {report.title}")
        
        try:
            # Build HTML
            html = "<!DOCTYPE html>\n<html>\n<head>\n"
            html += "<meta charset='utf-8'>\n"
            html += f"<title>{report.title}</title>\n"
            html += self.base_css
            
            if styling:
                html += "<style>\n" + "\n".join(f"{k} {{ {v} }}" for k, v in styling.items()) + "\n</style>\n"
            
            html += "</head>\n<body>\n"
            html += "<div class='container'>\n"
            
            # Title and metadata
            html += f"<h1>{report.title}</h1>\n"
            html += "<div class='metadata'>\n"
            html += f"<p><strong>Report Type:</strong> {report.report_type.value}</p>\n"
            html += f"<p><strong>Generated:</strong> {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>\n"
            if report.metadata:
                html += f"<p><strong>Sections:</strong> {report.metadata.get('sections_count', len(report.sections))}</p>\n"
            html += "</div>\n"
            
            # Sections
            for section in report.sections:
                content = report.content.get(section, "")
                section_title = section.replace("_", " ").title()
                html += f"<div class='section'>\n"
                html += f"<h2>{section_title}</h2>\n"
                html += f"<div>{content}</div>\n"
                html += "</div>\n"
            
            # Footer
            html += "<div class='footer'>\n"
            html += "<p>Generated by DualRAG Report Engine</p>\n"
            html += "</div>\n"
            
            html += "</div>\n</body>\n</html>"
            
            logger.info("HTML report rendered successfully")
            return html
        
        except Exception as e:
            logger.error(f"HTML rendering failed: {str(e)}")
            raise
    
    def render_pdf(
        self,
        report: ReportData,
        output_path: str,
        styling: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Render report as PDF.
        
        Args:
            report: ReportData instance
            output_path: Output file path
            styling: Optional custom CSS
            
        Returns:
            True if successful
        """
        logger.info(f"Rendering PDF report: {report.title}")
        
        try:
            # Generate HTML first
            html = self.render_html(report, styling)
            
            # Try to use weasyprint if available
            try:
                from weasyprint import HTML, CSS
                HTML(string=html).write_pdf(output_path)
                logger.info(f"PDF saved to {output_path}")
                return True
            except ImportError:
                logger.warning("weasyprint not installed, attempting fallback")
                # Fallback: save as HTML instead
                output_html = output_path.replace('.pdf', '.html')
                with open(output_html, 'w') as f:
                    f.write(html)
                logger.info(f"Fallback: saved as HTML to {output_html}")
                return False
        
        except Exception as e:
            logger.error(f"PDF rendering failed: {str(e)}")
            raise
    
    def render_markdown(self, report: ReportData) -> str:
        """
        Render report as Markdown.
        
        Args:
            report: ReportData instance
            
        Returns:
            Markdown string
        """
        logger.info(f"Rendering Markdown report: {report.title}")
        
        markdown = f"# {report.title}\n\n"
        
        # Metadata
        markdown += "## Metadata\n\n"
        markdown += f"- **Type:** {report.report_type.value}\n"
        markdown += f"- **Generated:** {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Sections
        for section in report.sections:
            content = report.content.get(section, "")
            section_title = section.replace("_", " ").title()
            markdown += f"## {section_title}\n\n"
            markdown += f"{content}\n\n"
        
        # Footer
        markdown += "---\n\n"
        markdown += "*Generated by DualRAG Report Engine*\n"
        
        return markdown
    
    def apply_customization(
        self,
        html: str,
        customization: Dict[str, Any]
    ) -> str:
        """
        Apply customizations to rendered HTML.
        
        Args:
            html: HTML string
            customization: Customization requirements
            
        Returns:
            Modified HTML
        """
        logger.debug(f"Applying customizations: {list(customization.keys())}")
        
        try:
            # Apply color scheme
            if "color_scheme" in customization:
                colors = customization["color_scheme"]
                html = html.replace("#1e40af", colors.get("primary", "#1e40af"))
                html = html.replace("#3b82f6", colors.get("secondary", "#3b82f6"))
            
            # Apply logo
            if "logo_url" in customization:
                logo_html = f'<img src="{customization["logo_url"]}" style="max-width: 100px; margin-bottom: 20px;">'
                html = html.replace("<h1>", f"{logo_html}<h1>", 1)
            
            # Add company info
            if "company_name" in customization:
                company_html = f'<p style="text-align: center; color: #999; font-size: 12px;">{customization["company_name"]}</p>'
                html = html.replace("</body>", f"{company_html}</body>")
            
            logger.info("Customizations applied successfully")
            return html
        
        except Exception as e:
            logger.warning(f"Error applying customizations: {str(e)}")
            return html


# Global renderer instance
_renderer: Optional[ReportRenderer] = None


def get_report_renderer() -> ReportRenderer:
    """Get or create global report renderer."""
    global _renderer
    if _renderer is None:
        _renderer = ReportRenderer()
    return _renderer
