"""Parse user customization requirements for reports."""

import logging
import json
import re
from typing import Dict, Any, Optional

from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class CustomizationParser:
    """Parse and validate report customization requirements."""
    
    def __init__(self):
        """Initialize parser."""
        self.valid_keys = {
            "layout": ["single_column", "two_column", "three_column"],
            "style": ["professional", "creative", "minimal", "corporate"],
            "colors": ["primary", "secondary", "accent"],
            "fonts": ["sans_serif", "serif", "monospace"],
            "sections": list,  # Any section names
            "logo_url": str,
            "company_name": str,
            "author": str,
            "footer_text": str,
            "include_toc": bool,
            "include_page_numbers": bool,
            "include_timestamps": bool,
        }
    
    def parse(self, customization_input: Any) -> Dict[str, Any]:
        """
        Parse customization input (string, dict, or natural language).
        
        Args:
            customization_input: Raw customization input
            
        Returns:
            Parsed customization dictionary
        """
        logger.debug(f"Parsing customization: {str(customization_input)[:100]}")
        
        if isinstance(customization_input, dict):
            return self._validate_dict(customization_input)
        elif isinstance(customization_input, str):
            return self._parse_string(customization_input)
        else:
            logger.warning(f"Unknown customization type: {type(customization_input)}")
            return {}
    
    def _parse_string(self, text: str) -> Dict[str, Any]:
        """
        Parse customization from string.
        
        Supports:
        - JSON format: {"layout": "two_column", ...}
        - Key-value: layout=two_column, style=professional
        - Natural language: "Make it professional with two columns"
        
        Args:
            text: Customization string
            
        Returns:
            Parsed customization dict
        """
        # Try JSON first
        try:
            data = json.loads(text)
            return self._validate_dict(data)
        except json.JSONDecodeError:
            pass
        
        # Try key=value format
        kv_match = re.findall(r'(\w+)\s*=\s*([^,]+)', text)
        if kv_match:
            customization = {}
            for key, value in kv_match:
                customization[key] = self._parse_value(value.strip())
            return self._validate_dict(customization)
        
        # Try natural language
        customization = self._parse_natural_language(text)
        return self._validate_dict(customization)
    
    def _parse_natural_language(self, text: str) -> Dict[str, Any]:
        """
        Parse customization from natural language.
        
        Args:
            text: Natural language text
            
        Returns:
            Parsed customization dict
        """
        customization = {}
        
        # Layout detection
        if "two column" in text.lower():
            customization["layout"] = "two_column"
        elif "three column" in text.lower():
            customization["layout"] = "three_column"
        elif "single column" in text.lower():
            customization["layout"] = "single_column"
        
        # Style detection
        if "professional" in text.lower():
            customization["style"] = "professional"
        elif "creative" in text.lower():
            customization["style"] = "creative"
        elif "minimal" in text.lower():
            customization["style"] = "minimal"
        elif "corporate" in text.lower():
            customization["style"] = "corporate"
        
        # Color detection
        if "dark" in text.lower() or "dark mode" in text.lower():
            customization["colors"] = {"primary": "#2d3748", "secondary": "#4a5568"}
        
        # Feature detection
        if "table of contents" in text.lower() or "toc" in text.lower():
            customization["include_toc"] = True
        
        if "page number" in text.lower():
            customization["include_page_numbers"] = True
        
        if "timestamp" in text.lower() or "date" in text.lower():
            customization["include_timestamps"] = True
        
        return customization
    
    def _validate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean customization dict.
        
        Args:
            data: Raw customization dict
            
        Returns:
            Validated customization dict
        """
        validated = {}
        
        for key, value in data.items():
            if key == "layout":
                if value in self.valid_keys["layout"]:
                    validated[key] = value
                else:
                    logger.warning(f"Invalid layout: {value}")
            
            elif key == "style":
                if value in self.valid_keys["style"]:
                    validated[key] = value
                else:
                    logger.warning(f"Invalid style: {value}")
            
            elif key == "colors":
                if isinstance(value, dict):
                    validated[key] = value
            
            elif key in ["logo_url", "company_name", "author", "footer_text"]:
                validated[key] = str(value)
            
            elif key in ["include_toc", "include_page_numbers", "include_timestamps"]:
                validated[key] = bool(value)
            
            elif key == "sections":
                if isinstance(value, list):
                    validated[key] = value
            
            else:
                logger.debug(f"Unknown customization key: {key}")
        
        return validated
    
    def _parse_value(self, value: str) -> Any:
        """
        Parse string value to appropriate type.
        
        Args:
            value: String value
            
        Returns:
            Parsed value
        """
        if value.lower() in ["true", "yes", "on"]:
            return True
        elif value.lower() in ["false", "no", "off"]:
            return False
        elif value.isdigit():
            return int(value)
        elif value.replace(".", "", 1).isdigit():
            return float(value)
        else:
            return value.strip('"\'')
    
    def merge_customizations(
        self,
        *customizations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge multiple customization dicts.
        
        Later customizations override earlier ones.
        
        Args:
            customizations: Multiple customization dicts
            
        Returns:
            Merged customization dict
        """
        merged = {}
        
        for customization in customizations:
            if customization:
                for key, value in customization.items():
                    if key == "colors" and key in merged and isinstance(value, dict):
                        # Merge colors dicts
                        merged[key].update(value)
                    else:
                        merged[key] = value
        
        return merged
    
    def get_defaults(self) -> Dict[str, Any]:
        """
        Get default customization values.
        
        Returns:
            Default customization dict
        """
        return {
            "layout": "single_column",
            "style": "professional",
            "colors": {
                "primary": "#1e40af",
                "secondary": "#3b82f6",
                "accent": "#10b981"
            },
            "fonts": "sans_serif",
            "include_toc": False,
            "include_page_numbers": False,
            "include_timestamps": True,
        }


# Global parser instance
_parser: Optional[CustomizationParser] = None


def get_customization_parser() -> CustomizationParser:
    """Get or create global customization parser."""
    global _parser
    if _parser is None:
        _parser = CustomizationParser()
    return _parser


def parse_customization(customization_input: Any) -> Dict[str, Any]:
    """
    Parse customization input.
    
    Args:
        customization_input: Customization input
        
    Returns:
        Parsed customization dict
    """
    parser = get_customization_parser()
    return parser.parse(customization_input)
