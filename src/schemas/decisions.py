# LLM routing decision types
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Union

"""
///////////////////////
All possible routing
///////////////////////
"""
class RagType(str,Enum):
    "types of rag available"
    Static = "static"
    SQL = "sql"
    BOTH = "both"
    NONE = "none"

class ReportType(str,Enum):
    "types of reports available"
    NONE = "none"
    DEFAULT = "default"
    CUSTOM = "custom"

class QueryIntent(str,Enum):
    """User's query intent"""
    FACTUAL = "factual"            # Simple fact lookup
    ANALYTICAL = "analytical"      # Requires data analysis
    CONVERSATIONAL = "conversational"  # Just chatting
    REPORT_REQUEST = "report_request"  # Wants a report
    COMPARISON = "comparison"      # Compare multiple things
    TROUBLESHOOTING = "troubleshooting"  # Problem solving

class ResponseConfidence(str,Enum):
    """LLM's confidence in its response"""
    HIGH = "high"      
    MEDIUM = "medium"  
    LOW = "low"      

class ResponseMode(str,Enum):
    DIRECT = "direct"        
    SEARCH_THEN_ANSWER = "search_then_answer"
    CLARIFY = "clarify"
    REPORT = "report" 

class MemoryRequirement(str,Enum):
    LongTermFollowUp = "long_term"




"""
/////////////////////////
Decision Data Models
/////////////////////////
"""

class RoutingDecision(BaseModel):
    """
    Main routing decision from LLM orchestrator
    
    The LLM analyzes the user's query and decides:
    1. What RAG system(s) to use
    2. Whether to generate a report
    3. How to respond
    """

    #rag decision
    rag_type: RagType = Field(description="Descide Which RAG system(s) to use")
    needs_static_rag: bool = Field(description="TRUE if document based/knowledge base retrieval is needed")
    needs_sql_rag: bool = Field(description="TRUE if database retrieval is needed")
    static_rag_query:Optional[str] = Field(default=None,description="Reformulated query for static RAG")
    sql_intent:Optional[str] = Field(default=None,description="What data to retrieve from SQL eg: 'top 5 customers by revenue', last sales figures etc")

    #report decision
    needs_report: bool = Field(description="TRUE if a report generation is needed")
    report_type: ReportType = Field(description="Type of report needed if any")
    report_customization: Optional[str] = Field(None,description="User's custom report requirements (charts, filters, etc.) or What columns/metrics to include in the report or Changs to main report titles or subheadings")

    #response decision
    response_mode: ResponseMode = Field(description="How the LLM should respond to the user")
    can_provide_direct_answer: bool = Field(description="TRUE if LLM is confident to answer directly without retrieval")
    requires_clarification: bool = Field(description="TRUE if LLM needs more info from user before answering")
    clarification_questions: Optional[List[str]] = Field(None,description="List of clarification questions to ask the user if needed")

    #intent and confidence
    query_intent: QueryIntent = Field(description="User's query intent")
    response_confidence: ResponseConfidence = Field(description="LLM's confidence in its response")
    reasoning: Optional[str] = Field(None,description="LLM's reasoning behind its decisions")

    #metadata
    timestamp: datetime = Field(default_factory=datetime.now,description="Timestamp of the decision")
    session_id: Optional[str] = Field(None,description="User session identifier for context tracking")

    #memory
    memory_requirement: MemoryRequirement = Field(description="If follow-up interactions require long-term memory")
    follow_up_needed: bool = Field(description="TRUE if follow-up interactions are anticipated")

"""
////////////////////////
Validation
////////////////////////
"""

@model_validator
def validate_rag_consistency(cls,values):
    needs_static = values.get("needs_static_rag")
    needs_sql = values.get("needs_sql_rag")
    rag_type = values.get("rag_type")

    if rag_type == RagType.Static and not needs_static: 
        raise ValueError("Inconsistent RAG decision: rag_type is Static but needs_static_rag is False")
    if rag_type == RagType.SQL and not needs_sql:
        raise ValueError("Inconsistent RAG decision: rag_type is SQL but needs_sql_rag is False")
    if rag_type == RagType.BOTH and (not needs_static or not needs_sql):
        raise ValueError("Inconsistent RAG decision: rag_type is BOTH but one of needs_static_rag or needs_sql_rag is False")
    if rag_type ==RagType.NONE and (needs_static or needs_sql):
        raise ValueError("Inconsistent RAG decision: rag_type is NONE but one of needs_static_rag or needs_sql_rag is True")
    return values

@field_validator
def validate_static_rag_query(cls,v,values):
    if values.get("needs_static_rag") and not v:
        raise ValueError("Static RAG query must be provided if needs_static_rag is True")
    return v

@field_validator
def validate_sql_intent(cls,v,values):
    if values.get("needs_sql_rag") and not v:
        raise ValueError("SQL intent must be provided if needs_sql_rag is True")
    return v

@field_validator
def report_customization_validator(cls,v,values):
    if values.get("needs_report") and values.get("report_type") == ReportType.CUSTOM and not v:
        raise ValueError("Report customization must be provided if report_type is CUSTOM and needs_report is True")
    return v

@field_validator
def follow_up_memory_validator(cls,v,values):
    if values.get("follow_up_needed") and not v:
        raise ValueError("Memory requirement must be specified if follow_up_needed is True")
    return v

@field_validator
def clarification_questions_validator(cls,v,values):
    if values.get("requires_clarification") and (not v or len(v) == 0):
        raise ValueError("Clarification questions must be provided if requires_clarification is True")
    return v

@model_validator
def validate_response_model(cls,values):
    can_answer = values.get("can_provide_direct_answer")
    requires_clarification = values.get("requires_clarification")
    response_mode = values.get("response_mode")
    needs_report = values.get("needs_report")

    if response_mode == ResponseMode.DIRECT and not can_answer:
            raise ValueError("response_mode is DIRECT but can_answer_directly is False")
        
    if response_mode == ResponseMode.REPORT and not needs_report:
        raise ValueError("response_mode is REPORT but needs_report is False")
    
    if response_mode == ResponseMode.CLARIFY and not requires_clarification:
        raise ValueError("response_mode is CLARIFY but requires_clarification is False")
    
    return values

"""
////////////////////////
Helpers Functions
////////////////////////
"""

def should_use_rag(self):
    return self.rag_needs_static_rag or self.needs_sql_rag

def get_rag_systems(self):
    systems = []
    if self.needs_static_rag:
        systems.append("static")
    if self.needs_sql_rag:
        systems.append("sql")
    return systems

def isHighConfidence(self):
    return self.response_confidence == ResponseConfidence.HIGH

def toDict(self):
    return self.dict(exclude={'timestamp', 'session_id'})


"""
////////////////////////
Static Rage Descisions 
////////////////////////
"""

class StaticRagDecision(BaseModel):
    pass

"""
////////////////////////
SQL Rage Descisions
////////////////////////
"""

class SQLRagDecision(BaseModel):
    pass

"""
////////////////////////
Report Descisions
////////////////////////
"""


class ReportDecision(BaseModel):
    pass

"""
////////////////////////
Clarrification Descisions
////////////////////////
"""

class ClarificationDecision(BaseModel):
    pass

"""
////////////////////////
Memory Descisions
////////////////////////
"""
class MemoryDecision(BaseModel):
    pass

""" 
////////////////////////
Execution Descisions
////////////////////////
"""

class ExecutionDecision(BaseModel):
    pass

"""
////////////////////////
Descision validation
////////////////////////
"""

class DecisionValidator:
    pass

"""
////////////////////////
Helper functions
////////////////////////
"""

def simple_routing_decision():
    pass




