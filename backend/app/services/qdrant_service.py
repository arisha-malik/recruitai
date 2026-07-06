import logging
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchText, Range

from app.config import settings
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class QdrantConfigurationError(Exception):
    """Raised when Qdrant service is improperly configured."""
    pass

class QdrantOperationError(Exception):
    """Raised when vector database operations fail."""
    pass

class QdrantService:
    def __init__(self):
        self._client = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        if settings.QDRANT_ENABLED:
            self.embedding_service = EmbeddingService()
            self._init_client()
        else:
            logger.info("Qdrant integration is disabled.")

    def _init_client(self):
        if not settings.QDRANT_ENABLED:
            return
        try:
            # If QDRANT_URL is set, use it. Otherwise construct from host & port
            url = settings.QDRANT_URL
            if url:
                self._client = QdrantClient(url=url, api_key=settings.QDRANT_API_KEY)
            else:
                self._client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY
                )
        except Exception as e:
            logger.warning(f"Could not initialize QdrantClient: {str(e)}. Vector operations will fail unless mocked.")

    def ensure_collection(self):
        """
        Check if collection exists; create it with appropriate dimensions if not.
        """
        if not self._client:
            raise QdrantConfigurationError("QdrantClient is not initialized.")
            
        try:
            # Check if collection exists
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                vector_size = self.embedding_service.get_embedding_dimension()
                logger.info(f"Creating Qdrant collection '{self.collection_name}' with dimension {vector_size}...")
                
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self.collection_name}' successfully created.")
        except Exception as e:
            logger.error(f"Error checking/creating Qdrant collection: {str(e)}")
            raise QdrantOperationError(f"Failed to ensure Qdrant collection: {str(e)}")

    def upsert_candidate_vector(
        self,
        candidate_id: str,
        resume_id: str,
        vector: List[float],
        skills: List[str],
        experience_years: float,
        location: str,
        current_company: str,
        domain: str = None
    ):
        """
        Upsert a candidate's vector and metadata payload into the Qdrant collection.
        If a vector point already exists for this candidate_id (as UUID string), it will be overwritten.
        """
        if not self._client:
            raise QdrantConfigurationError("QdrantClient is not initialized.")
            
        # Ensure collection exists before upserting
        self.ensure_collection()
        
        try:
            # We use candidate_id directly as the point ID since it's a UUID string
            # Qdrant accepts valid UUID strings as point IDs
            point = PointStruct(
                id=candidate_id,
                vector=vector,
                payload={
                    "candidate_id": candidate_id,
                    "resume_id": resume_id,
                    "skills": skills or [],
                    "total_experience_years": float(experience_years) if experience_years is not None else 0.0,
                    "location": location or "",
                    "current_company": current_company or "",
                    "domain": domain or "OTHER"
                }
            )
            
            self._client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Successfully upserted candidate vector for candidate_id: {candidate_id}")
        except Exception as e:
            logger.error(f"Failed to upsert candidate vector: {str(e)}")
            raise QdrantOperationError(f"Qdrant upsert failed: {str(e)}")

    def search_candidates_vectors(
        self,
        query_vector: List[float],
        top_n: int = 20,
        skills_filter: List[str] = None,
        location_filter: str = None,
        min_experience_years: float = None,
        domain_filter: str = None
    ) -> List[dict]:
        """
        Search the candidate collection in Qdrant using vector similarity (Cosine).
        Returns a list of dicts: [{"candidate_id": "...", "score": 0.89}, ...]
        """
        if not self._client:
            raise QdrantConfigurationError("QdrantClient is not initialized.")
            
        filter_conditions = []
        
        if domain_filter:
            filter_conditions.append(
                FieldCondition(
                    key="domain",
                    match=MatchValue(value=domain_filter)
                )
            )
            
        if skills_filter:
            for skill in skills_filter:
                filter_conditions.append(
                    FieldCondition(
                        key="skills",
                        match=MatchValue(value=skill)
                    )
                )
                
        if location_filter:
            filter_conditions.append(
                FieldCondition(
                    key="location",
                    match=MatchText(text=location_filter)
                )
            )
            
        if min_experience_years is not None:
            filter_conditions.append(
                FieldCondition(
                    key="total_experience_years",
                    range=Range(gte=float(min_experience_years))
                )
            )
            
        qdrant_filter = None
        if filter_conditions:
            qdrant_filter = Filter(must=filter_conditions)

        try:
            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_n
            )
            
            hits = []
            for hit in results:
                payload = hit.payload or {}
                hits.append({
                    "candidate_id": payload.get("candidate_id"),
                    "resume_id": payload.get("resume_id"),
                    "score": hit.score,
                    "skills": payload.get("skills"),
                    "location": payload.get("location"),
                    "current_company": payload.get("current_company"),
                    "total_experience_years": payload.get("total_experience_years")
                })
            return hits
        except Exception as e:
            logger.error(f"Qdrant search failed: {str(e)}")
            raise QdrantOperationError(f"Qdrant vector search failed: {str(e)}")
