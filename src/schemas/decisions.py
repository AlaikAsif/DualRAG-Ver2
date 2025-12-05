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
    """Memory persistence requirements for follow-up interactions"""
    SESSION = "session"           # Keep context within current session only
    PERSISTENT = "persistent"     # Store across sessions for follow-ups
    NONE = "none"                 # No special memory requirements




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
    memory_requirement: MemoryRequirement = Field(
        default=MemoryRequirement.NONE,
        description=(
            "If follow-up interactions require memory; default NONE (no memory). "
            "Use SESSION for session-scoped follow-ups such as report customization, "
            "or PERSISTENT for cross-session storage."
        ),
    )
    follow_up_needed: bool = Field(default=False, description="TRUE if follow-up interactions are anticipated")

    def should_use_rag(self):
        return self.needs_static_rag or self.needs_sql_rag

    def get_rag_systems(self):
        systems = []
        if self.needs_static_rag:
            systems.append("static")
        if self.needs_sql_rag:
            systems.append("sql")
        return systems

    def is_high_confidence(self):
        return self.response_confidence == ResponseConfidence.HIGH

    def to_dict(self):
        return self.model_dump(exclude={'timestamp', 'session_id'})

    @model_validator(mode='after')
    def validate_rag_consistency(self):
        needs_static = self.needs_static_rag
        needs_sql = self.needs_sql_rag
        rag_type = self.rag_type

        if rag_type == RagType.Static and not needs_static: 
            raise ValueError("Inconsistent RAG decision: rag_type is Static but needs_static_rag is False")
        if rag_type == RagType.SQL and not needs_sql:
            raise ValueError("Inconsistent RAG decision: rag_type is SQL but needs_sql_rag is False")
        if rag_type == RagType.BOTH and (not needs_static or not needs_sql):
            raise ValueError("Inconsistent RAG decision: rag_type is BOTH but one of needs_static_rag or needs_sql_rag is False")
        if rag_type == RagType.NONE and (needs_static or needs_sql):
            raise ValueError("Inconsistent RAG decision: rag_type is NONE but one of needs_static_rag or needs_sql_rag is True")
        return self

    @field_validator('static_rag_query')
    @classmethod
    def validate_static_rag_query(cls, v, info):
        if info.data.get("needs_static_rag") and not v:
            raise ValueError("Static RAG query must be provided if needs_static_rag is True")
        return v

    @field_validator('sql_intent')
    @classmethod
    def validate_sql_intent(cls, v, info):
        if info.data.get("needs_sql_rag") and not v:
            raise ValueError("SQL intent must be provided if needs_sql_rag is True")
        return v

    @field_validator('report_customization')
    @classmethod
    def report_customization_validator(cls, v, info):
        if info.data.get("needs_report") and info.data.get("report_type") == ReportType.CUSTOM and not v:
            raise ValueError("Report customization must be provided if report_type is CUSTOM and needs_report is True")
        return v

    @field_validator('memory_requirement')
    @classmethod
    def follow_up_memory_validator(cls, v, info):
        if info.data.get("follow_up_needed") and not v:
            raise ValueError("Memory requirement must be specified if follow_up_needed is True")
        return v

    @field_validator('clarification_questions')
    @classmethod
    def clarification_questions_validator(cls, v, info):
        if info.data.get("requires_clarification") and (not v or len(v) == 0):
            raise ValueError("Clarification questions must be provided if requires_clarification is True")
        return v

    @model_validator(mode='after')
    def validate_response_model(self):
        can_answer = self.can_provide_direct_answer
        requires_clarification = self.requires_clarification
        response_mode = self.response_mode
        needs_report = self.needs_report

        if response_mode == ResponseMode.DIRECT and not can_answer:
            raise ValueError("response_mode is DIRECT but can_provide_direct_answer is False")
        
        if response_mode == ResponseMode.REPORT and not needs_report:
            raise ValueError("response_mode is REPORT but needs_report is False")
        
        if response_mode == ResponseMode.CLARIFY and not requires_clarification:
            raise ValueError("response_mode is CLARIFY but requires_clarification is False")
        
        return self


"""
////////////////////////
Static Rage Descisions 
////////////////////////
"""

class StaticRagDecision(BaseModel):
    query: str = Field(description="Reformulated query for static RAG retrieval")
    filters: Optional[Dict[str, Union[str, int, float]]] = Field(None,description="Metadata filters for document retrieval eg: {'category': 'finance', 'date_after': '2023-01-01'}")
    similarity_threshold: float = Field(0.7,ge=0.0,le=1.0,description="Minimum similarity score for results")       
    rerank: bool = Field(True,description="Whether to rerank results")    
"""
////////////////////////
SQL Rage Descisions
////////////////////////
"""

class SQLRagDecision(BaseModel):
    intent: str = Field(description="SQL retrieval intent eg: 'top 5 customers by revenue', last sales figures etc")
    tables_needed: Optional[List[str]] = Field(None,description="List of database tables needed for the query")
    aggregations: Optional[List[str]] = Field(None,description="List of aggregations needed eg: SUM, AVG, COUNT")
    time_range: Optional[Dict[str, str]] = Field(None,description="Time range for data retrieval eg: {'start_date': '2023-01-01', 'end_date': '2023-12-31'}")
    limit: int = Field(1000,ge=1,le=10000,description="Maximum number of records to retrieve")
    requires_join: bool = Field(False,description="Whether joins between tables are required")

"""
////////////////////////
Report Descisions
////////////////////////
"""


class ReportDecision(BaseModel):
    report_type: ReportType = Field(description="Type of report needed")
    customization: Optional[str] = Field(None,description="User's custom report requirements (charts, filters, etc.)")
    title: str = Field(description="Title of the report")

    #custom report specifics
    data_sources: Optional[List[str]] = Field(None,description="List of data sources to include in the report")
    metrics: Optional[List[str]] = Field(None,description="Key metrics to highlight in the report")
    columns: Optional[List[str]] = Field(None,description="Specific columns to include in the report")
    formatting_preferences: Optional[Dict[str, str]] = Field(None,description="Formatting preferences eg: {'font_size': '12pt', 'color_scheme': 'dark'}")
    
    #template
    template_name: Optional[str] = Field(None,description="Predefined report template to use if any")
    custom_css_styles: Optional[str] = Field(None,description="Custom CSS styles for report formatting if any")
"""
////////////////////////
Clarrification Descisions
////////////////////////
"""

class ClarificationDecision(BaseModel):
    reason: str = Field(description="Reason why clarification is needed")
    ambiguities: Optional[List[str]] = Field(None,description="List of ambiguous aspects in the user's query that need clarification")
    questions: List[str] = Field(description="List of clarification questions to ask the user",min_items=1,max_items=3)
    suggested_options: Optional[List[str]] = Field(None,description="Suggested options for the user to choose from if applicable")

"""
////////////////////////
Memory Descisions
////////////////////////
"""
class MemoryDecision(BaseModel):
    """Details about memory requirements for follow-up interactions"""
    purpose: Optional[str] = Field(default="report_customization", description="High-level purpose/namespace for this memory (e.g., 'report_customization')")
    followup_details: Optional[str] = Field(None,description="Details about the anticipated follow-up interactions")
    context_to_preserve: Optional[List[str]] = Field(None,description="Key context elements to preserve between turns eg: ['user_preferences', 'previous_queries', 'report_state']")
    custom_report_memory: Optional[str] = Field(None,description="Custom memory requirements for report generation if any")
""" 
////////////////////////
Execution Descisions
////////////////////////
"""

class ExecutionPlan(BaseModel):
    """
    Complete execution plan combining all decisions
    Generated by orchestrator after LLM routing decision
    """
    
    routing_decision: RoutingDecision = Field(description="Main routing decision")
    static_rag: Optional[StaticRagDecision] = Field(None,description="Static RAG retrieval details")
    sql_rag: Optional[SQLRagDecision] = Field(None,description="SQL RAG retrieval details")
    report: Optional[ReportDecision] = Field(None,description="Report generation details")
    clarification: Optional[ClarificationDecision] = Field(None,description="Clarification details if needed")
    memory: Optional[MemoryDecision] = Field(None,description="Memory management details for follow-up interactions")
    estimated_execution_time: float = Field(description="Estimated time to execute (seconds)")
    

"""
////////////////////////
Descision validation
////////////////////////
"""

class DecisionValidator:
    """Validate LLM routing decisions"""
    
    @staticmethod
    def validate_routing_decision(decision: RoutingDecision) -> tuple[bool, List[str]]:
        """
        Validate routing decision
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        if decision.rag_type == RagType.NONE and decision.should_use_rag():
            errors.append("rag_type is NONE but RAG flags are set")
        
        if decision.response_confidence == ResponseConfidence.LOW:
            errors.append("Low confidence decision - may need human review")
        
        if decision.requires_clarification and not decision.clarification_questions:
            errors.append("requires_clarification=True but no questions provided")
        
        if decision.needs_report and decision.report_type == ReportType.NONE:
            errors.append("needs_report=True but report_type is NONE")
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def validate_execution_plan(plan: ExecutionPlan) -> tuple[bool, List[str]]:
        """
        Validate complete execution plan
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Validate routing decision first
        is_valid, routing_errors = DecisionValidator.validate_routing_decision(
            plan.routing_decision
        )
        errors.extend(routing_errors)
        
        if plan.routing_decision.needs_static_rag and not plan.static_rag:
            errors.append("Missing static_rag decision")
        
        if plan.routing_decision.needs_sql_rag and not plan.sql_rag:
            errors.append("Missing sql_rag decision")
        
        if plan.routing_decision.needs_report and not plan.report:
            errors.append("Missing report decision")
        
        return (len(errors) == 0, errors)



"""
////////////////////////
Helper functions
////////////////////////
"""

def create_simple_routing_decision(
    query: str,
    use_static: bool = False,
    use_sql: bool = False,
    generate_report: bool = False
) -> RoutingDecision:
    """
    Helper function to create simple routing decisions
    
    Useful for testing or overriding LLM decisions
    """
    
    if use_static and use_sql:
        rag_type = RagType.BOTH
    elif use_static:
        rag_type = RagType.Static
    elif use_sql:
        rag_type = RagType.SQL
    else:
        rag_type = RagType.NONE
    
    if generate_report:
        response_mode = ResponseMode.REPORT
    elif use_static or use_sql:
        response_mode = ResponseMode.SEARCH_THEN_ANSWER
    else:
        response_mode = ResponseMode.DIRECT
    
    return RoutingDecision(
        rag_type=rag_type,
        needs_static_rag=use_static,
        needs_sql_rag=use_sql,
        static_rag_query=query if use_static else None,
        sql_intent=query if use_sql else None,
        needs_report=generate_report,
        report_type=ReportType.DEFAULT if generate_report else ReportType.NONE,
        response_mode=response_mode,
        can_provide_direct_answer=not (use_static or use_sql),
        requires_clarification=False,
        query_intent=QueryIntent.FACTUAL,
        response_confidence=ResponseConfidence.HIGH,
        reasoning="Manually created decision",
        memory_requirement=MemoryRequirement.SESSION,
        follow_up_needed=False
    )



__all__ = ["RoutingDecision","StaticRagDecision","SQLRagDecision","ReportDecision","ClarificationDecision","MemoryDecision","ExecutionPlan","DecisionValidator","create_simple_routing_decision"]