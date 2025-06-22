import os
from typing import List, Dict, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import openai
from fast_graphrag import GraphRAG
from app.config import settings
import logging

logger = logging.getLogger(__name__)

os.environ['OPENAI_API_KEY'] = settings.openai_api_key

DOMAIN = """
Analyze documents from Next Step Foundation, a disability inclusion and employment organization in Kenya. 
Focus on identifying beneficiaries, programs, partnerships, outcomes, challenges, geographic locations, 
funding sources, methodologies, and impact metrics. Extract information about their R.A.A.T.T. method 
(Recruit, Assess, Accommodate, Train, Transition), AI training programs, mental health initiatives like 
Upili, employment partnerships, and work with Persons with Disabilities, Women, and Youth in Africa.
"""

EXAMPLE_QUERIES = [
    "What is the R.A.A.T.T. method and how is it implemented across programs?",
    "What are the key outcomes and impact metrics from the Upili mental health program?",
    "Which organizations has Next Step Foundation partnered with for employment placement?",
    "What are the main barriers to employment for Persons with Disabilities identified in their work?",
    "How has AI training contributed to job placement rates?",
    "What geographic regions in Kenya has NSF operated in and what were the outcomes?",
    "What funding sources and grant amounts have supported different programs?",
    "How do impact reports show progression from training to employment?",
    "What accommodations and assistive technologies are mentioned across documents?",
    "What are the key learnings and recommendations from failed or challenging initiatives?",
    "How does NSF measure success and what are their key performance indicators?",
    "What partnerships exist with international organizations vs local Kenyan entities?",
    "How do concept notes evolve into implemented programs based on documentation?",
    "What mental health interventions have been most effective according to reports?",
    "How does the foundation address intersectionality (disability + gender + youth)?"
]

ENTITY_TYPES = [
    "Person", "Organization", "Program", "Location", "Skill", "Technology",
    "Outcome", "Challenge", "Method", "Metric", "Funding", "Accommodation",
    "Disability", "Employer", "Event"
]


class GraphRAGService:
    def __init__(self):
        self.grag = None
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self._initialize()

    def _initialize(self):
        self.grag = GraphRAG(
            working_dir=settings.graphrag_working_dir,
            domain=DOMAIN,
            example_queries=EXAMPLE_QUERIES,
            entity_types=ENTITY_TYPES
        )

    def _preprocess_message(self, message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        if not conversation_history:
            return message

        history_context = ""
        for msg in conversation_history[-3:]:
            history_context += f"User: {msg['user_message']}\nAssistant: {msg['ai_response']}\n"

        prompt = f"""Given the conversation history and current user message, return the current message as-is if it's standalone and clear. If it references previous context or is unclear without history, rephrase it to be a complete, standalone question.

Conversation History:
{history_context}

Current Message: {message}

Return only the standalone version of the message:"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return response.choices[0].message.content.strip()

    def query(self, question: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        if not self.grag:
            self._initialize()

        processed_question = self._preprocess_message(question, conversation_history)
        response = self.grag.query(processed_question)
        return response.response

    async def query_async(self, question: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    self._run_graphrag_query,
                    question,
                    conversation_history
                )
            return result
        except Exception as e:
            logger.error(f"Error in GraphRAG query: {str(e)}")
            return f"I apologize, but I encountered an error while processing your question. Please try again."

    def _run_graphrag_query(self, question: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        try:
            if not self.grag:
                self._initialize()

            processed_question = self._preprocess_message(question, conversation_history)
            response = self.grag.query(processed_question)
            return response.response
        except Exception as e:
            logger.error(f"GraphRAG query failed: {str(e)}")
            return "I apologize, but I'm unable to process your request at the moment. Please try again later."

    def add_document(self, content: str):
        if not self.grag:
            self._initialize()
        self.grag.insert(content)


graphrag_service = GraphRAGService()