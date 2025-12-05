"""Validate LLM routing decisions against schema."""

import logging
from typing import Dict, Any, Tuple
from pydantic import ValidationError

from src.schemas.decisions import RoutingDecision, RagType, ResponseMode
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class RoutingValidator:
    """Validate routing decisions for safety and correctness."""
    
    def __init__(self):
        """Initialize validator."""
        self.min_confidence = 0.0
        self.max_confidence = 1.0
    
    def validate(self, decision_data: Dict[str, Any]) -> Tuple[bool, RoutingDecision, str]:
        """
        Validate routing decision data.
        
        Args:
            decision_data: Raw decision data from LLM
            
        Returns:
            Tuple of (is_valid, RoutingDecision, error_message)
        """
        try:
            # Validate required fields exist
            required_fields = [
                "rag_type",
                "needs_static_rag",
                "needs_sql_rag",
                "response_mode",
                "confidence"
            ]
            
            missing_fields = [f for f in required_fields if f not in decision_data]
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.warning(f"Validation failed: {error_msg}")
                return False, None, error_msg
            
            # Validate rag_type enum
            rag_type_str = decision_data.get("rag_type", "").lower()
            try:
                # Handle both 'static' and 'Static' variants
                if rag_type_str == "static":
                    rag_type = RagType.Static
                elif rag_type_str == "sql":
                    rag_type = RagType.SQL
                elif rag_type_str == "both":
                    rag_type = RagType.BOTH
                elif rag_type_str == "none":
                    rag_type = RagType.NONE
                else:
                    raise ValueError(f"Invalid rag_type: {rag_type_str}")
            except ValueError:
                error_msg = f"Invalid rag_type: {rag_type_str}. Must be one of {[e.value for e in RagType]}"
                logger.warning(f"Validation failed: {error_msg}")
                return False, None, error_msg
            
            # Validate response_mode enum
            response_mode_str = decision_data.get("response_mode", "").upper()
            try:
                response_mode = ResponseMode(response_mode_str)
            except ValueError:
                error_msg = f"Invalid response_mode: {response_mode_str}. Must be one of {[e.value for e in ResponseMode]}"
                logger.warning(f"Validation failed: {error_msg}")
                return False, None, error_msg
            
            # Validate confidence score
            confidence = float(decision_data.get("confidence", 0.0))
            if not (self.min_confidence <= confidence <= self.max_confidence):
                error_msg = f"Confidence {confidence} out of range [{self.min_confidence}, {self.max_confidence}]"
                logger.warning(f"Validation failed: {error_msg}")
                return False, None, error_msg
            
            # Validate boolean fields
            needs_static_rag = bool(decision_data.get("needs_static_rag", False))
            needs_sql_rag = bool(decision_data.get("needs_sql_rag", False))
            
            # Logical validation: if needs_static_rag/sql_rag is true, rag_type must match
            if needs_static_rag and rag_type != RagType.Static:
                logger.warning("needs_static_rag=true but rag_type != Static, correcting")
                rag_type = RagType.Static
            
            if needs_sql_rag and rag_type != RagType.SQL:
                logger.warning("needs_sql_rag=true but rag_type != SQL, correcting")
                rag_type = RagType.SQL
            
            # Build validated decision
            decision = RoutingDecision(
                rag_type=rag_type,
                needs_static_rag=needs_static_rag,
                needs_sql_rag=needs_sql_rag,
                report_type=decision_data.get("report_type"),
                response_mode=response_mode,
                reasoning=decision_data.get("reasoning", ""),
                confidence=confidence
            )
            
            logger.debug(f"Validation successful: {decision}")
            return True, decision, ""
        
        except ValidationError as e:
            error_msg = f"Pydantic validation error: {str(e)}"
            logger.warning(f"Validation failed: {error_msg}")
            return False, None, error_msg
        
        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            logger.error(f"Validation failed: {error_msg}")
            return False, None, error_msg
    
    def validate_execution_plan(self, plan: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate an execution plan structure.
        
        Args:
            plan: Execution plan dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required fields
            required_fields = ["chains", "order", "parallel"]
            missing = [f for f in required_fields if f not in plan]
            if missing:
                error_msg = f"Missing fields: {', '.join(missing)}"
                return False, error_msg
            
            # Validate chains list
            if not isinstance(plan["chains"], list):
                return False, "chains must be a list"
            
            if not plan["chains"]:
                return False, "chains cannot be empty"
            
            # Validate order list matches chains
            chains = plan["chains"]
            order = plan.get("order", [])
            
            if set(order) != set(range(len(chains))):
                return False, "order must contain indices 0..len(chains)-1"
            
            # Validate parallel boolean
            if not isinstance(plan.get("parallel"), bool):
                return False, "parallel must be boolean"
            
            logger.debug("Execution plan validation successful")
            return True, ""
        
        except Exception as e:
            error_msg = f"Plan validation error: {str(e)}"
            return False, error_msg
    
    def set_confidence_range(self, min_conf: float, max_conf: float):
        """
        Set acceptable confidence range.
        
        Args:
            min_conf: Minimum confidence
            max_conf: Maximum confidence
        """
        if not (0.0 <= min_conf <= max_conf <= 1.0):
            raise ValueError("Invalid confidence range")
        self.min_confidence = min_conf
        self.max_confidence = max_conf
        logger.info(f"Set confidence range to [{min_conf}, {max_conf}]")


# Global validator instance
_validator: RoutingValidator = RoutingValidator()


def validate_routing_decision(decision_data: Dict[str, Any]) -> Tuple[bool, RoutingDecision, str]:
    """
    Validate a routing decision.
    
    Args:
        decision_data: Raw decision data
        
    Returns:
        Tuple of (is_valid, RoutingDecision, error_message)
    """
    return _validator.validate(decision_data)


def validate_execution_plan(plan: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate an execution plan.
    
    Args:
        plan: Execution plan
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    return _validator.validate_execution_plan(plan)
