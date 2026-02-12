# 🚀 LongFormMemoryAI Backend

> FastAPI-based backend service for intelligent AI conversations with persistent memory

![FastAPI](https://img.shields.io/badge/FastAPI-0.115.8-009688?style=flat-square&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)
![MongoDB](https://img.shields.io/badge/MongoDB-4.6.1-47A248?style=flat-square&logo=mongodb)

## 🎯 Overview

The LongFormMemoryAI backend is a high-performance, async-first API server that provides:

- **RESTful API** with automatic OpenAPI documentation
- **Long-term memory management** across conversations
- **Multi-provider LLM integration** (OpenRouter, Gemini)
- **Secure authentication** with Firebase and JWT
- **Real-time streaming** responses
- **Semantic search** and memory retrieval
- **Production-ready** configuration and deployment

## ✨ Features

### 🧠 Memory System
- **Persistent memory storage** across unlimited conversations
- **Semantic search** using sentence transformers
- **Time-aware retrieval** (recent memories prioritized)
- **Memory inference** from stored preferences
- **Automatic extraction** with confidence scoring
- **Cross-conversation** memory access

### 🔐 Authentication & Security
- **Firebase authentication** with Google Sign-In
- **JWT token management** with refresh support
- **Password hashing** with bcrypt
- **CORS protection** with configurable origins
- **Input validation** with Pydantic models

### 🤖 AI Integration
- **OpenRouter API** integration for multiple models
- **Google Gemini** direct API support
- **Streaming responses** for real-time interaction
- **Configurable parameters** (temperature, tokens, etc.)
- **Error handling** and graceful fallbacks

### 🛠 Developer Experience
- **Auto-generated API docs** with Swagger UI
- **Environment-based** configuration
- **Comprehensive logging** (debug mode available)
- **Health check** endpoints
- **Structured error responses**

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├─────────────────────────────────────────────────────────────────┤
│  Request Flow                                            │
│                                                         │
│  Client → CORS → Auth → Router → Service → LLM → Response  │
│           ↓         ↓        ↓         ↓        ↓         │
│  Validation → JWT → Business → Memory → Stream → Store     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│                                                         │
│  MongoDB ← Beanie ODM ← Models ← Services → Memories     │
│      ↑              ↑           ↑         ↑          ↑        │
│  Users  ←  Conversations  Messages  Extraction  Search   │
└─────────────────────────────────────────────────────────────────┘
```

### Core Layers

1. **API Layer** (`app/routers/`)
   - HTTP request handling
   - Input validation
   - Response formatting
   - Authentication middleware

2. **Service Layer** (`app/services/`)
   - Business logic implementation
   - LLM communication
   - Memory management
   - User authentication

3. **Data Layer** (`app/models/`)
   - Database models with Beanie
   - Schema validation
   - Relationship definitions
   - Index optimization

4. **Core Layer** (`app/core/`)
   - Memory algorithms
   - Embedding generation
   - Search and retrieval
   - Inference logic

## ⚙ How It Works

### 1. Request Processing
```python
@router.post("/conversations/{id}/messages")
async def send_message(message: MessageCreate):
    # 1. Authenticate user
    user = await get_current_user(token)
    
    # 2. Retrieve relevant memories
    memories = await memory_service.search_memories(
        user_id=user.id,
        query_text=message.content,
        current_turn=conversation.turn_count
    )
    
    # 3. Generate response with LLM
    response = await llm_service.generate_response(
        messages=context_with_memories,
        stream=True
    )
    
    # 4. Extract and store new memories
    await memory_extractor.extract_memories(
        conversation=conversation,
        user_message=message.content,
        assistant_response=response
    )
    
    return StreamingResponse(response)
```

### 2. Memory Retrieval Strategy
```python
# Multi-layered memory retrieval
def get_relevant_memories(query, user_id):
    # 1. Semantic search (embeddings)
    semantic = semantic_search(query, user_id, top_k=12)
    
    # 2. Recent memories (time-based)
    recent = get_recent_memories(user_id, hours_ago=4)
    
    # 3. Important memories (high confidence)
    important = get_important_memories(user_id, limit=8)
    
    # 4. Preference memories (user preferences)
    preferences = get_preference_memories(user_id, limit=30)
    
    # 5. Merge and prioritize
    return merge_and_rank(semantic, recent, important, preferences)
```

### 3. Authentication Flow
```python
# Firebase + JWT authentication
async def login_with_google(firebase_token: str):
    # 1. Verify Firebase token
    firebase_user = firebase_service.verify_id_token(firebase_token)
    
    # 2. Create/update user in database
    user = await firebase_service.create_or_update_user(firebase_user)
    
    # 3. Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}
```

## 🛠 Tech Stack

### Core Framework
- **FastAPI 0.115.8** - Modern async web framework
- **Python 3.11+** - Core programming language
- **Pydantic 2.10.6** - Data validation and settings
- **Uvicorn 0.34.0** - ASGI server

### Database & Storage
- **MongoDB 4.6.1** - NoSQL document database
- **Motor 3.3.2** - Async MongoDB driver
- **Beanie 1.25.0** - MongoDB ODM with validation
- **Sentence Transformers 3.4.1** - Text embeddings

### Authentication & Security
- **python-jose 3.3.0** - JWT token handling
- **passlib 1.7.4** - Password hashing
- **bcrypt 4.2.1** - Secure password storage
- **Firebase Admin 6.4.0** - Google authentication

### AI & ML
- **OpenAI 1.61.0** - OpenRouter API client
- **LangChain 0.3.17** - LLM orchestration
- **Tiktoken 0.8.0** - Token counting
- **httpx 0.28.1** - Async HTTP client

### Development Tools
- **pytest 8.3.4** - Testing framework
- **python-dotenv 1.0.1** - Environment management
- **gunicorn 21.2.0** - Production server

## 📁 Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection setup
│   │
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── user.py            # User model and schema
│   │   ├── chat.py            # Conversation and message models
│   │   └── memory.py          # Memory model and types
│   │
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication routes
│   │   ├── chat.py            # Conversation and message routes
│   │   ├── memory.py          # Memory management routes
│   │   └── user.py            # User profile routes
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py     # Authentication logic
│   │   ├── chat_service.py     # Conversation handling
│   │   ├── memory_service.py   # Memory management
│   │   ├── llm_service.py     # LLM integration
│   │   └── firebase_service.py # Firebase authentication
│   │
│   ├── core/                  # Core algorithms
│   │   ├── __init__.py
│   │   ├── memory_extractor.py  # Memory extraction logic
│   │   ├── memory_reasoner.py   # Memory inference
│   │   ├── memory_store.py     # Storage abstraction
│   │   └── retriever.py       # Search and retrieval
│   │
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       └── helpers.py          # Common utilities
│
├── requirements.txt             # Python dependencies
├── run.py                    # Application startup script
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 🚀 Installation

### Prerequisites
- **Python 3.11+** installed
- **MongoDB** database running
- **Firebase project** (for Google auth)

### Quick Start
```bash
# Clone and navigate
git clone <repository-url>
cd long-form-memory-ai/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start development server
python run.py
```

## 🔧 Environment Variables

### Required Variables
```bash
# Application
SECRET_KEY=your-cryptographically-secure-secret-key
MONGODB_URL=mongodb://username:password@host:port/database
OPENROUTER_API_KEY=your-openrouter-api-key
```

### Optional Variables
```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# LLM Configuration
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4o-mini
GEMINI_API_KEY=your-gemini-key

# Firebase Authentication
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json

# Caching (Optional)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 📡 API Endpoints

### Authentication (`/auth`)
```http
POST   /auth/register          # User registration
POST   /auth/login             # Email/password login
POST   /auth/google            # Google Sign-In
GET    /auth/me               # Get current user profile
```

### Conversations (`/conversations`)
```http
GET    /conversations           # List user conversations
POST   /conversations           # Create new conversation
GET    /conversations/{id}      # Get conversation details
DELETE /conversations/{id}      # Delete conversation
```

### Messages (`/conversations/{id}/messages`)
```http
POST   /messages               # Send message to conversation
GET    /messages               # Get conversation history
```

### Memory (`/memories`)
```http
GET    /memories               # Search user memories
GET    /memories/stats         # Memory statistics
DELETE /memories/{id}          # Delete specific memory
```

### Users (`/users`)
```http
GET    /users/profile          # Get user profile
PUT    /users/profile          # Update user profile
```

### System
```http
GET    /                      # API information
GET    /health                 # Health check
GET    /docs                  # Swagger documentation
```

## 🧪 Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Database Migrations
```bash
# Beanie handles migrations automatically
# Just ensure models are imported in app/models/__init__.py
```

### Debug Mode
```bash
# Enable debug logging
DEBUG=true python run.py

# Or set in .env
DEBUG=true
```

## 🚀 Production Deployment

### Using Gunicorn
```bash
# Install production server
pip install gunicorn

# Start with workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Configuration
```bash
# Production .env example
DEBUG=false
SECRET_KEY=your-production-secret-key
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/db
OPENROUTER_API_KEY=prod-openrouter-key
CORS_ORIGINS=https://yourdomain.com
```

## 🔒 Security Considerations

### Authentication
- **JWT tokens** expire after 30 minutes
- **Firebase tokens** are verified on each request
- **Password hashing** with bcrypt (work factor 12)
- **CORS** configured for specific origins

### Data Protection
- **Input validation** with Pydantic models
- **SQL injection protection** (MongoDB driver)
- **Rate limiting** (implement as needed)
- **HTTPS enforcement** in production

### Environment Security
- **Secrets** stored in environment variables
- **No hardcoded credentials** in source code
- **Production keys** separate from development
- **Firebase credentials** properly secured

## 🧪 Challenges & Solutions

### Challenge 1: Memory Retrieval Performance
**Problem**: Searching through thousands of memories quickly
**Solution**: Semantic embeddings with time-based filtering and caching

### Challenge 2: Context Window Management
**Problem**: Fitting memories into LLM context limits
**Solution**: Intelligent memory selection and prioritization algorithms

### Challenge 3: Concurrent Memory Access
**Problem**: Multiple requests accessing same memories
**Solution**: Async operations with proper database connection pooling

### Challenge 4: Memory Consistency
**Problem**: Keeping memories synchronized across conversations
**Solution**: Atomic operations and proper transaction handling

## 🔮 Future Improvements

### Backend Enhancements
- [ ] **GraphQL API** for efficient data fetching
- [ ] **WebSocket support** for real-time updates
- [ ] **Memory analytics** and insights API
- [ ] **Advanced caching** with Redis
- [ ] **Rate limiting** and DDoS protection
- [ ] **Background tasks** for memory processing

### Infrastructure
- [ ] **Microservices architecture** for scalability
- [ ] **Message queue** for async processing
- [ ] **Database sharding** for large datasets
- [ ] **Monitoring and alerting** system
- [ ] **Automated backups** and recovery

### AI/ML Improvements
- [ ] **Custom embedding models** fine-tuned on conversations
- [ ] **Advanced reasoning** chains for inference
- [ ] **Multi-modal memory** (images, audio, files)
- [ ] **Federated learning** for privacy

## 📄 License

This project is licensed under the **MIT License**.

---

## 🤝 Contributing

We welcome contributions! Please see the main [README.md](../README.md) for guidelines.

---

**Built with ❤️ using FastAPI and modern Python technologies**
