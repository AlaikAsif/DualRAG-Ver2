"""
Followup and Context Schemas.

Defines Pydantic models for managing conversation context, follow-up detection,
and multi-turn conversation state.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class InteractionContext(BaseModel):
    """Context from a previous interaction."""
    
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="Assistant's response")
    timestamp: datetime = Field(..., description="When interaction occurred")
    entities_mentioned: List[str] = Field(default_factory=list, description="Entities mentioned (people, places, things)")
    intent: Optional[str] = Field(None, description="Detected user intent")
    key_terms: List[str] = Field(default_factory=list, description="Important keywords from interaction")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are our Q3 sales?",
                "response": "Q3 sales were $500,000...",
                "timestamp": "2025-12-04T15:50:00Z",
                "entities_mentioned": ["Q3", "sales"],
                "intent": "data_query",
                "key_terms": ["quarterly", "revenue", "financial"]
            }
        }


class ConversationContext(BaseModel):
    """Overall conversation context for handling follow-ups."""
    
    session_id: str = Field(..., description="Conversation session ID")
    user_id: str = Field(..., description="User identifier")
    last_query: Optional[str] = Field(None, description="Last user query")
    last_response: Optional[str] = Field(None, description="Last assistant response")
    interaction_history: List[InteractionContext] = Field(
        default_factory=list,
        max_items=10,
        description="Recent interactions (up to 10)"
    )
    key_entities: Dict[str, str] = Field(default_factory=dict, description="Important entities being discussed")
    common_topics: List[str] = Field(default_factory=list, description="Topics discussed in conversation")
    last_rag_type_used: Optional[str] = Field(None, description="Last RAG system used (static, sql, etc.)")
    turn_count: int = Field(default=0, ge=0, description="Number of conversation turns so far")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_456",
                "user_id": "user_123",
                "last_query": "How did Q3 compare to Q2?",
                "interaction_history": [],
                "key_entities": {"Q2": "previous_quarter", "Q3": "current_quarter"},
                "common_topics": ["sales", "quarterly_reports"],
                "last_rag_type_used": "sql",
                "turn_count": 5
            }
        }


class FollowupAnalysis(BaseModel):
    """Analysis of whether current query is a follow-up."""
    
    is_followup: bool = Field(..., description="Whether this is a follow-up question")
    followup_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in follow-up detection")
    related_to_previous: bool = Field(default=False, description="Is it related to previous query?")
    previous_entity_reference: Optional[str] = Field(None, description="Which previous entity is referenced?")
    implicit_context: List[str] = Field(default_factory=list, description="Context implied from previous turn")
    suggested_rag_type: Optional[str] = Field(None, description="Suggested RAG type for this follow-up")
    clarification_needed: bool = Field(default=False, description="Is clarification needed?")
    clarification_questions: List[str] = Field(default_factory=list, description="Questions to clarify ambiguity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_followup": True,
                "followup_confidence": 0.95,
                "related_to_previous": True,
                "previous_entity_reference": "Q3_sales",
                "implicit_context": ["We were discussing quarterly sales", "Focus on revenue metrics"],
                "suggested_rag_type": "sql",
                "clarification_needed": False
            }
        }


class FollowupRequest(BaseModel):
    """Request to analyze and handle a follow-up question."""
    
    query: str = Field(..., min_length=1, description="Current user query")
    conversation_context: ConversationContext = Field(..., description="Previous conversation context")
    resolve_pronouns: bool = Field(default=True, description="Attempt to resolve pronouns (it, this, that)")
    include_implicit_context: bool = Field(default=True, description="Include implicit context in response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "How did it compare to the previous quarter?",
                "conversation_context": {
                    "session_id": "session_456",
                    "user_id": "user_123",
                    "last_query": "What were Q3 sales?",
                    "turn_count": 5
                },
                "resolve_pronouns": True,
                "include_implicit_context": True
            }
        }


class FollowupResponse(BaseModel):
    """Response with follow-up analysis and enriched query."""
    
    original_query: str = Field(..., description="Original query as asked")
    enriched_query: str = Field(..., description="Query with context resolved")
    followup_analysis: FollowupAnalysis = Field(..., description="Follow-up analysis results")
    resolved_pronouns: Dict[str, str] = Field(default_factory=dict, description="Pronoun resolutions (this -> Q3 sales)")
    context_summary: str = Field(default="", description="Summary of relevant context to pass to next stage")
    suggested_next_step: str = Field(default="retrieve", description="Suggested processing step (retrieve, generate, clarify)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_query": "How did it compare?",
                "enriched_query": "How did Q3 sales compare to Q2 sales?",
                "followup_analysis": {
                    "is_followup": True,
                    "followup_confidence": 0.95,
                    "related_to_previous": True
                },
                "resolved_pronouns": {"it": "Q3 sales"},
                "context_summary": "Comparing quarterly sales figures",
                "suggested_next_step": "retrieve"
            }
        }


class ContextPreservation(BaseModel):
    """Strategy for preserving context across turns."""
    
    preserve_entities: bool = Field(default=True, description="Remember entities mentioned")
    preserve_topics: bool = Field(default=True, description="Remember conversation topics")
    preserve_rag_results: bool = Field(default=True, description="Cache recent RAG results")
    max_context_turns: int = Field(default=5, ge=1, le=10, description="Max previous turns to keep")
    context_expiry_minutes: int = Field(default=30, ge=1, description="Minutes before context expires")
    
    class Config:
        json_schema_extra = {
            "example": {
                "preserve_entities": True,
                "preserve_topics": True,
                "preserve_rag_results": True,
                "max_context_turns": 5,
                "context_expiry_minutes": 30
            }
        }
