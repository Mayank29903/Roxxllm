import uuid
import pickle
import os
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
import faiss

from app.config import settings
from app.models.memory import Memory


class MemoryStore:
    """Manages vector storage and retrieval of memories using FAISS."""
    
    def __init__(self):
        self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.index = None
        self.memories = {}
        self.user_memories = {}  # Separate index per user
        self.index_file = "faiss_index.pkl"
        self._load_index()
    
    def _load_index(self):
        """Load or create FAISS index."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'rb') as f:
                    data = pickle.load(f)
                    self.user_memories = data.get('user_memories', {})
                    self.memories = data.get('memories', {})
            except Exception as e:
                print(f"Error loading index: {e}")
                self.user_memories = {}
                self.memories = {}
        else:
            self.user_memories = {}
            self.memories = {}
    
    def _save_index(self):
        """Save FAISS index to disk."""
        try:
            with open(self.index_file, 'wb') as f:
                pickle.dump({
                    'user_memories': self.user_memories,
                    'memories': self.memories
                }, f)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def _get_user_index(self, user_id: int):
        """Get or create FAISS index for a user."""
        user_key = str(user_id)
        if user_key not in self.user_memories:
            # Create new index: 384 dimensions (MiniLM), Inner Product (cosine similarity)
            index = faiss.IndexFlatIP(384)
            self.user_memories[user_key] = {
                'index': index,
                'id_map': {},  # Maps FAISS index position to memory data
                'next_id': 0
            }
        return self.user_memories[user_key]
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        embedding = self.embedder.encode(text, convert_to_numpy=True)
        # Normalize for cosine similarity
        faiss.normalize_L2(embedding.reshape(1, -1))
        return embedding.astype('float32')
    
    def store_memory(
        self,
        db: Session,
        user_id: int,
        memory_data: Dict[str, Any],
        conversation_id: int,
        turn_number: int
    ) -> Memory:
        """Store a new memory in both SQL and FAISS."""
        
        # Create SQL record first
        vector_id = str(uuid.uuid4())
        
        # Determine expiration for time-sensitive memories
        expires_at = None
        if memory_data['type'] in ['commitment', 'instruction']:
            expires_at = datetime.utcnow() + timedelta(days=30)
        
        db_memory = Memory(
            user_id=user_id,
            memory_type=memory_data['type'],
            key=memory_data['key'],
            value=memory_data['value'],
            context=memory_data.get('context', ''),
            source_conversation_id=conversation_id,
            source_turn=turn_number,
            confidence=memory_data.get('confidence', 0.5),
            importance_score=memory_data.get('importance', 0.5),
            vector_id=vector_id,
            expires_at=expires_at
        )
        
        db.add(db_memory)
        db.commit()
        db.refresh(db_memory)
        
        # Add to FAISS index
        user_index_data = self._get_user_index(user_id)
        index = user_index_data['index']
        
        # Create embedding
        embedding_text = f"{memory_data['type']}: {memory_data['key']} - {memory_data['value']}"
        embedding = self._get_embedding(embedding_text)
        
        # Add to index
        index.add(embedding.reshape(1, -1))
        
        # Store mapping
        faiss_id = user_index_data['next_id']
        user_index_data['id_map'][faiss_id] = {
            'db_id': db_memory.id,
            'vector_id': vector_id,
            'content': embedding_text,
            'metadata': {
                'type': memory_data['type'],
                'key': memory_data['key'],
                'value': memory_data['value'],
                'turn_number': turn_number,
                'confidence': memory_data.get('confidence', 0.5),
                'importance': memory_data.get('importance', 0.5)
            }
        }
        user_index_data['next_id'] += 1
        
        self._save_index()
        
        return db_memory
    
    def retrieve_relevant_memories(
        self,
        user_id: int,
        query: str,
        current_turn: int,
        top_k: int = None,
        memory_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories using FAISS."""
        
        if top_k is None:
            top_k = settings.MEMORY_TOP_K
        
        user_key = str(user_id)
        if user_key not in self.user_memories:
            return []
        
        user_index_data = self.user_memories[user_key]
        index = user_index_data['index']
        id_map = user_index_data['id_map']
        
        if index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self._get_embedding(query)
        
        # Search
        scores, indices = index.search(query_embedding.reshape(1, -1), min(top_k * 2, index.ntotal))
        
        memories = []
        for i, idx in enumerate(indices[0]):
            if idx == -1 or idx not in id_map:
                continue
            
            mem_data = id_map[idx]
            
            # Filter by memory type if specified
            if memory_types and mem_data['metadata']['type'] not in memory_types:
                continue
            
            # Calculate final score with importance and recency
            similarity = float(scores[0][i])
            importance_boost = mem_data['metadata'].get('importance', 0.5) * 0.2
            recency_boost = self._calculate_recency_boost(
                mem_data['metadata'].get('turn_number', 0),
                current_turn
            )
            
            final_score = similarity + importance_boost + recency_boost
            
            # Filter by confidence threshold
            if similarity < settings.MEMORY_CONFIDENCE_THRESHOLD:
                continue
            
            memories.append({
                'vector_id': mem_data['vector_id'],
                'db_id': mem_data['db_id'],
                'content': mem_data['content'],
                'similarity': similarity,
                'final_score': final_score,
                'metadata': mem_data['metadata']
            })
        
        # Sort by final score and return top_k
        memories.sort(key=lambda x: x['final_score'], reverse=True)
        return memories[:top_k]
    
    def _calculate_recency_boost(self, source_turn: int, current_turn: int) -> float:
        """Calculate recency boost for memory scoring."""
        if current_turn == 0:
            return 0
        
        turns_ago = current_turn - source_turn
        # Exponential decay: newer memories get higher boost
        return 0.1 * np.exp(-turns_ago / 100)  # Decay over ~100 turns
    
    def get_user_memories(
        self,
        db: Session,
        user_id: int,
        memory_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[Memory]:
        """Get all memories for a user."""
        query = db.query(Memory).filter(Memory.user_id == user_id)
        
        if memory_type:
            query = query.filter(Memory.memory_type == memory_type)
        if active_only:
            query = query.filter(Memory.is_active == True)
        
        return query.order_by(Memory.importance_score.desc()).all()
    
    def update_memory_access(self, db: Session, memory_id: int, current_turn: int):
        """Update access statistics for a memory."""
        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if memory:
            memory.access_count += 1
            memory.last_accessed_turn = current_turn
            db.commit()
    
    def deactivate_memory(self, db: Session, memory_id: int):
        """Soft delete a memory."""
        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if memory:
            memory.is_active = False
            db.commit()
            self._save_index()