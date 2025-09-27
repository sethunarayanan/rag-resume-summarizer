## Resume Summarizer

### Status: Work in Progress — this project is primarily an experimentation with RAG, LangChain, and vector-based resume summarization.

RAG-Resume-Summarizer is a Dockerized web application that allows users to upload resumes (PDFs) and get concise summaries in real-time. Built with FastAPI, Streamlit, and WebSockets, it leverages ChromaDB and MongoDB for document storage and retrieval, while demonstrating Retrieval-Augmented Generation (RAG) workflows.

### Features
- Upload a single PDF resume.
- Process resumes asynchronously with:
  - Text extraction using PyPDF
  - Document chunking
  - Vector embeddings using LangChain + sentence-transformers
  - Summary generation using LangChain + HuggingFace LLM
- Receive real-time processing updates via WebSockets
- Interact with the application through a Streamlit frontend
- Partial bulk processing support (work in progress)

### Technologies Used

#### Backend: 
- FastAPI, asyncio
#### Frontend: 
- Streamlit
#### Databases / Storage:
  - MongoDB (metadata)
  - Chroma (vector embeddings)
#### Machine Learning / NLP:
  - LangChain (LLM chains & embeddings)
  - HuggingFace Transformers (flan-t5-small)
  - Sentence Transformers (all-MiniLM-L6-v2)
  - PyPDF (PDF text extraction)
#### WebSocket Communication: 
- FastAPI + Streamlit
#### Containerization & DevOps: 
  - Docker, Docker Compose
#### Observability / Logging: 
  - Elasticsearch, Kibana, Filebeat
#### Testing & API Tools: 
 - pytest, Postman
#### Documentation
 - Swagger UI (FastAPI)

### Docker Setup
- streamlit (frontend)
- fastapi (backend)
- mongo (metadata)
- chroma (vector DB)
- chroma_admin (Chroma UI)
- elasticsearch (logs & search)
- kibana (Elasticsearch UI)
- filebeat (log shipping)

### Start all services
```
docker-compose -f compose-local.yml up
```

### Future Features / Roadmap
- Parallel embedding & bulk processing optimization – Improve processing speed by handling multiple resume chunks or multiple resumes simultaneously.
- Real-time progress bar and partial summaries – Display a live progress indicator in Streamlit and show partial summaries while the full summary is being generated.
- Enhanced error handling – Better handling of exceptions in file upload, WebSocket communication, and backend processing to ensure smooth user experience.