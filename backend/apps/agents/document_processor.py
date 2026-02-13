"""
Document processing pipeline for RAG.
Extracts text from uploaded files (PDF, TXT, DOCX, MD, CSV),
chunks it, and indexes into ChromaDB for the AI assistant.
"""

import hashlib
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def extract_text(file_path: str, file_type: str) -> str:
    """
    Extract plain text from a file based on its type.

    Supports: pdf, txt, md, docx, csv
    """
    file_type = file_type.lower().strip('.')

    if file_type == 'pdf':
        return _extract_pdf(file_path)
    elif file_type in ('txt', 'md'):
        return _extract_text_file(file_path)
    elif file_type == 'docx':
        return _extract_docx(file_path)
    elif file_type == 'csv':
        return _extract_csv(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return '\n\n'.join(pages)
    except ImportError:
        logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
        raise
    except Exception as e:
        logger.error(f"Error extracting PDF: {e}")
        raise


def _extract_text_file(file_path: str) -> str:
    """Extract text from TXT or Markdown files."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def _extract_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n\n'.join(paragraphs)
    except ImportError:
        logger.error("python-docx not installed. Install with: pip install python-docx")
        raise
    except Exception as e:
        logger.error(f"Error extracting DOCX: {e}")
        raise


def _extract_csv(file_path: str) -> str:
    """Extract text from a CSV file by converting rows to readable text."""
    import csv
    rows = []
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        headers = None
        for i, row in enumerate(reader):
            if i == 0:
                headers = row
                continue
            if headers:
                row_text = ', '.join(
                    f"{h}: {v}" for h, v in zip(headers, row) if v.strip()
                )
            else:
                row_text = ', '.join(row)
            if row_text.strip():
                rows.append(row_text)
    return '\n'.join(rows)


def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[str]:
    """
    Split text into overlapping chunks for embedding.
    Uses paragraph/sentence boundaries when possible.
    """
    if not text or not text.strip():
        return []

    # Try to use LangChain's splitter if available
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_text(text)
    except ImportError:
        pass

    # Fallback: simple chunking
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - chunk_overlap
    return chunks


def process_and_index_document(document) -> int:
    """
    Process a RAGDocument: extract text, chunk it, and index into ChromaDB.

    Args:
        document: RAGDocument model instance

    Returns:
        Number of chunks indexed
    """
    from apps.agents.chat_rag import get_user_data_rag

    document.status = 'processing'
    document.save(update_fields=['status', 'updated_at'])

    try:
        # Get the file path
        file_path = document.file.path
        file_type = document.file_type or os.path.splitext(file_path)[1].lstrip('.')

        # Extract text
        text = extract_text(file_path, file_type)
        if not text or not text.strip():
            document.status = 'failed'
            document.error_message = 'No text could be extracted from the file.'
            document.save(update_fields=['status', 'error_message', 'updated_at'])
            return 0

        # Chunk the text
        chunks = chunk_text(text)
        if not chunks:
            document.status = 'failed'
            document.error_message = 'Text extracted but no chunks generated.'
            document.save(update_fields=['status', 'error_message', 'updated_at'])
            return 0

        # Index into ChromaDB
        rag = get_user_data_rag()

        # Delete any existing chunks for this document
        doc_id_prefix = f"doc_{document.id}"
        try:
            existing = rag.collection.get(
                where={"document_id": str(document.id)}
            )
            if existing and existing['ids']:
                rag.collection.delete(ids=existing['ids'])
        except Exception:
            pass

        # Prepare chunks for indexing
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(
                f"{doc_id_prefix}_{i}_{chunk[:50]}".encode()
            ).hexdigest()
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                'document_id': str(document.id),
                'document_title': document.title,
                'data_type': 'company_document',
                'scope': document.scope,
                'uploaded_by': str(document.uploaded_by_id),
                'file_type': file_type,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'indexed_at': datetime.utcnow().isoformat(),
                # For global docs, user_id is set to 'global' so all users can access
                'user_id': 'global' if document.scope == 'global' else str(document.uploaded_by_id),
            })

        # Add in batches
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            rag.collection.add(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
            )

        # Update document status
        document.status = 'indexed'
        document.chunk_count = len(chunks)
        document.error_message = ''
        document.save(update_fields=['status', 'chunk_count', 'error_message', 'updated_at'])

        logger.info(
            f"Document '{document.title}' (ID: {document.id}) indexed: "
            f"{len(chunks)} chunks from {file_type} file"
        )
        return len(chunks)

    except Exception as e:
        document.status = 'failed'
        document.error_message = str(e)[:500]
        document.save(update_fields=['status', 'error_message', 'updated_at'])
        logger.error(f"Error processing document {document.id}: {e}")
        return 0


def delete_document_chunks(document) -> int:
    """
    Delete all ChromaDB chunks for a document.

    Returns:
        Number of chunks deleted
    """
    from apps.agents.chat_rag import get_user_data_rag

    try:
        rag = get_user_data_rag()
        existing = rag.collection.get(
            where={"document_id": str(document.id)}
        )
        if existing and existing['ids']:
            count = len(existing['ids'])
            rag.collection.delete(ids=existing['ids'])
            logger.info(f"Deleted {count} chunks for document {document.id}")
            return count
        return 0
    except Exception as e:
        logger.error(f"Error deleting document chunks: {e}")
        return 0
