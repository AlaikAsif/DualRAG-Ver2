"""Multi-stage routing orchestration with LLM and semantic fallback."""

import logging
from typing import Optional, Dict, Any
from enum import Enum

from src.chains.llm import get_llm
from src.schemas.decisions import RoutingDecision, RAGType, ResponseMode
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class ChainType(str, Enum):
    """Available chain types for routing."""
    STATIC_RAG = "static_rag"
    SQL_RAG = "sql_rag"
    CHAT = "chat"
    REPORT = "report"
    FOLLOWUP = "followup"


class Router:
    """Multi-stage routing with LLM primary and semantic fallback."""
    
    def __init__(self):
        """Initialize router."""
        self.llm = get_llm()
        self.confidence_threshold = 0.7
    
    async def route(self, query: str) -> RoutingDecision:
        """
        Route query through multi-stage decision process.
        
        Stage 1: LLM-based routing with structured output
        Stage 2: Semantic fallback using embeddings similarity
        Stage 3: Static fallback to chat chain
        
        Args:
            query: User query to route
            
        Returns:
            RoutingDecision with selected chain and confidence
        """
        logger.info(f"Routing query: {query[:100]}...")
        
        try:
            # Stage 1: LLM-based routing
            decision = await self._llm_route(query)
            
            if decision.confidence >= self.confidence_threshold:
                logger.info(
                    f"Stage 1 (LLM): Routed to {decision.rag_type} "
                    f"with confidence {decision.confidence:.2%}"
                )
                return decision
            
            logger.info(
                f"Stage 1 (LLM) low confidence ({decision.confidence:.2%}), "
                f"attempting semantic fallback"
            )
        
        except Exception as e:
            logger.warning(f"Stage 1 (LLM) failed: {str(e)}, attempting fallback")
        
        # Stage 2: Semantic fallback
        try:
            decision = await self._semantic_route(query)
            logger.info(
                f"Stage 2 (Semantic): Routed to {decision.rag_type} "
                f"with confidence {decision.confidence:.2%}"
            )
            return decision
        
        except Exception as e:
            logger.warning(f"Stage 2 (Semantic) failed: {str(e)}, using static fallback")
        
        # Stage 3: Static fallback
        decision = self._static_fallback()
        logger.info(f"Stage 3 (Static): Routed to {decision.rag_type}")
        return decision
    
    async def _llm_route(self, query: str) -> RoutingDecision:
        """
        Stage 1: LLM-based routing with structured function calling.
        
        Args:
            query: User query
            
        Returns:
            RoutingDecision from LLM structured output
        """
        system_prompt = """You are an intelligent routing system. Analyze the user query and decide which chain to use.

Return a JSON object with:
{
  "rag_type": "static"|"sql"|"none",
  "needs_static_rag": boolean,
  "needs_sql_rag": boolean,
  "report_type": null|"summary"|"detailed"|"comparison",
  "response_mode": "contextual"|"direct"|"exploratory",
  "reasoning": "brief explanation",
  "confidence": 0.0-1.0
}

Rules:
- Use "static" RAG for document/knowledge questions
- Use "sql" RAG for data/database queries
- Use "none" for general chat
- Return confidence 0.0-1.0 based on certainty
"""
        
        response = await self.llm.ainvoke({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        })
        
        from src.decision.parsers import parse_routing_decision
        decision = parse_routing_decision(response.content)
        
        return decision
    
    async def _semantic_route(self, query: str) -> RoutingDecision:
        """
        Stage 2: Semantic fallback using embeddings similarity.
        
        Args:
            query: User query
            
        Returns:
            RoutingDecision based on semantic similarity
        """
        try:
            from src.rag.static.embeddings import get_embeddings
            
            embeddings = get_embeddings()
            query_embedding = embeddings.embed_query(query)
            
            # Compare against template embeddings
            templates = {
                RAGType.STATIC: "Find information from documents about {topic}",
                RAGType.SQL: "Query the database for {metric} data",
                RAGType.NONE: "Have a general conversation",
            }
            
            # Find most similar template
            similarities = {}
            for rag_type, template in templates.items():
                template_embedding = embeddings.embed_query(template)
                similarity = self._cosine_similarity(query_embedding, template_embedding)
                similarities[rag_type] = similarity
            
            best_rag_type = max(similarities, key=similarities.get)
            confidence = similarities[best_rag_type]
            
            return RoutingDecision(
                rag_type=best_rag_type,
                needs_static_rag=(best_rag_type == RAGType.STATIC),
                needs_sql_rag=(best_rag_type == RAGType.SQL),
                report_type=None,
                response_mode=ResponseMode.CONTEXTUAL,
                reasoning=f"Semantic similarity routing (max: {confidence:.2%})",
                confidence=confidence
            )
        
        except Exception as e:
            logger.error(f"Semantic routing failed: {str(e)}")
            raise
    
    def _static_fallback(self) -> RoutingDecision:
        """
        Stage 3: Default fallback to chat chain.
        
        Returns:
            Default RoutingDecision
        """
        return RoutingDecision(
            rag_type=RAGType.NONE,
            needs_static_rag=False,
            needs_sql_rag=False,
            report_type=None,
            response_mode=ResponseMode.DIRECT,
            reasoning="Static fallback (all routing stages failed)",
            confidence=0.5
        )
    
    @staticmethod
    def _cosine_similarity(vec1: list, vec2: list) -> float:
        """
        Calculate cosine similarity between vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score 0.0-1.0
        """
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def set_confidence_threshold(self, threshold: float):
        """
        Set confidence threshold for routing decisions.
        
        Args:
            threshold: Threshold value 0.0-1.0
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        self.confidence_threshold = threshold
        logger.info(f"Set routing confidence threshold to {threshold:.2%}")


# Global router instance
_router: Optional[Router] = None


def get_router() -> Router:
    """Get or create global router instance."""
    global _router
    if _router is None:
        _router = Router()
    return _router
