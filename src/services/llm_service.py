"""
LLM service for generating responses using OpenAI.
"""
import logging
import json
from typing import Dict, List, Optional, Tuple
from enum import Enum
from openai import OpenAI

from src.config.settings import settings

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Types of user queries for classification."""

    GENERAL_QUESTION = "general_question"
    TECHNICAL_ISSUE = "technical_issue"
    URGENT_ISSUE = "urgent_issue"
    ACCESS_REQUEST = "access_request"
    FEATURE_REQUEST = "feature_request"
    FEEDBACK = "feedback"
    OTHER = "other"


class ResponseType(str, Enum):
    """Types of responses the bot can generate."""

    DIRECT_ANSWER = "direct_answer"
    REQUEST_MORE_INFO = "request_more_info"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    ACKNOWLEDGE = "acknowledge"


class LLMService:
    """Service for interacting with LLMs (specifically OpenAI)."""

    def __init__(self):
        """Initialize the LLM service with API key from settings."""
        self.api_key = settings.openai_api_key
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4"  # Can be configured from settings

    def analyze_query(self, query: str) -> Tuple[QueryType, Dict, float]:
        """
        Analyze the user query to classify it and extract relevant information.
        
        Args:
            query: The user's message text
            
        Returns:
            Tuple containing:
            - QueryType: The classified type of query
            - Dict: Extracted information (topic, system, etc.)
            - float: Urgency score (0-1)
        """
        if not query:
            return QueryType.OTHER, {}, 0.0

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are an AI assistant that helps classify support queries and extract relevant information.
                        Analyze the user's message and provide:
                        1. The type of query (technical_issue, urgent_issue, general_question, access_request, feature_request, feedback, other)
                        2. Extracted information (topic, system, application, error messages, etc.)
                        3. An urgency score from 0 to 1 (0 being not urgent, 1 being extremely urgent)
                        
                        Return your response as a JSON object.
                        """,
                    },
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
            )

            result = response.choices[0].message.content
            
            # Parse the JSON string response
            parsed_response = json.loads(result)
            
            # Extract and validate values
            query_type_str = parsed_response.get("type", "other").lower()
            extracted_info = parsed_response.get("extracted_info", {})
            urgency_score = float(parsed_response.get("urgency_score", 0.0))
            
            # Ensure urgency is between 0 and 1
            urgency_score = max(0.0, min(1.0, urgency_score))
            
            # Map to QueryType enum
            try:
                query_type = QueryType(query_type_str)
            except ValueError:
                logger.warning(f"Unknown query type: {query_type_str}, defaulting to OTHER")
                query_type = QueryType.OTHER
                
            return query_type, extracted_info, urgency_score
            
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return QueryType.OTHER, {}, 0.0

    def generate_initial_response(
        self, query: str, query_type: QueryType, extracted_info: Dict
    ) -> Tuple[str, ResponseType]:
        """
        Generate an initial response to the user's query.
        
        Args:
            query: The user's message text
            query_type: The classified type of query
            extracted_info: Extracted information about the query
            
        Returns:
            Tuple containing:
            - str: The response message
            - ResponseType: The type of response
        """
        try:
            # Generate a system prompt based on query type
            system_prompt = self._get_system_prompt_for_query_type(query_type)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.7,
            )

            result = response.choices[0].message.content
            
            # Determine response type based on content
            response_type = self._classify_response_type(result, query_type)
            
            return result, response_type
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return (
                "I'm having trouble processing your request. Let me connect you with a support specialist.",
                ResponseType.ESCALATE_TO_HUMAN,
            )

    def _get_system_prompt_for_query_type(self, query_type: QueryType) -> str:
        """Get appropriate system prompt based on query type."""
        if query_type == QueryType.URGENT_ISSUE:
            return """
            You are a helpful support assistant. The user has an urgent issue.
            Ask for any critical information needed (screenshots, error messages, etc.) and inform them
            that you're escalating this to a support specialist who will assist them shortly.
            Be empathetic and professional.
            """
        elif query_type == QueryType.TECHNICAL_ISSUE:
            return """
            You are a helpful support assistant. The user has a technical issue.
            Ask for any necessary details like screenshots, what system they're using, error messages, 
            and steps to reproduce the issue. Provide guidance if you have enough information to help.
            If not, inform them you need more details.
            """
        elif query_type == QueryType.ACCESS_REQUEST:
            return """
            You are a helpful support assistant. The user has an access request.
            Ask for necessary details like which system they need access to, 
            their job role/purpose, and any relevant deadlines.
            Let them know their request will be processed accordingly.
            """
        else:
            return """
            You are a helpful support assistant. Respond to the user's query professionally and empathetically.
            If you don't have enough information, ask clarifying questions.
            If it seems like a complex issue, mention that you can escalate to a specialist if needed.
            """

    def _classify_response_type(self, response: str, query_type: QueryType) -> ResponseType:
        """Classify the response type based on content and query type."""
        # For urgent issues, always escalate
        if query_type == QueryType.URGENT_ISSUE:
            return ResponseType.ESCALATE_TO_HUMAN
            
        # Check if response is asking for more information
        more_info_indicators = [
            "could you provide", "could you share", "can you tell me more",
            "would you mind sharing", "i need more information", "can you provide",
            "please share", "screenshot", "more details", "additional context"
        ]
        if any(indicator in response.lower() for indicator in more_info_indicators):
            return ResponseType.REQUEST_MORE_INFO
            
        # Check if response is escalating to human
        escalate_indicators = [
            "specialist", "team member", "escalate", "connect you with", 
            "have someone", "human agent", "support team"
        ]
        if any(indicator in response.lower() for indicator in escalate_indicators):
            return ResponseType.ESCALATE_TO_HUMAN
            
        # Default to direct answer
        return ResponseType.DIRECT_ANSWER 