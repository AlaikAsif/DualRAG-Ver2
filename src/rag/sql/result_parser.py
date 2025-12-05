"""
SQL Result Parsing and Formatting.

Parses and formats SQL query results for LLM consumption and user presentation.
Handles data type conversions and error formatting.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
import json

from src.schemas.sql import SQLResult
from src.monitoring.logger import get_logger


logger = get_logger(__name__)


class ResultParser:
    """
    Parse and format SQL query results.
    
    Features:
    - Result summary generation
    - Data type conversion
    - Error message formatting
    - Result limiting and truncation
    - JSON serialization support
    """
    
    def __init__(self, max_display_rows: int = 100, max_text_length: int = 5000):
        """
        Initialize result parser.
        
        Args:
            max_display_rows: Max rows to display in results
            max_text_length: Max text length for result summary
        """
        self.max_display_rows = max_display_rows
        self.max_text_length = max_text_length
    
    def parse(self, result: SQLResult) -> Dict[str, Any]:
        """
        Parse SQL result into formatted output.
        
        Args:
            result: SQLResult from query execution
        
        Returns:
            Dict with formatted result data
        """
        if result.status == 'error':
            return self._format_error(result)
        
        return self._format_success(result)
    
    def _format_success(self, result: SQLResult) -> Dict[str, Any]:
        """Format successful query result."""
        logger.info(f"Formatting {result.row_count} rows")
        
        # Truncate rows if necessary
        display_rows = result.rows[:self.max_display_rows]
        truncated = result.row_count > self.max_display_rows
        
        # Generate summary
        summary = self._generate_summary(result, truncated)
        
        # Format rows for LLM
        formatted_rows = self._format_rows(display_rows, result.column_names)
        
        # Convert to serializable format
        serializable_rows = [
            self._make_serializable(row) for row in display_rows
        ]
        
        return {
            "status": "success",
            "row_count": result.row_count,
            "display_count": len(display_rows),
            "truncated": truncated,
            "columns": result.column_names,
            "rows": serializable_rows,
            "summary": summary,
            "formatted_text": formatted_rows,
            "execution_time_ms": result.execution_time_ms
        }
    
    def _format_error(self, result: SQLResult) -> Dict[str, Any]:
        """Format error result."""
        logger.warning(f"Formatting error result: {result.error_message}")
        
        return {
            "status": "error",
            "error_message": result.error_message,
            "error_type": self._categorize_error(result.error_message),
            "execution_time_ms": result.execution_time_ms
        }
    
    def _format_rows(self, rows: List[Dict[str, Any]], columns: List[str]) -> str:
        """
        Format rows as readable text for LLM.
        
        Args:
            rows: List of result rows
            columns: Column names
        
        Returns:
            Formatted text representation
        """
        if not rows:
            return "No results returned."
        
        text_lines = []
        
        # Header
        header = " | ".join(columns)
        text_lines.append(header)
        text_lines.append("-" * min(len(header), 100))
        
        # Rows
        for row in rows:
            values = []
            for col in columns:
                value = row.get(col)
                value_str = self._format_value(value)
                values.append(value_str)
            text_lines.append(" | ".join(values))
        
        text = "\n".join(text_lines)
        
        # Truncate if too long
        if len(text) > self.max_text_length:
            text = text[:self.max_text_length] + "\n... (truncated)"
        
        return text
    
    def _generate_summary(self, result: SQLResult, truncated: bool) -> str:
        """
        Generate natural language summary of results.
        
        Args:
            result: SQLResult
            truncated: Whether results were truncated
        
        Returns:
            Summary string
        """
        summary = f"Query returned {result.row_count} row"
        if result.row_count != 1:
            summary += "s"
        
        summary += f" in {result.execution_time_ms:.0f}ms"
        
        if truncated:
            summary += f" (displaying first {self.max_display_rows})"
        
        if result.row_count == 0:
            summary = "No rows returned."
        
        return summary
    
    def _format_value(self, value: Any) -> str:
        """
        Format a single value for display.
        
        Args:
            value: Value to format
        
        Returns:
            Formatted string
        """
        if value is None:
            return "NULL"
        
        if isinstance(value, bool):
            return "true" if value else "false"
        
        if isinstance(value, (int, float)):
            return str(value)
        
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        
        if isinstance(value, Decimal):
            return str(value)
        
        if isinstance(value, (list, dict)):
            return json.dumps(value, default=str)
        
        # String
        value_str = str(value)
        if len(value_str) > 50:
            value_str = value_str[:47] + "..."
        
        return value_str
    
    def _make_serializable(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert row to JSON-serializable format.
        
        Args:
            row: Row dict
        
        Returns:
            Serializable row dict
        """
        serializable = {}
        
        for key, value in row.items():
            if value is None:
                serializable[key] = None
            elif isinstance(value, (int, float, str, bool)):
                serializable[key] = value
            elif isinstance(value, (datetime, date)):
                serializable[key] = value.isoformat()
            elif isinstance(value, Decimal):
                serializable[key] = float(value)
            elif isinstance(value, (list, dict)):
                serializable[key] = json.dumps(value, default=str)
            else:
                serializable[key] = str(value)
        
        return serializable
    
    def _categorize_error(self, error_msg: str) -> str:
        """
        Categorize error type.
        
        Args:
            error_msg: Error message
        
        Returns:
            Error category string
        """
        error_upper = error_msg.upper()
        
        if "SYNTAX" in error_upper:
            return "syntax_error"
        elif "NOT FOUND" in error_upper or "DOES NOT EXIST" in error_upper:
            return "schema_error"
        elif "TIMEOUT" in error_upper:
            return "timeout_error"
        elif "CONNECTION" in error_upper:
            return "connection_error"
        elif "PERMISSION" in error_upper or "DENIED" in error_upper:
            return "permission_error"
        else:
            return "unknown_error"
    
    def format_for_llm(self, result: SQLResult) -> str:
        """
        Format result as string for LLM consumption.
        
        Args:
            result: SQLResult
        
        Returns:
            Formatted string for LLM
        """
        parsed = self.parse(result)
        
        if parsed['status'] == 'error':
            return f"Error: {parsed['error_message']}"
        
        # Include summary and formatted rows
        output = parsed['summary']
        output += "\n\n" + parsed['formatted_text']
        
        return output

