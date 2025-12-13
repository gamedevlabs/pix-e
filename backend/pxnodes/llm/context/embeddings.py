"""
OpenAI Embedding Generation for Structural Memory.

Generates embeddings for Knowledge Triples and Atomic Facts
for vector similarity search.
"""

import logging
from typing import Optional

import logfire
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIEmbeddingGenerator:
    """Generate embeddings using OpenAI's embedding API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
    ):
        """
        Initialize embedding generator.

        Args:
            model: OpenAI embedding model to use
                - text-embedding-3-small (1536 dims, cost-effective)
                - text-embedding-3-large (3072 dims, higher quality)
            api_key: Optional API key (uses OPENAI_API_KEY env var if not provided)
        """
        self.model = model
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        
        # Determine embedding dimensions based on model
        self.dimensions = 3072 if "large" in model else 1536
        
        logger.info(
            f"Initialized OpenAI embedding generator with model: {model} "
            f"({self.dimensions} dimensions)"
        )

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        with logfire.span(
            "openai.generate_embedding",
            model=self.model,
            text_length=len(text),
        ):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text,
                )
                
                embedding = response.data[0].embedding
                
                logfire.info(
                    "embedding_generated",
                    model=self.model,
                    dimensions=len(embedding),
                    text_preview=text[:100],
                )
                
                return embedding
                
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
                logfire.error(
                    "embedding_generation_failed",
                    error=str(e),
                    model=self.model,
                    text_preview=text[:100],
                )
                raise

    def generate_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch (max 2048 for OpenAI)

        Returns:
            List of embeddings
        """
        with logfire.span(
            "openai.generate_embeddings_batch",
            model=self.model,
            total_texts=len(texts),
            batch_size=batch_size,
        ):
            all_embeddings: list[list[float]] = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                
                try:
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch,
                    )
                    
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                    
                    logfire.info(
                        "batch_embeddings_generated",
                        batch_num=i // batch_size + 1,
                        batch_size=len(batch),
                        model=self.model,
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to generate batch embeddings: {e}")
                    logfire.error(
                        "batch_embedding_failed",
                        error=str(e),
                        batch_num=i // batch_size + 1,
                        model=self.model,
                    )
                    raise
            
            return all_embeddings


# Convenience function for one-off embedding generation
def generate_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """
    Generate a single embedding (convenience function).

    Args:
        text: Text to embed
        model: OpenAI embedding model

    Returns:
        Embedding vector
    """
    generator = OpenAIEmbeddingGenerator(model=model)
    return generator.generate_embedding(text)

