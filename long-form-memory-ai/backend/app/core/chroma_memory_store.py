import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

from app.config import settings as app_settings


class ChromaMemoryStore:
    """
    Manages vector storage and retrieval of memories using ChromaDB.
    Handles memory conflicts, recency weighting, and preference updates.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client and embedding model."""
        self.embedder = SentenceTransformer(app_settings.EMBEDDING_MODEL)
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Create or get collections per user (we'll use one collection with user_id metadata)
        self.collection_name = "user_memories"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
    
    def _generate_memory_id(self, user_id: str, memory_type: str, key: str) -> str:
        """
        Generate a consistent ID for a memory based on user_id, type, and key.
        This allows us to update/replace existing memories with the same key.
        """
        return f"{user_id}_{memory_type}_{key}".replace(" ", "_")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        embedding = self.embedder.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def store_memory(
        self,
        user_id: str,
        memory_type: str,
        key: str,
        value: str,
        conversation_id: str,
        turn_number: int,
        confidence: float = 0.5,
        importance: float = 0.5,
        context: str = "",
        db_memory_id: str = None
    ) -> Dict[str, Any]:
        """
        Store a new memory or UPDATE an existing one if the same key exists.
        This handles preference changes like "Spanish" -> "English".
        """
        
        # Generate consistent memory ID for deduplication
        memory_id = self._generate_memory_id(user_id, memory_type, key)
        
        # Create embedding text
        embedding_text = f"{memory_type}: {key} - {value}"
        embedding = self._get_embedding(embedding_text)
        
        # Check if memory with same key already exists
        try:
            existing = self.collection.get(
                ids=[memory_id],
                include=["metadatas"]
            )
            
            if existing and existing['ids']:
                print(f"\n🔄 UPDATING EXISTING MEMORY: {memory_id}")
                print(f"   Old value: {existing['metadatas'][0].get('value')}")
                print(f"   New value: {value}")
                
                # Mark old memory as superseded by updating metadata
                old_metadata = existing['metadatas'][0]
                old_metadata['superseded_by'] = memory_id
                old_metadata['superseded_at'] = datetime.utcnow().isoformat()
                old_metadata['is_active'] = False
        except Exception as e:
            print(f"No existing memory found for {memory_id}: {e}")
        
        # Store/Update the memory in ChromaDB
        metadata = {
            "user_id": user_id,
            "memory_type": memory_type,
            "key": key,
            "value": value,
            "context": context,
            "conversation_id": conversation_id,
            "turn_number": turn_number,
            "confidence": confidence,
            "importance": importance,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "db_memory_id": db_memory_id or str(uuid.uuid4()),
            "access_count": 0
        }
        
        # Upsert (insert or update)
        self.collection.upsert(
            ids=[memory_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[embedding_text]
        )
        
        print(f"✅ Stored memory in ChromaDB: {memory_id}")
        
        return {
            "chroma_id": memory_id,
            "db_memory_id": metadata["db_memory_id"],
            "metadata": metadata
        }
    
    def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        current_turn: int,
        top_k: int = 10,
        memory_types: Optional[List[str]] = None,
        include_context: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories using semantic search with recency weighting.
        Only returns ACTIVE (non-superseded) memories.
        """
        
        # Generate query embedding
        query_embedding = self._get_embedding(query)
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k * 3, 100),  # Get more results for filtering
            where={
                "user_id": user_id,
                "is_active": True  # Only active memories
            },
            include=["metadatas", "documents", "distances"]
        )
        
        if not results or not results['ids'] or not results['ids'][0]:
            return []
        
        memories = []
        
        for i, mem_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            distance = results['distances'][0][i]
            
            # Filter by memory type if specified
            if memory_types and metadata['memory_type'] not in memory_types:
                continue
            
            # Calculate similarity score (ChromaDB returns distance, lower is better)
            # For cosine distance: similarity = 1 - distance
            similarity = 1 - distance
            
            # Calculate recency boost
            turn_diff = current_turn - metadata.get('turn_number', 0)
            recency_boost = 0.2 * np.exp(-turn_diff / 50.0)  # Decay over 50 turns
            
            # Calculate importance boost
            importance_boost = metadata.get('importance', 0.5) * 0.15
            
            # Final score = similarity + recency + importance
            final_score = similarity + recency_boost + importance_boost
            
            memories.append({
                'chroma_id': mem_id,
                'db_memory_id': metadata.get('db_memory_id'),
                'memory_type': metadata['memory_type'],
                'key': metadata['key'],
                'value': metadata['value'],
                'context': metadata.get('context', '') if include_context else '',
                'document': document,
                'similarity': similarity,
                'recency_boost': recency_boost,
                'importance_boost': importance_boost,
                'final_score': final_score,
                'turn_number': metadata.get('turn_number', 0),
                'confidence': metadata.get('confidence', 0.5),
                'importance': metadata.get('importance', 0.5),
                'created_at': metadata.get('created_at')
            })
        
        # Sort by final score (descending)
        memories.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Return top_k
        return memories[:top_k]
    
    def get_all_active_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        sort_by: str = "importance"  # "importance", "recency", or "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Get all active memories for a user, sorted by specified criterion.
        """
        
        where_filter = {
            "user_id": user_id,
            "is_active": True
        }
        
        if memory_type:
            where_filter["memory_type"] = memory_type
        
        try:
            results = self.collection.get(
                where=where_filter,
                include=["metadatas", "documents"]
            )
            
            if not results or not results['ids']:
                return []
            
            memories = []
            for i, mem_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                memories.append({
                    'chroma_id': mem_id,
                    'db_memory_id': metadata.get('db_memory_id'),
                    'memory_type': metadata['memory_type'],
                    'key': metadata['key'],
                    'value': metadata['value'],
                    'context': metadata.get('context', ''),
                    'turn_number': metadata.get('turn_number', 0),
                    'confidence': metadata.get('confidence', 0.5),
                    'importance': metadata.get('importance', 0.5),
                    'created_at': metadata.get('created_at')
                })
            
            # Sort based on criterion
            if sort_by == "importance":
                memories.sort(key=lambda x: x['importance'], reverse=True)
            elif sort_by == "recency":
                memories.sort(key=lambda x: x['turn_number'], reverse=True)
            
            return memories
            
        except Exception as e:
            print(f"Error retrieving memories: {e}")
            return []
    
    def deactivate_memory(self, chroma_id: str) -> bool:
        """
        Soft delete a memory by marking it as inactive.
        """
        try:
            # Get existing memory
            existing = self.collection.get(
                ids=[chroma_id],
                include=["metadatas", "embeddings", "documents"]
            )
            
            if not existing or not existing['ids']:
                return False
            
            # Update metadata to mark as inactive
            metadata = existing['metadatas'][0]
            metadata['is_active'] = False
            metadata['deactivated_at'] = datetime.utcnow().isoformat()
            
            # Update in ChromaDB
            self.collection.update(
                ids=[chroma_id],
                metadatas=[metadata]
            )
            
            return True
            
        except Exception as e:
            print(f"Error deactivating memory: {e}")
            return False
    
    def update_memory_access(self, chroma_id: str) -> bool:
        """
        Update access count for a memory when it's used.
        """
        try:
            existing = self.collection.get(
                ids=[chroma_id],
                include=["metadatas"]
            )
            
            if not existing or not existing['ids']:
                return False
            
            metadata = existing['metadatas'][0]
            metadata['access_count'] = metadata.get('access_count', 0) + 1
            metadata['last_accessed_at'] = datetime.utcnow().isoformat()
            
            self.collection.update(
                ids=[chroma_id],
                metadatas=[metadata]
            )
            
            return True
            
        except Exception as e:
            print(f"Error updating memory access: {e}")
            return False
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user's memories.
        """
        memories = self.get_all_active_memories(user_id)
        
        stats = {
            "total_memories": len(memories),
            "by_type": {},
            "high_importance_count": 0,
            "recent_memories": 0
        }
        
        for mem in memories:
            mem_type = mem['memory_type']
            stats["by_type"][mem_type] = stats["by_type"].get(mem_type, 0) + 1
            
            if mem['importance'] >= 0.8:
                stats["high_importance_count"] += 1
        
        return stats
