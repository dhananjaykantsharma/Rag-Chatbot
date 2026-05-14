# RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that allows users to interact with documents through natural language queries. The system ingests documents, stores them in a vector database, and retrieves relevant information to generate context-aware responses.

## Features

- **Document Ingestion**: Upload and process various document formats
- **Vector Storage**: Uses ChromaDB for efficient vector storage and retrieval
- **Chat Interface**: Web-based chat interface built with React
- **API Backend**: FastAPI-based backend for handling chat and ingestion requests
- **Real-time Responses**: Generate responses based on retrieved document context

## Architecture

```mermaid
graph TD
    A[User] --> B[Frontend React App]
    B --> C[Chat Interface]
    C --> D[API Request to Backend]
    D --> E[FastAPI Backend]
    E --> F{Chat or Ingestion?}
    F -->|Ingestion| G[Document Processing]
    G --> H[ChromaDB Vector Storage]
    F -->|Chat| I[Query Processing]
    I --> J[Vector Search in ChromaDB]
    J --> K[Retrieve Relevant Documents]
    K --> L[Generate Response with LLM]
    L --> M[Send Response to Frontend]
    M --> N[Display in Chat Interface]
```

## Tech Stack

### Backend
- Python
- FastAPI
- ChromaDB
- Other dependencies (see requirements.txt)

### Frontend
- React
- JavaScript
- Lucide React (for icons)

## Installation

### Prerequisites
- Python 3.8+
- Node.js 14+
- Git
- PostgreSQL Database
- Redis (for caching)
- Supabase Account (for file storage)
- OpenAI API Key

### Environment Configuration

Create a `.env` file in the backend directory with the following variables:

```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/rag_chatbot

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_BUCKET=rag-chatbot

# JWT
SECRET_KEY=your_secret_key

# Email (for OTP)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Redis
REDIS_URL=redis://localhost:6379
```

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   .\venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database (run migrations):
   ```bash
   alembic upgrade head
   ```

5. Run the backend server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```
   The frontend will be available at `http://localhost:3000`

## Usage

1. Start both backend and frontend servers as described above.
2. Open your browser and navigate to the frontend URL (usually http://localhost:3000).
3. Upload documents through the ingestion interface.
4. Start chatting with your documents using the chat interface.

## Backend Architecture & Flow

### System Components

```mermaid
graph TD
    A[User Frontend] -->|Auth Requests| B[Auth Routes]
    A -->|Upload Documents| C[Ingestion Routes]
    A -->|Chat Messages| D[Chat Routes]
    
    B -->|Hash Password| E[Auth Utils]
    B -->|Send OTP| F[Email Service]
    B -->|Create JWT Token| E
    
    C -->|Store File Metadata| G[PostgreSQL Database]
    C -->|Upload File| H[Supabase Storage]
    C -->|Queue Ingestion| G
    
    I[Ingestion Processor] -->|Fetch Files to Process| G
    I -->|Download from Storage| H
    I -->|Process PDF/TXT| J[Document Processors]
    J -->|Split into Chunks| K[Text Splitter]
    K -->|Generate Embeddings| L[HuggingFace Model]
    L -->|Store Vectors| M[ChromaDB]
    M -->|Update Status| G
    
    D -->|Verify JWT| E
    D -->|Get Chat History| N[Redis Cache]
    D -->|Rewrite Question| O[OpenAI GPT-4o-mini]
    O -->|Search Vectors| M
    M -->|Retrieve Context| D
    D -->|Generate Answer| O
    O -->|Stream Response| A
    D -->|Save Chat| G
    D -->|Update Cache| N
```

### Detailed Flow Explanations

#### 1. Authentication Flow

**Signup Process:**
```
User Registration
    ↓
Password Hashing (bcrypt)
    ↓
Store in PostgreSQL (User table)
    ↓
Generate Random OTP
    ↓
Send OTP to User Email
    ↓
Wait for OTP Verification
```

**Login Process:**
```
User provides Email & Password
    ↓
Verify OTP Status (must be verified)
    ↓
Compare Password with Hashed Password
    ↓
Generate JWT Token if Valid
    ↓
Return Token to Frontend
```

**OTP Verification:**
```
User enters Email & OTP
    ↓
Compare with stored OTP
    ↓
Update is_otp_verified flag
    ↓
User can now login
```

#### 2. Document Ingestion Flow

**Upload Phase:**
```
User selects PDF/TXT file
    ↓
Frontend sends to /ingestion endpoint
    ↓
File uploaded to Supabase Storage
    ↓
Metadata stored in PostgreSQL:
  - file_name
  - file_type
  - file_size
  - file_path (Supabase URL)
  - status = "to_ingest"
  - user_id (for isolation)
```

**Processing Phase:**
```
Call /ingestion endpoint
    ↓
Query DB for files with status="to_ingest"
    ↓
For each file:
  1. Download from Supabase Storage
  2. Load documents:
     - PDF → PyPDFLoader
     - TXT → TextLoader
  3. Split documents into chunks:
     - chunk_size: 1000 characters
     - overlap: 200 characters
  4. Add metadata to each chunk:
     - user_id (for data isolation)
     - datasource_id (to track source)
  5. Generate embeddings using HuggingFace
     - Model: sentence-transformers/all-MiniLM-L6-v2
  6. Store in ChromaDB:
     - Collection name: user_{user_id}
  7. Update status to "ingested"
    ↓
Return success/failure statistics
```

**Storage Structure in ChromaDB:**
```
ChromaDB Database
├── Collection: user_1
│   ├── Document 1
│   │   ├── Embedding (384-dimensional vector)
│   │   ├── Content (text chunk)
│   │   └── Metadata (user_id, datasource_id)
│   ├── Document 2
│   └── Document N
├── Collection: user_2
└── Collection: user_N
```

#### 3. Chat Flow (RAG Process)

**Step-by-Step Chat Process:**

```
1. USER ASKS QUESTION
   └─ Question received at /chat/ask endpoint
   
2. CREATE CHAT HISTORY ENTRY
   └─ Status: "in_progress"
   └─ Stored in PostgreSQL
   
3. RETRIEVE CONTEXT
   └─ Get previous chat history from Redis
   └─ Convert to LangChain message format
   
4. REWRITE QUESTION (Context-Aware)
   ├─ Input: Previous chat history + current question
   ├─ LLM: GPT-4o-mini (temperature=0)
   ├─ Process: Convert question to standalone form
   └─ Example:
        Original: "Tell me more about it"
        Rewritten: "Tell me more about the machine learning algorithms mentioned"
   
5. VECTOR SIMILARITY SEARCH
   ├─ Input: Rewritten standalone question
   ├─ Embedding: Convert question to vector using HuggingFace
   ├─ ChromaDB: Search for top 3 similar document chunks
   └─ Output: Most relevant context documents
   
6. BUILD CONTEXT
   └─ Format retrieved documents into context string
   
7. GENERATE RESPONSE (Streaming)
   ├─ System Prompt: You are a helpful assistant
   ├─ Context: Retrieved documents
   ├─ Chat History: Previous conversation
   ├─ User Question: Rewritten standalone question
   ├─ LLM: GPT-4o-mini with streaming (temperature=0.1)
   └─ Output: Streamed token by token to frontend
   
8. SAVE & CACHE
   ├─ Full response saved to PostgreSQL ChatHistory table
   ├─ Status: "completed"
   ├─ User message + AI response saved to Redis cache
   └─ Chat history updated for next question
   
9. RETURN RESPONSE
   └─ Frontend displays streamed response in real-time
```

**Complete Chat Request/Response Flow:**

```
Frontend (React)
    │
    ├─→ POST /chat/ask
    │   ├─ Headers: Authorization: Bearer {JWT_TOKEN}
    │   └─ Body: { "question": "What is RAG?" }
    │
    └─← Response (Streaming):
        ├─ Status: 200 OK
        ├─ Content-Type: application/json
        └─ Body (streamed):
           RAG stands for Retrieval-Augmented Generation...
           (tokens streamed one by one)
```

### Data Flow Diagram

```
UPLOAD DOCUMENTS
─────────────────
User Files → Frontend → Backend → Supabase Storage
                          ↓
                    PostgreSQL (metadata)
                          ↓
                    Mark as "to_ingest"
                          ↓
              [/ingestion endpoint called]
                          ↓
          Download → Process → Split → Embed
                          ↓
                 Store in ChromaDB (vectors)
                          ↓
              Update status to "ingested"


CHAT INTERACTION
────────────────
User Question → Frontend → /chat/ask → PostgreSQL (create entry)
                                             ↓
                                    Get history from Redis
                                             ↓
                              Rewrite question (GPT-4o-mini)
                                             ↓
                      Convert to embedding (HuggingFace)
                                             ↓
                    Search ChromaDB (top 3 similar chunks)
                                             ↓
                        Generate response (GPT-4o-mini)
                                             ↓
                            Stream to Frontend
                                             ↓
                          Save to PostgreSQL
                                             ↓
                          Update Redis cache
```

### API Endpoints

**Authentication:**
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login and get JWT token
- `POST /auth/verify-otp` - Verify OTP sent to email

**Document Management:**
- `POST /ingestion/ingestion` - Trigger document processing and embedding
- `POST /datasource/upload` - Upload document file

**Chat:**
- `POST /chat/ask` - Send question and get streaming response

### Database Schema

**Users Table:**
```sql
- id (Primary Key)
- full_name
- email (Unique)
- hashed_password
- is_otp_verified
- generated_otp
- created_at
```

**Datasources Table (Files Uploaded):**
```sql
- id (UUID Primary Key)
- user_id (Foreign Key → Users)
- file_name
- file_type (pdf/txt)
- file_size
- file_path (Supabase URL)
- status (to_ingest / ingested)
- created_at
- updated_at
```

**ChatHistory Table:**
```sql
- id (UUID Primary Key)
- user_id (Foreign Key → Users)
- question (User's question)
- answer (AI's response)
- status (in_progress / completed)
- created_at
```

### Key Technologies

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Vector DB:** ChromaDB
- **Embeddings:** HuggingFace (all-MiniLM-L6-v2)
- **LLM:** OpenAI GPT-4o-mini
- **Cache:** Redis
- **File Storage:** Supabase
- **Authentication:** JWT + bcrypt
- **Email:** FastAPI Mail
- **Document Processing:** LangChain (PyPDFLoader, TextLoader)

## Project Structure

```
├── backend/                          # FastAPI Backend Application
│   ├── main.py                      # FastAPI app initialization & CORS setup
│   ├── database.py                  # PostgreSQL connection & session management
│   ├── models.py                    # SQLAlchemy ORM models (User, Datasource, ChatHistory)
│   ├── embeddings.py                # HuggingFace embeddings initialization
│   ├── requirements.txt             # Python dependencies
│   │
│   ├── routes/
│   │   ├── auth.py                  # Authentication endpoints (signup, login, verify-otp)
│   │   ├── chat.py                  # Chat endpoint with RAG logic & streaming
│   │   ├── ingestion.py             # Document ingestion & embedding pipeline
│   │   └── datasource.py            # File upload & management endpoints
│   │
│   ├── utils/
│   │   ├── auth_utils.py            # Password hashing, JWT creation, OTP management
│   │   ├── chat_utils.py            # Chat history formatting, response streaming
│   │   └── redis_util.py            # Redis cache operations for chat history
│   │
│   ├── chroma_db/                   # ChromaDB vector database storage
│   │   ├── chroma.sqlite3           # Vector database file
│   │   └── {collection_ids}/        # User-specific vector collections
│   │
│   └── alembic/                     # Database migration system
│       ├── env.py                   # Alembic configuration
│       ├── script.py.mako           # Migration script template
│       └── versions/                # Migration files
│           ├── 377706994509_add_the_user_table.py
│           ├── 8343a24261ab_add_chat_history_table.py
│           ├── d4005cb655e3_add_the_datasource_table.py
│           └── ...                  # Other migrations
│
├── frontend/                         # React Frontend Application
│   ├── package.json                 # Node.js dependencies
│   ├── public/
│   │   ├── index.html               # Main HTML file
│   │   └── manifest.json            # PWA manifest
│   │
│   └── src/
│       ├── api.js                   # Axios API client for backend requests
│       ├── App.js                   # Main React component & routing
│       ├── App.css                  # Global styles
│       ├── index.js                 # React entry point
│       ├── index.css                # Global CSS
│       │
│       ├── ChatInterface.jsx        # Main chat UI component
│       ├── LandingPage.jsx          # Welcome page with document upload
│       │
│       ├── components/
│       │   ├── Auth.jsx             # Login/Signup form component
│       │   ├── ProtectedRoute.jsx   # JWT-protected route wrapper
│       │   └── VerifyOtp.jsx        # OTP verification component
│       │
│       └── context/
│           └── AuthContext.jsx      # Global auth state management
│
└── README.md                        # This file
```

### Backend File Descriptions

**Core Files:**
- `main.py` - Initializes FastAPI app, sets up CORS middleware for React frontend, includes all route routers, and runs embeddings on startup
- `database.py` - Configures PostgreSQL connection using SQLAlchemy, creates session maker for database operations
- `models.py` - Defines database schema (User, Datasource, ChatHistory) with relationships and constraints
- `embeddings.py` - Lazy-loads HuggingFace embeddings model on first request to save memory

**Routes (API Endpoints):**
- `routes/auth.py` - Handles user registration, login, OTP verification with JWT token generation
- `routes/chat.py` - Implements RAG chat endpoint with question rewriting, vector search, and response streaming
- `routes/ingestion.py` - Manages document upload processing: downloads from Supabase, splits into chunks, generates embeddings, stores in ChromaDB
- `routes/datasource.py` - Manages file metadata, storage, and deletion

**Utilities:**
- `utils/auth_utils.py` - Password hashing/verification (bcrypt), JWT token creation/verification, OTP generation/email sending
- `utils/chat_utils.py` - Converts chat history to LangChain message format, handles streaming responses
- `utils/redis_util.py` - Stores/retrieves chat history from Redis for fast access

**Database Migrations:**
- `alembic/` - Manages database schema changes across versions using Alembic

### Frontend File Descriptions

- `api.js` - Centralizes all API calls to backend with JWT token handling
- `AuthContext.jsx` - Global state management for user authentication data
- `Auth.jsx` - Login and signup form component with email/password validation
- `VerifyOtp.jsx` - OTP verification component that sends code to backend
- `ProtectedRoute.jsx` - Route wrapper that redirects unauthenticated users to login
- `LandingPage.jsx` - Main page with file upload interface and document list
- `ChatInterface.jsx` - Chat UI with message display, streaming responses, and input form

## Important Concepts & Configuration

### Data Isolation
- Each user has their own ChromaDB collection named `user_{user_id}`
- When documents are ingested, `user_id` is added to chunk metadata
- During chat, only the user's own collection is searched
- This ensures users cannot access other users' documents

### Chat History Management
- **Redis Cache:** Current session chat history for real-time access
- **PostgreSQL:** Persistent chat history for records and analytics
- Chat history is used to:
  - Maintain conversation context
  - Rewrite follow-up questions with context
  - Ensure continuity across sessions

### Embeddings
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions:** 384-dimensional vector space
- **Device:** CPU (can be changed to GPU for better performance)
- **Time:** ~10-15 seconds to load on first request

### Vector Database (ChromaDB)
- Stores document chunks as vectors
- Uses SQLite as backend (`chroma.sqlite3`)
- Retrieval uses cosine similarity
- Returns top-k (default: 3) most similar documents
- Each collection is isolated per user

### Document Processing Pipeline
**Chunk Configuration:**
- `chunk_size`: 1000 characters
- `chunk_overlap`: 200 characters
- Overlap helps maintain context between chunks

**Supported Formats:**
- PDF (via PyPDFLoader)
- TXT (via TextLoader)

### LLM Configuration
**Question Rewriting:**
- Model: GPT-4o-mini
- Temperature: 0 (deterministic)
- Purpose: Convert conversational questions to standalone form
- Example: "Tell me more" → "Tell me more about the RAG architecture"

**Response Generation:**
- Model: GPT-4o-mini
- Temperature: 0.1 (slightly creative)
- Streaming: Enabled for real-time token delivery
- System Prompt: Instructs to use only provided context

### Security
- **Passwords:** Hashed with bcrypt (salt rounds: 12)
- **Authentication:** JWT tokens with expiration
- **OTP Verification:** Required before login
- **Email Verification:** Confirms user email ownership
- **CORS:** Only allows requests from frontend URL
- **Database:** SQL injection prevented via SQLAlchemy ORM

### Performance Optimization
- Redis caching reduces database queries
- Lazy-loading of embeddings model saves memory
- Vector similarity search is fast (optimized in ChromaDB)
- Streaming responses provide immediate user feedback
- Supabase CDN delivers files efficiently

## Troubleshooting

### Backend Won't Start
1. Check all environment variables in `.env` file
2. Ensure PostgreSQL service is running
3. Ensure Redis is running: `redis-cli ping`
4. Run migrations: `alembic upgrade head`
5. Check for port conflicts: `netstat -ano | findstr :8000` (Windows)

### Documents Not Being Ingested
1. Check Supabase credentials and bucket name
2. Verify file status is "to_ingest": `SELECT * FROM datasources WHERE status='to_ingest'`
3. Check for file processing errors in logs
4. Ensure files are PDF or TXT format

### Chat Returning Empty Results
1. Verify documents were ingested: `SELECT * FROM datasources WHERE status='ingested'`
2. Check ChromaDB collection exists: `ls chroma_db/`
3. Ensure OpenAI API key is valid
4. Check vector search results are relevant to your query

### OTP Not Arriving
1. Verify email credentials in `.env`
2. Check email is enabled for third-party apps
3. Verify Gmail app password (not regular password)
4. Check spam folder

### CORS Errors on Frontend
1. Ensure frontend URL is in `origins` list in `main.py`
2. Frontend must include `Authorization: Bearer {token}` header
3. Clear browser cache and cookies

## Development Workflow

### Adding a New Route
1. Create handler function in appropriate route file
2. Add authentication dependency if needed: `Depends(get_current_user)`
3. Use database session: `Depends(get_db)`
4. Include proper error handling
5. Test with FastAPI docs at `/docs`

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

### Testing Chat Flow Locally
1. Create a test user and verify OTP
2. Upload a PDF file
3. Call `/ingestion/ingestion` to process documents
4. Call `/chat/ask` with a question about your documents

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add YourFeature'`)
5. Push to the branch (`git push origin feature/YourFeature`)
6. Submit a pull request

## License

This project is licensed under the MIT License.