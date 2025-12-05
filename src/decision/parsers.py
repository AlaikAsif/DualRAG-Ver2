"""Parse structured LLM outputs into decision objects."""

import json
import logging
import re
from typing import Dict, Any, Optional

from src.schemas.decisions import RoutingDecision
from src.decision.validators import validate_routing_decision
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


def parse_routing_decision(response: str) -> RoutingDecision:
    """
    Parse LLM response into RoutingDecision.
    
    Handles:
    - Valid JSON responses
    - Markdown JSON blocks (```json ... ```)
    - Malformed JSON with error recovery
    - Missing fields with sensible defaults
    
    Args:
        response: Raw LLM response text
        
    Returns:
        RoutingDecision instance
        
    Raises:
        ValueError: If response cannot be parsed
    """
    logger.debug(f"Parsing routing decision from: {response[:200]}...")
    
    # Try to extract JSON from response
    decision_data = _extract_json(response)
    
    if decision_data is None:
        logger.warning("Failed to extract JSON from response, using fallback")
        decision_data = _create_fallback_decision()
    
    # Normalize field names to lowercase
    decision_data = {k.lower(): v for k, v in decision_data.items()}
    
    # Apply defaults for missing fields
    decision_data = _apply_defaults(decision_data)
    
    # Validate and construct decision
    is_valid, decision, error_msg = validate_routing_decision(decision_data)
    
    if not is_valid:
        logger.warning(f"Validation failed: {error_msg}, using fallback")
        decision = _create_fallback_decision_object()
    
    return decision


def _extract_json(response: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from response text.
    
    Tries multiple strategies:
    1. Direct JSON parse
    2. Extract from markdown code block (```json ... ```)
    3. Regex extraction of {...}
    
    Args:
        response: Response text
        
    Returns:
        Parsed JSON dict or None
    """
    # Strategy 1: Direct parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Find JSON object {...}
    matches = re.findall(r'\{.*?\}', response, re.DOTALL)
    for match in reversed(matches):  # Try from end (more likely to be structured)
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    # Strategy 4: Attempt to fix common JSON issues
    fixed = _fix_json(response)
    if fixed:
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
    
    return None


def _fix_json(text: str) -> Optional[str]:
    """
    Attempt to fix malformed JSON.
    
    Fixes:
    - Single quotes → double quotes
    - Trailing commas
    - Missing quotes around keys
    - Control characters
    
    Args:
        text: Potentially malformed JSON
        
    Returns:
        Fixed JSON string or None
    """
    try:
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Single quotes to double quotes (cautiously)
        text = re.sub(r"'([^']*)':", r'"\1":', text)
        
        # Remove trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        # Try to parse to verify
        json.loads(text)
        return text
    
    except Exception:
        return None


def _apply_defaults(decision_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply defaults to decision data.
    
    Args:
        decision_data: Decision data dict
        
    Returns:
        Decision data with defaults applied
    """
    defaults = {
        "rag_type": "none",
        "needs_static_rag": False,
        "needs_sql_rag": False,
        "report_type": None,
        "response_mode": "direct",
        "reasoning": "Parsed from LLM response",
        "confidence": 0.7,
    }
    
    for key, default_value in defaults.items():
        if key not in decision_data or decision_data[key] is None:
            decision_data[key] = default_value
            logger.debug(f"Applied default for {key}: {default_value}")
    
    return decision_data


def _create_fallback_decision() -> Dict[str, Any]:
    """
    Create fallback decision data.
    
    Returns:
        Default decision data
    """
    return {
        "rag_type": "none",
        "needs_static_rag": False,
        "needs_sql_rag": False,
        "report_type": None,
        "response_mode": "direct",
        "reasoning": "Parsing fallback (invalid response format)",
        "confidence": 0.5,
    }


def _create_fallback_decision_object() -> RoutingDecision:
    """
    Create fallback RoutingDecision object.
    
    Returns:
        Default RoutingDecision
    """
    from src.schemas.decisions import RAGType, ResponseMode
    
    return RoutingDecision(
        rag_type=RAGType.NONE,
        needs_static_rag=False,
        needs_sql_rag=False,
        report_type=None,
        response_mode=ResponseMode.DIRECT,
        reasoning="Validation fallback (all parsing failed)",
        confidence=0.5,
    )


def parse_execution_plan(response: str) -> Dict[str, Any]:
    """
    Parse execution plan from LLM response.
    
    Args:
        response: LLM response text
        
    Returns:
        Execution plan dictionary
    """
    plan_data = _extract_json(response)
    
    if plan_data is None:
        logger.warning("Could not parse execution plan, using default")
        return _create_default_execution_plan()
    
    return plan_data


def _create_default_execution_plan() -> Dict[str, Any]:
    """
    Create default execution plan.
    
    Returns:
        Default execution plan
    """
    return {
        "chains": ["chat"],
        "order": [0],
        "parallel": False,
    }


def parse_confidence_score(response: str) -> float:
    """
    Extract confidence score from response.
    
    Looks for:
    - "confidence": <float>
    - confidence=<float>
    - confidence: <float>
    
    Args:
        response: Response text
        
    Returns:
        Confidence score 0.0-1.0 (default 0.5)
    """
    # Try JSON extraction first
    try:
        data = json.loads(response)
        if "confidence" in data:
            return float(data["confidence"])
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Try regex patterns
    patterns = [
        r'"confidence"\s*:\s*(\d+\.?\d*)',
        r'confidence\s*=\s*(\d+\.?\d*)',
        r'confidence:\s*(\d+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response)
        if match:
            try:
                score = float(match.group(1))
                if 0.0 <= score <= 1.0:
                    return score
            except ValueError:
                continue
    
    return 0.5  # Default
