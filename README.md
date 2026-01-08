<p align="center">
  <img src="pathway_client/src/assets/logo.svg" alt="FinSight" height="64" />
</p>

<p align="center">
  <b>FinSight — Financial Document Intelligence Platform</b><br/>
  An agentic RAG system for financial documents with a modern web app, built to scale from demo mode to full LangGraph-powered analysis.
</p>

<p align="center">
  <a href="https://youtu.be/6lSDO5A-Eds">Demo Video</a> ·
  <a href="https://youtu.be/AZFCZrfKrAs">Architecture Video</a>
</p>

### What this project is

FinSight is an end-to-end, agentic Retrieval-Augmented Generation (RAG) system designed specifically for financial document workflows such as reading, searching, and interrogating 10‑K filings and other long-form financial PDFs. The core idea is to combine structured retrieval (vector search + metadata filters + relevance checks) with agentic reasoning (question decomposition, iterative refinement, and evaluation) so the system can handle complex finance questions that require grounded, source-aware answers. The repository includes the backend services, a Vite + React frontend for a full product experience, and the research-grade pipeline components used to implement and evaluate the RAG workflows.

This repo is intentionally organized to support two operating modes. In “full mode,” the LangGraph pipeline runs with external LLM and embedding providers to enable end-to-end document analysis. In “demo mode,” the application can run without API keys so that core product functionality (spaces, storage, uploads, chat UI, websockets, navigation) remains usable while the AI endpoints return a consistent “API key expired” response. This makes it easy to deploy a stable demo environment while keeping the architecture intact for later activation.

### Demo videos

<div align="center">
  <div>
    <iframe
      width="840"
      height="472"
      src="https://www.youtube.com/embed/6lSDO5A-Eds"
      title="FinSight Demo"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      allowfullscreen
    ></iframe>
  </div>

  <br />

  <div>
    <iframe
      width="840"
      height="472"
      src="https://www.youtube.com/embed/AZFCZrfKrAs"
      title="FinSight Architecture"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      allowfullscreen
    ></iframe>
  </div>

  <br />

<a href="https://youtu.be/6lSDO5A-Eds">Demo Video</a> ·
<a href="https://youtu.be/AZFCZrfKrAs">Architecture Video</a>

</div>

### High-level architecture

At a high level, the system follows a document→index→retrieve→reason→respond loop. Documents are ingested and parsed, embeddings are computed and stored in a vector store, and retrieval is performed using semantic similarity with optional metadata constraints (for example, company and fiscal year). The agentic layer orchestrates the flow across nodes and edges: decomposing questions into sub‑queries, performing targeted retrieval per sub‑query, grading document relevance, optionally pulling web evidence, generating an answer, and then evaluating the answer for quality and hallucinations. The UI is designed to feel like a production app: users create “spaces” (work contexts), upload files, browse storage, and chat with a websocket-driven experience for streaming responses.

### Repository layout

This repository contains both the research pipeline and the productized application:

```
.
├── nodes/                         # LangGraph nodes: retrieval, grading, generation, safety, HITL, etc.
├── edges/                         # LangGraph edges: decision logic between nodes
├── workflows/                     # End-to-end workflows (naive → advanced → final)
├── evaluation/                    # Evaluation pipelines and scripts
├── vector_store.py                # Vector store server and ingestion helpers
├── retriever.py                   # Retrieval client utilities (timeouts, robustness)
├── llm.py                         # LLM provider wiring (full mode)
├── embeddings.py                  # Embedding provider wiring (full mode)
├── state.py                       # State models for agentic iterations
├── utils.py                       # Shared workflow utilities
├── config.py                      # Configuration switches and defaults
├── pathway_server/                # FastAPI backend used by the product UI
└── pathway_client/                # Vite + React frontend (bun)
```

### Running the app (demo mode, no API keys required)

The current product UI and backend can run locally without LLM/RAG credentials. In this mode, AI chat responses return a consistent “API key expired” message while the rest of the system continues to work normally.

Backend (FastAPI):

```bash
cd pathway_server
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python -m uvicorn backend_server:app --host 0.0.0.0 --port 8000 --reload
```

Frontend (Vite + React):

```bash
cd pathway_client
bun install
bun run dev
```

Open the app at `http://localhost:5173`.

### Demo authentication

For demo deployments, the backend provides a simple, in-memory auth flow and the UI exposes a single “Use Demo Account” sign-in action. This is meant to keep the product experience cohesive without introducing database-backed user management until you’re ready to harden auth for production.

### Running the full RAG pipeline (requires API keys)

The research pipeline is built around LangGraph workflows that combine retrieval, reasoning, grading, and safety checks. When you provide API keys and enable the full mode configuration, the system can run end-to-end with embedding + LLM calls and optional web search. You can use the top-level scripts and the `nodes/`, `edges/`, and `workflows/` modules to experiment with different orchestration strategies and evaluation criteria, including metadata-based retrieval, decomposition, and hallucination-aware answer grading.

### Deployment notes (frontend + backend together)

For deployment, the most common pattern is to keep the backend private inside the same network as the frontend (or a reverse proxy) and expose only a single public entry point. In practice, this means the browser never needs a separately “public” backend hostname; instead, the frontend calls a relative `/api` path that is reverse-proxied to the backend service. This reduces surface area, simplifies CORS, and keeps internal services unexposed while still shipping a single cohesive application.
