# RAG Knowledge Assistant - Product Requirements Document

## Original Problem Statement
Build LLM Knowledge assistant using RAG and MCP

## User Choices
- **LLM Provider**: OpenAI GPT-4o
- **Document Formats**: PDF, TXT, MD, DOCX
- **Core Features**: Document upload & processing, Chat with context-aware responses, Conversation history, Source citations
- **Authentication**: None (open access)
- **Design**: Stylish "Cognitive Library" theme

## User Personas
1. **Knowledge Worker**: Needs to quickly query large document collections
2. **Researcher**: Requires accurate citations and source tracking
3. **Professional**: Wants organized conversation history for reference

## Core Requirements
- Upload documents in multiple formats (PDF, TXT, MD, DOCX)
- Process and chunk documents for vector search
- RAG-based chat with context retrieval
- Source citations in AI responses
- Conversation management (create, list, delete)
- Document management (upload, list, delete)

## Architecture
- **Frontend**: React with Shadcn UI components
- **Backend**: FastAPI with async endpoints
- **Database**: MongoDB for conversations/messages/documents
- **Vector Store**: ChromaDB for document embeddings
- **LLM**: OpenAI GPT-4o via LangChain

## What's Been Implemented 
- [x] Document upload endpoint with multi-format support
- [x] Text extraction (PDF, DOCX, TXT, MD)
- [x] Document chunking and ChromaDB storage
- [x] Conversation CRUD operations
- [x] RAG-based chat with source citations
- [x] Dark sidebar / Light content UI design
- [x] Real-time typing indicators
- [x] Responsive drag-drop file upload

## Prioritized Backlog
### P0 (Critical)
- All implemented ✓

### P1 (Important)
- Multiple file upload at once
- Document search/filter
- Export chat history

### P2 (Nice to Have)
- Document preview
- Highlight relevant text in sources
- User sessions/authentication
- Custom embedding models

## Next Tasks
1. Add batch document upload
2. Implement document search functionality
3. Add conversation export feature
