"""
Embedding generation for semantic similarity and vector search.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch


class EmbeddingGenerator:
    """
    Generates embeddings for text content to enable semantic search and similarity matching.
    Uses sentence-transformers for high-quality embeddings.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Model configuration
        self.model_name = config.get("model", "all-MiniLM-L6-v2")
        self.device = config.get("device", "cpu")
        self.batch_size = config.get("batch_size", 32)
        self.max_seq_length = config.get("max_seq_length", 512)
        
        # Model instance
        self.model = None
        self.embedding_dimension = None
        
    async def initialize(self):
        """Initialize the embedding model."""
        try:
            # Load the sentence transformer model
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.model.max_seq_length = self.max_seq_length
            
            # Get embedding dimension
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            
            self.logger.info(f"Embedding model '{self.model_name}' loaded successfully")
            self.logger.info(f"Embedding dimension: {self.embedding_dimension}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            # Preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Generate embedding
            embedding = self.model.encode([cleaned_text], convert_to_tensor=False)[0]
            
            # Convert to list and normalize
            embedding_list = embedding.tolist()
            normalized_embedding = self._normalize_embedding(embedding_list)
            
            return normalized_embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently."""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            # Preprocess texts
            cleaned_texts = [self._preprocess_text(text) for text in texts]
            
            # Generate embeddings in batches
            all_embeddings = []
            
            for i in range(0, len(cleaned_texts), self.batch_size):
                batch = cleaned_texts[i:i + self.batch_size]
                embeddings = self.model.encode(batch, convert_to_tensor=False)
                
                # Convert to lists and normalize
                for embedding in embeddings:
                    embedding_list = embedding.tolist()
                    normalized_embedding = self._normalize_embedding(embedding_list)
                    all_embeddings.append(normalized_embedding)
            
            return all_embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before embedding generation."""
        if not text:
            return ""
        
        # Clean and truncate text
        cleaned = text.strip()
        
        # Truncate if too long (rough character estimate)
        if len(cleaned) > self.max_seq_length * 4:  # Rough token-to-char ratio
            cleaned = cleaned[:self.max_seq_length * 4]
        
        return cleaned
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding vector for consistent similarity calculations."""
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        
        if norm == 0:
            return embedding
        
        normalized = embedding_array / norm
        return normalized.tolist()
    
    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    async def find_most_similar(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]],
        threshold: float = 0.7
    ) -> List[tuple]:
        """
        Find most similar embeddings from candidates.
        Returns list of (index, similarity_score) tuples.
        """
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = await self.compute_similarity(query_embedding, candidate)
            if similarity >= threshold:
                similarities.append((i, similarity))
        
        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings generated by this model."""
        return self.embedding_dimension
