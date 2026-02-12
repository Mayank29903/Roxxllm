# 🧠 LongFormMemoryAI

> A smart AI assistant that remembers conversations, understands context, and improves responses over time.
Built with a scalable memory pipeline, semantic retrieval, and modern full-stack architecture.




## 📸 Screenshots

### Memory AI UI
![Memory AI UI](./screenshots/DemoUI.png)

### Login Page
![Login Page](./screenshots/LoginPage.png)

### Signup Page
![Signup Page](./screenshots/SignupPage.png)



## 🎯 Overview

LongFormMemoryAI is a sophisticated AI conversation system that maintains persistent memory across thousands of interactions. Unlike traditional chatbots that forget after each conversation, this system:

- **Remembers user preferences** across all conversations
- **Learns from past interactions** to provide personalized responses  
- **Maintains context** over 1000+ conversation turns
- **Supports multiple LLM providers** (OpenRouter, Gemini)
- **Provides real-time streaming** responses
- **Implements secure authentication** with Firebase/Google Sign-In

## ✨ Features

### 🧠 Memory System
- **Long-term memory storage** across unlimited conversations
- **Semantic search** for relevant memory retrieval
- **Time-aware memory access** (recent memories prioritized)
- **Memory inference** - answers questions based on stored preferences
- **Automatic memory extraction** from conversations
- **Memory categorization** (preferences, facts, entities, commitments)

### 🤖 AI Integration
- **Multiple LLM providers**: OpenRouter, Google Gemini
- **Real-time streaming** responses
- **Context-aware responses** using retrieved memories
- **Configurable models** and parameters

### 🔐 Authentication & Security
- **Firebase authentication** with Google Sign-In
- **JWT token-based** session management
- **Secure API endpoints** with proper validation
- **CORS configuration** for frontend integration

### 🛠 Developer Features
- **RESTful API** with comprehensive documentation
- **Environment-based configuration**
- **Production-ready deployment setup**
- **Comprehensive error handling**
- **Structured logging** (debug mode available)

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend    │    │    Backend     │    │   Database      │
│   (React)     │◄──►│   (FastAPI)    │◄──►│   (MongoDB)    │
│               │    │               │    │               │
│ • UI/UX       │    │ • API Routes   │    │ • User Data    │
│ • State Mgmt   │    │ • Auth Logic   │    │ • Memories     │
│ • API Calls    │    │ • Memory Mgmt  │    │ • Conversations│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   LLM Service  │
                       │               │
                       │ • OpenRouter   │
                       │ • Gemini       │
                       │ • Streaming    │
                       └─────────────────┘
```

### Core Components

1. **Frontend (React)**
   - Modern React application with Vite
   - Tailwind CSS for styling
   - Axios for API communication
   - Firebase authentication integration

2. **Backend (FastAPI)**
   - High-performance async API
   - JWT-based authentication
   - Memory management system
   - LLM service abstraction

3. **Memory System**
   - Semantic search with embeddings
   - Time-based memory retrieval
   - Automatic memory extraction
   - Cross-conversation memory access

4. **Database (MongoDB)**
   - Document-based storage
   - Beanie ODM for Python
   - Scalable for large datasets

## ⚙ How It Works

### 1. User Interaction Flow
```
User sends message → Frontend → Backend API → Memory Retrieval → LLM → Response → Store Memory → User
```

### 2. Memory Processing
```
Conversation → Memory Extraction → Classification → Storage → Semantic Indexing → Search Availability
```

### 3. Memory Retrieval
```
New Message → Semantic Search → Time-based Filter → Confidence Scoring → Context Injection → LLM
```

### 4. Authentication Flow
```
Google Sign-In → Firebase Token → Backend Verification → JWT Generation → Secure API Access
```

## 🛠 Tech Stack

### Frontend
- **React 18** - Modern UI framework
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **Firebase SDK** - Google authentication

### Backend
- **FastAPI** - Modern async web framework
- **Python 3.11+** - Core programming language
- **MongoDB** - NoSQL database for storage
- **Motor** - Async MongoDB driver
- **Beanie** - MongoDB ODM with validation
- **JWT** - Token-based authentication
- **Sentence Transformers** - Text embeddings
- **OpenRouter/Gemini APIs** - LLM providers

### Infrastructure
- **Uvicorn** - ASGI server
- **Gunicorn** - Production WSGI server
- **Firebase Admin** - Server-side authentication

## 📁 Folder Structure

```
long-form-memory-ai/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/        # API and utility services
│   │   └── utils/           # Helper functions
│   ├── public/               # Static assets
│   ├── package.json          # Dependencies and scripts
│   └── vite.config.js       # Vite configuration
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── models/           # Database models
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── core/             # Core algorithms
│   │   └── config.py         # Configuration management
│   ├── requirements.txt        # Python dependencies
│   ├── run.py              # Application entry point
│   └── .env.example        # Environment template
├── DEPLOYMENT.md             # Deployment guide
└── README.md               # This file
```

## 🚀 Installation

### Prerequisites
- **Python 3.11+** for backend
- **Node.js 18+** for frontend
- **MongoDB** database
- **Firebase project** (optional, for Google auth)

### Backend Setup
```bash
# Clone repository
git clone <repository-url>
cd long-form-memory-ai/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start development server
python run.py
```

### Frontend Setup
```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

## 🔧 Environment Variables

### Backend (.env)
```bash
# Application
APP_NAME=LongFormMemoryAI
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-secret-key-here

# Database
MONGODB_URL=mongodb://username:password@host:port/database

# LLM Configuration
OPENROUTER_API_KEY=your-openrouter-key
LLM_MODEL=openai/gpt-4o-mini

# Firebase (optional)
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

### Frontend (.env)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Firebase Configuration
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_PROJECT_ID=your-project-id

# Application
VITE_APP_NAME=LongFormMemoryAI
VITE_NODE_ENV=development
```

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/google` - Google authentication
- `GET /auth/me` - Get current user

### Conversations
- `GET /conversations` - List user conversations
- `POST /conversations` - Create new conversation
- `GET /conversations/{id}` - Get conversation details
- `DELETE /conversations/{id}` - Delete conversation

### Messages
- `POST /conversations/{id}/messages` - Send message
- `GET /conversations/{id}/messages` - Get conversation history

### Memory
- `GET /memories` - Search memories
- `GET /memories/stats` - Memory statistics
- `DELETE /memories/{id}` - Delete memory

### Users
- `GET /users/profile` - User profile
- `PUT /users/profile` - Update profile

## 🧪 Challenges & Solutions

### Challenge 1: Memory Scalability
**Problem**: Storing and searching through thousands of conversation turns
**Solution**: Semantic embeddings with time-based filtering and confidence scoring

### Challenge 2: Context Relevance
**Problem**: Finding the most relevant memories for current context
**Solution**: Multi-layered retrieval (semantic + recent + important + preferences)

### Challenge 3: Real-time Performance
**Problem**: Providing fast responses with large memory datasets
**Solution**: Async operations, efficient indexing, and caching strategies

### Challenge 4: Memory Accuracy
**Problem**: Extracting accurate memories from conversations
**Solution**: Multiple extraction methods with confidence scoring and fallbacks

## 🔮 Future Improvements

### Short Term
- [ ] **Memory visualization** dashboard
- [ ] **Conversation analytics** and insights
- [ ] **Memory editing** interface for users
- [ ] **Import/export** memory functionality

### Medium Term
- [ ] **Multi-modal memory** (images, files)
- [ ] **Advanced inference** with reasoning chains
- [ ] **Memory sharing** between users (opt-in)
- [ ] **Plugin system** for custom memory types

### Long Term
- [ ] **Federated learning** for memory improvement
- [ ] **Voice interface** for conversations
- [ ] **Mobile applications** (iOS/Android)
- [ ] **Enterprise features** with team collaboration

## 👥 Contributors

### Core Team
- **[Aditya Kumar Upadhyay](https://github.com/Adi-3108)** - Backend Developer & AI Integration
- **[Aaditya Kothari](https://github.com/Aaditya-3)** - Frontend Developer & UI/UX & Debugging
- **[Mayank Kumar Singh](https://github.com/Mayank29903)** - Lead Developer & Architect


### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React code
- Write tests for new features
- Update documentation for API changes
- Keep commits atomic and well-described

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### MIT License Summary
- ✅ Commercial use allowed
- ✅ Modification allowed  
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ Must include license and copyright notice
- ⚠️ No warranty provided

---

## 🙏 Acknowledgments

- **OpenAI** for GPT models via OpenRouter
- **Google** for Gemini models and Firebase
- **MongoDB** for the robust database solution
- **FastAPI** for the excellent web framework
- **React** and **Vite** for the modern frontend experience

---

**🚀 Ready to build the future of AI memory?**  
**Star this repo** and **join our community**!

<div align="center">
  <strong>Made with ❤️ by the LongFormMemoryAI team</strong>
</div>
