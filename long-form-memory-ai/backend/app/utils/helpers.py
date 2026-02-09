from datetime import datetime, timedelta
from typing import Optional
import re


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat() if dt else None


def parse_datetime(date_string: str) -> Optional[datetime]:
    """Parse ISO datetime string."""
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def sanitize_text(text: str) -> str:
    """Clean and sanitize text input."""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    return text.strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + suffix


def calculate_relevance_score(
    similarity: float,
    importance: float,
    recency_boost: float = 0.0
) -> float:
    """Calculate final relevance score for memory retrieval."""
    # Weighted combination
    score = (similarity * 0.6) + (importance * 0.3) + (recency_boost * 0.1)
    return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1


def is_expired(expiry_date: Optional[datetime]) -> bool:
    """Check if a memory has expired."""
    if not expiry_date:
        return False
    return datetime.utcnow() > expiry_date


def generate_memory_key(text: str) -> str:
    """Generate a semantic key from text."""
    # Convert to lowercase
    key = text.lower()
    # Remove special characters
    key = re.sub(r'[^\w\s]', '', key)
    # Replace spaces with underscores
    key = re.sub(r'\s+', '_', key)
    # Limit length
    return key[:50]


def mask_sensitive_data(text: str) -> str:
    """Mask sensitive information like emails, phone numbers."""
    # Mask emails
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]', text)
    # Mask phone numbers (basic pattern)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    return text


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (for OpenAI)."""
    # Average: 1 token ≈ 4 characters for English
    return len(text) // 4


def format_memory_for_display(memory_type: str, key: str, value: str) -> str:
    """Format memory for human-readable display."""
    type_emojis = {
        'preference': '⚙️',
        'fact': '📋',
        'entity': '👤',
        'commitment': '📅',
        'instruction': '📌',
        'constraint': '⚠️'
    }
    
    emoji = type_emojis.get(memory_type, '💡')
    return f"{emoji} [{memory_type.upper()}] {key}: {value}"