"""
Main LLM orchestration service for Cashie financial chatbot.
"""
import json
import logging
import time
from typing import Dict, Any, Optional, List

from django.conf import settings

from ..models import ChatSession, ChatMessage
from .context_builder import ContextBuilder

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Cashie, a friendly and financially savvy AI assistant for the Bamboo Money personal finance app. You help users understand their spending, budgets, and financial habits.

PERSONALITY:
- Friendly, supportive, and encouraging
- Knowledgeable about personal finance
- Concise but thorough when explaining financial concepts
- Never judgmental about spending habits

RULES:
1. ONLY use the financial data provided in the context below - never make up numbers
2. If asked about data you don't have, honestly say you don't have that information
3. When discussing spending, always reference actual transaction data
4. Provide actionable insights and suggestions when appropriate
5. If the user asks something unrelated to finance, gently redirect to financial topics

RESPONSE FORMAT:
You must respond with valid JSON in this exact format:
{{
    "message": "Your conversational response to the user",
    "visualization": null or {{
        "type": "pie_chart|bar_chart|line_chart|table",
        "title": "Chart title",
        "data": {{}}
    }},
    "suggested_questions": ["Question 1?", "Question 2?", "Question 3?"]
}}

For visualizations:
- pie_chart: {{"labels": ["A", "B"], "values": [10, 20], "colors": ["#hex1", "#hex2"]}}
- bar_chart: {{"labels": ["A", "B"], "values": [10, 20], "color": "#hex"}}
- table: {{"headers": ["Col1", "Col2"], "rows": [["val1", "val2"]]}}

Only include visualization when the data lends itself to visual representation (spending breakdowns, comparisons, trends).

Suggested questions should be relevant follow-ups the user might want to ask.

USER'S FINANCIAL DATA:
{context}
"""


class CashieService:
    """Main service for Cashie chatbot LLM orchestration."""

    def __init__(self, user):
        self.user = user
        self.api_key = getattr(settings, 'OPENAI_API_KEY', '')
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI package not installed")

    def get_or_create_session(self, session_id: Optional[str] = None) -> ChatSession:
        """Get existing session or create a new one."""
        if session_id:
            try:
                return ChatSession.objects.get(id=session_id, user=self.user)
            except ChatSession.DoesNotExist:
                pass

        return ChatSession.objects.create(user=self.user)

    def send_message(
        self,
        session: ChatSession,
        user_message: str
    ) -> ChatMessage:
        """
        Send a message and get Cashie's response.

        Returns the assistant's ChatMessage.
        """
        start_time = time.time()

        # Save user message
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=user_message
        )

        # Build financial context
        context_builder = ContextBuilder(self.user)
        context_string = context_builder.build_context_string()

        # Get conversation history
        history = self._get_conversation_history(session)

        # Call LLM
        response_data = self._call_llm(context_string, history, user_message)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Create assistant message
        assistant_message = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=response_data['message'],
            visualization_type=response_data.get('visualization', {}).get('type', '') if response_data.get('visualization') else '',
            visualization_data=response_data.get('visualization'),
            suggested_questions=response_data.get('suggested_questions'),
            processing_time_ms=processing_time_ms
        )

        # Update session title if this is the first exchange
        if session.messages.count() == 2:  # User + Assistant
            self._update_session_title(session, user_message)

        session.save()  # Update updated_at timestamp

        return assistant_message

    def _get_conversation_history(self, session: ChatSession) -> List[Dict[str, str]]:
        """Get conversation history for context."""
        messages = session.messages.order_by('created_at')[:20]  # Limit to last 20 messages
        return [
            {'role': msg.role, 'content': msg.content}
            for msg in messages
        ]

    def _call_llm(
        self,
        context: str,
        history: List[Dict[str, str]],
        user_message: str
    ) -> Dict[str, Any]:
        """Call the OpenAI API and parse the response."""
        if not self.client:
            return self._fallback_response(user_message)

        try:
            # Build messages
            messages = [
                {
                    'role': 'system',
                    'content': SYSTEM_PROMPT.format(context=context)
                }
            ]

            # Add conversation history
            for msg in history:
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })

            # Add current user message
            messages.append({
                'role': 'user',
                'content': user_message
            })

            # Call API
            response = self.client.chat.completions.create(
                model='gpt-4o',
                messages=messages,
                temperature=0.7,
                response_format={'type': 'json_object'}
            )

            # Parse response
            content = response.choices[0].message.content
            return self._parse_response(content)

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return self._fallback_response(user_message)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        try:
            data = json.loads(content)

            # Validate required fields
            if 'message' not in data:
                data['message'] = "I'm sorry, I had trouble processing that. Could you try rephrasing?"

            # Ensure suggested_questions is a list
            if not isinstance(data.get('suggested_questions'), list):
                data['suggested_questions'] = []

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                'message': content if content else "I'm having trouble responding right now. Please try again.",
                'visualization': None,
                'suggested_questions': []
            }

    def _fallback_response(self, user_message: str) -> Dict[str, Any]:
        """Provide a fallback response when LLM is unavailable."""
        return {
            'message': (
                "I'm sorry, I'm having trouble connecting to my AI backend right now. "
                "Please check that the OpenAI API key is configured and try again. "
                "In the meantime, you can explore your spending data in the Dashboard and Transactions pages."
            ),
            'visualization': None,
            'suggested_questions': [
                "How much did I spend this month?",
                "What's my biggest spending category?",
                "Am I on track with my budgets?"
            ]
        }

    def _update_session_title(self, session: ChatSession, first_message: str) -> None:
        """Generate a title for the session based on the first message."""
        # Simple title: first 50 chars of the message
        title = first_message[:47] + '...' if len(first_message) > 50 else first_message
        session.title = title
        session.save(update_fields=['title'])

    def get_welcome_suggestions(self) -> List[str]:
        """Get suggested questions for a new conversation."""
        context_builder = ContextBuilder(self.user)
        context = context_builder.build_context()

        suggestions = [
            "How much have I spent this month?",
            "What's my biggest spending category?",
        ]

        # Add contextual suggestions
        budgets = context['budget_status']
        if budgets:
            over_budget = [b for b in budgets if b['spent'] > b['limit']]
            if over_budget:
                suggestions.append("Which budgets am I over on?")
            else:
                suggestions.append("Am I on track with my budgets?")

        if context['unread_alerts']:
            suggestions.append("What alerts do I have?")

        if context['summary_stats']['transaction_count'] > 0:
            suggestions.append("Show me my recent transactions")

        return suggestions[:4]  # Return at most 4 suggestions
