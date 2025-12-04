"""
Chat Message and Conversation Schemas.

Defines Pydantic models for chat interactions including messages, requests, and responses.
Ensures type safety and validation for all conversation data.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single message in a conversation."""
    
    content: str = Field(..., min_length=1, description="Message text content")
    role: MessageRole = Field(default=MessageRole.USER, description="Who sent the message")
    timestamp: datetime = Field(default_factory=datetime.now, description="When message was sent")
    message_id: Optional[str] = Field(None, description="Unique message identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "What is the weather?",
                "role": "user",
                "timestamp": "2025-12-04T15:52:00Z",
                "message_id": "msg_123",
                "metadata": {}
            }
        }


class ChatRequest(BaseModel):
    """Chat API request with conversation history."""
    
    query: str = Field(..., min_length=1, description="Current user query")
    user_id: str = Field(..., description="Unique user identifier")
    session_id: Optional[str] = Field(None, description="Conversation session ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="Conversation history")
    max_tokens: int = Field(default=512, ge=1, le=4096, description="Maximum response tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature for randomness")
    include_context: bool = Field(default=True, description="Whether to include previous context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What was my previous question?",
                "user_id": "user_123",
                "session_id": "session_456",
                "messages": [
                    {
                        "content": "Hello",
                        "role": "user",
                        "timestamp": "2025-12-04T15:50:00Z"
                    },
                    {
                        "content": "Hello! How can I help?",
                        "role": "assistant",
                        "timestamp": "2025-12-04T15:50:05Z"
                    }
                ],
                "max_tokens": 512,
                "temperature": 0.7,
                "include_context": True
            }
        }


class ChatResponse(BaseModel):
    """Chat API response with generated message."""
    
    response: str = Field(..., description="Generated response text")
    message_id: str = Field(..., description="ID of generated message")
    user_id: str = Field(..., description="User who received response")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="When response was generated")
    tokens_used: int = Field(default=0, ge=0, description="Number of tokens consumed")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Response generation time in milliseconds")
    model_name: Optional[str] = Field(None, description="LLM model used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Your previous question was about the weather.",
                "message_id": "msg_789",
                "user_id": "user_123",
                "session_id": "session_456",
                "timestamp": "2025-12-04T15:52:00Z",
                "tokens_used": 45,
                "latency_ms": 250.5,
                "model_name": "granite3-dense:8b",
                "metadata": {}
            }
        }


class ConversationTurn(BaseModel):
    """Single turn in a conversation (user message + assistant response)."""
    
    user_message: ChatMessage = Field(..., description="User's input message")
    assistant_response: ChatMessage = Field(..., description="Assistant's output message")
    turn_number: int = Field(..., ge=1, description="Sequential turn number in conversation")
    intent: Optional[str] = Field(None, description="Detected user intent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_message": {
                    "content": "What is 2+2?",
                    "role": "user"
                },
                "assistant_response": {
                    "content": "2+2 equals 4.",
                    "role": "assistant"
                },
                "turn_number": 1,
                "intent": "factual_question"
            }
        }


class ConversationHistory(BaseModel):
    """Complete conversation history."""
    
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    turns: List[ConversationTurn] = Field(default_factory=list, description="All conversation turns")
    created_at: datetime = Field(default_factory=datetime.now, description="When conversation started")
    updated_at: datetime = Field(default_factory=datetime.now, description="When conversation was last updated")
    total_tokens_used: int = Field(default=0, ge=0, description="Total tokens for entire conversation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_456",
                "user_id": "user_123",
                "turns": [],
                "created_at": "2025-12-04T15:50:00Z",
                "updated_at": "2025-12-04T15:52:00Z",
                "total_tokens_used": 250
            }
        }
