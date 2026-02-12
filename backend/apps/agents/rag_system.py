"""
RAG (Retrieval-Augmented Generation) System for Travel Knowledge
Uses ChromaDB for vector storage and retrieval
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class TravelKnowledgeBase:
    """
    Vector database for travel knowledge using ChromaDB.
    Stores and retrieves information about destinations, tips, reviews, etc.
    """

    def __init__(
        self,
        collection_name: str = "travel_knowledge",
        persist_directory: Optional[str] = None
    ):
        """
        Initialize the travel knowledge base.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
        """
        if persist_directory is None:
            persist_directory = str(Path(settings.BASE_DIR) / 'data' / 'chromadb')

        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_api_key,
                model_name="text-embedding-3-small"
            )
        else:
            # Fallback to default sentence transformer
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"description": "Travel knowledge and recommendations"}
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        logger.info(f"Initialized ChromaDB collection: {collection_name}")

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to the knowledge base.

        Args:
            texts: List of text documents to add
            metadatas: Optional metadata for each document
            ids: Optional IDs for documents (generated if not provided)
        """
        try:
            if not texts:
                logger.warning("No texts provided to add_documents")
                return

            # Generate IDs if not provided
            if ids is None:
                import hashlib
                ids = [
                    hashlib.md5(text.encode()).hexdigest()
                    for text in texts
                ]

            # Add documents to collection
            self.collection.add(
                documents=texts,
                metadatas=metadatas or [{} for _ in texts],
                ids=ids
            )

            logger.info(f"Added {len(texts)} documents to knowledge base")

        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    def add_destination_guide(
        self,
        destination: str,
        country: str,
        content: str,
        category: str = "general",
        source: str = "manual"
    ) -> None:
        """
        Add a destination guide to the knowledge base.

        Args:
            destination: City or destination name
            country: Country name
            content: Guide content
            category: Category (e.g., 'attractions', 'food', 'culture')
            source: Source of information
        """
        try:
            # Split content into chunks
            chunks = self.text_splitter.split_text(content)

            # Create metadata for each chunk
            metadatas = [
                {
                    'destination': destination,
                    'country': country,
                    'category': category,
                    'source': source,
                    'chunk_index': i
                }
                for i in range(len(chunks))
            ]

            # Generate IDs
            import hashlib
            base_id = f"{destination}_{country}_{category}_{source}"
            ids = [
                hashlib.md5(f"{base_id}_{i}".encode()).hexdigest()
                for i in range(len(chunks))
            ]

            self.add_documents(chunks, metadatas, ids)

        except Exception as e:
            logger.error(f"Error adding destination guide: {str(e)}")
            raise

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the knowledge base.

        Args:
            query_text: Query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            Dictionary with query results
        """
        try:
            # Query collection
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_metadata
            )

            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'total_results': len(results['documents'][0]) if results['documents'] else 0
            }

        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}")
            return {
                'documents': [],
                'metadatas': [],
                'distances': [],
                'total_results': 0
            }

    def get_destination_context(
        self,
        destination: str,
        query: str,
        n_results: int = 3
    ) -> str:
        """
        Get relevant context about a destination for a specific query.

        Args:
            destination: Destination name
            query: Specific query about the destination
            n_results: Number of context chunks to retrieve

        Returns:
            Concatenated context string
        """
        try:
            # Build full query
            full_query = f"{destination}: {query}"

            # Query with destination filter
            results = self.query(
                query_text=full_query,
                n_results=n_results,
                filter_metadata={"destination": destination}
            )

            # Concatenate results
            context = "\n\n".join(results['documents'])

            return context if context else "No specific information available."

        except Exception as e:
            logger.error(f"Error getting destination context: {str(e)}")
            return "No specific information available."

    def delete_collection(self) -> None:
        """Delete the entire collection"""
        try:
            self.client.delete_collection(self.collection.name)
            logger.info(f"Deleted collection: {self.collection.name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                'name': self.collection.name,
                'total_documents': count,
                'embedding_function': str(self.collection._embedding_function)
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}


class RAGPipeline:
    """
    Complete RAG pipeline for enhancing agent responses with retrieved knowledge.
    """

    def __init__(
        self,
        knowledge_base: Optional[TravelKnowledgeBase] = None,
        model_name: str = "gpt-4"
    ):
        """
        Initialize RAG pipeline.

        Args:
            knowledge_base: TravelKnowledgeBase instance
            model_name: LLM model to use
        """
        self.knowledge_base = knowledge_base or TravelKnowledgeBase()
        self.llm = ChatOpenAI(model_name=model_name, temperature=0.7)

        # Define RAG prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a knowledgeable travel assistant. Use the following context to answer the question.
If you don't know the answer based on the context, say so and provide general travel advice.

Context:
{context}

Question: {question}

Detailed Answer:"""
        )

    def generate_response(
        self,
        query: str,
        destination: Optional[str] = None,
        n_context_docs: int = 3
    ) -> Dict[str, Any]:
        """
        Generate response using RAG pipeline.

        Args:
            query: User query
            destination: Optional destination filter
            n_context_docs: Number of context documents to retrieve

        Returns:
            Dictionary with answer and sources
        """
        try:
            # Retrieve relevant context
            if destination:
                context = self.knowledge_base.get_destination_context(
                    destination=destination,
                    query=query,
                    n_results=n_context_docs
                )
                filter_metadata = {"destination": destination}
            else:
                results = self.knowledge_base.query(
                    query_text=query,
                    n_results=n_context_docs
                )
                context = "\n\n".join(results['documents'])
                filter_metadata = None

            # Generate response using LLM
            prompt = self.prompt_template.format(context=context, question=query)

            from langchain.schema import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])

            # Get sources
            sources = self.knowledge_base.query(
                query_text=query,
                n_results=n_context_docs,
                filter_metadata=filter_metadata
            )

            return {
                'answer': response.content,
                'context': context,
                'sources': sources['metadatas'],
                'confidence': 'high' if sources['total_results'] > 0 else 'low'
            }

        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return {
                'answer': f"Error generating response: {str(e)}",
                'context': '',
                'sources': [],
                'confidence': 'low'
            }

    def enhance_agent_prompt(
        self,
        base_prompt: str,
        destination: str,
        query_type: str = "general"
    ) -> str:
        """
        Enhance an agent prompt with retrieved context.

        Args:
            base_prompt: Original agent prompt
            destination: Destination being queried
            query_type: Type of information needed

        Returns:
            Enhanced prompt with context
        """
        try:
            # Retrieve relevant context
            context = self.knowledge_base.get_destination_context(
                destination=destination,
                query=query_type,
                n_results=2
            )

            # Enhance prompt
            enhanced_prompt = f"""{base_prompt}

Additional Context from Knowledge Base:
{context}

Please incorporate this context into your response where relevant.
"""

            return enhanced_prompt

        except Exception as e:
            logger.error(f"Error enhancing prompt: {str(e)}")
            return base_prompt


class KnowledgeBaseSeeder:
    """Utility to seed the knowledge base with initial travel data"""

    def __init__(self, knowledge_base: TravelKnowledgeBase):
        self.knowledge_base = knowledge_base

    def seed_sample_destinations(self) -> None:
        """Seed knowledge base with sample destination data"""
        try:
            sample_data = [
                {
                    'destination': 'Paris',
                    'country': 'France',
                    'category': 'attractions',
                    'content': """
                    Paris, the City of Light, is home to iconic landmarks including the Eiffel Tower,
                    Louvre Museum, and Notre-Dame Cathedral. The Eiffel Tower offers stunning views
                    of the city, especially at sunset. The Louvre houses thousands of artworks including
                    the Mona Lisa. Montmartre offers a charming village atmosphere with the Sacré-Cœur
                    basilica. The Champs-Élysées is perfect for shopping and dining. Consider visiting
                    the Palace of Versailles for a day trip outside the city.
                    """
                },
                {
                    'destination': 'Paris',
                    'country': 'France',
                    'category': 'food',
                    'content': """
                    Paris is a culinary paradise. Must-try dishes include croissants from local boulangeries,
                    escargot, coq au vin, and crème brûlée. The Latin Quarter has excellent bistros.
                    Le Marais is known for falafel and Jewish bakeries. For fine dining, reserve at
                    Michelin-starred restaurants well in advance. Café culture is essential - enjoy
                    coffee and people-watching at sidewalk cafés. Visit farmers markets for fresh produce
                    and cheese. Don't miss French wine and champagne.
                    """
                },
                {
                    'destination': 'Tokyo',
                    'country': 'Japan',
                    'category': 'culture',
                    'content': """
                    Tokyo blends ancient traditions with modern innovation. Visit Senso-ji Temple in Asakusa
                    for traditional architecture. Shibuya Crossing showcases modern Tokyo's energy.
                    Harajuku offers youth fashion culture. Experience a traditional tea ceremony.
                    Stay in a ryokan for authentic Japanese hospitality. Remove shoes when entering homes
                    and some restaurants. Bowing is a respectful greeting. The city is incredibly safe
                    and clean. Public transportation is efficient but can be crowded during rush hour.
                    """
                },
                {
                    'destination': 'New York',
                    'country': 'USA',
                    'category': 'attractions',
                    'content': """
                    New York City offers world-class attractions. Central Park provides green space in
                    Manhattan. The Statue of Liberty and Ellis Island tell immigrant stories. Times Square
                    dazzles with lights and energy. The Metropolitan Museum of Art houses incredible
                    collections. Brooklyn Bridge offers iconic views. Visit the 9/11 Memorial and Museum.
                    Take in Broadway shows. Explore diverse neighborhoods like Greenwich Village, SoHo,
                    and Williamsburg. The High Line is an elevated park with art and gardens.
                    """
                },
            ]

            for data in sample_data:
                self.knowledge_base.add_destination_guide(**data)

            logger.info("Successfully seeded knowledge base with sample data")

        except Exception as e:
            logger.error(f"Error seeding knowledge base: {str(e)}")

    def seed_from_file(self, file_path: str) -> None:
        """Seed knowledge base from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            for entry in data:
                self.knowledge_base.add_destination_guide(**entry)

            logger.info(f"Successfully seeded knowledge base from {file_path}")

        except Exception as e:
            logger.error(f"Error seeding from file: {str(e)}")


# Global instances
_knowledge_base = None
_rag_pipeline = None


def get_knowledge_base() -> TravelKnowledgeBase:
    """Get or create global knowledge base instance"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = TravelKnowledgeBase()
    return _knowledge_base


def get_rag_pipeline() -> RAGPipeline:
    """Get or create global RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline(knowledge_base=get_knowledge_base())
    return _rag_pipeline
