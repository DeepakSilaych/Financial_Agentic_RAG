# Multi-Agent RAG System - Pathway High Prep

[Final Report](./final_report.pdf)

## Running Instructions

1. Run the vector store: `python vector_store.py`
2. Run the log server: `python log_server.py`
3. Run the cache server: `python semantic_server.py`
4. Run the backend server: `python backend_server.py`
5. Install the deps for the frontend: `npm install`
6. Run the frontend server: `npm run dev`

## 1. Introduction

This project implements a RAG pipeline using the LangGraph framework, designed for efficiently analyzing financial documents, specifically 10-K filings. The RAG approach combines information retrieval and language generation to provide comprehensive answers to user queries. The repository consists of custom nodes, edges, and workflows that enable seamless document processing, metadata extraction, question decomposition, and answer generation.

## 2. Project Overview

The RAG pipeline leverages various components to deliver a robust and extensible solution for financial document analysis. The key elements of the project are:

### 2.1. Nodes

The `nodes/` directory contains the core processing units, known as "nodes," that handle specific tasks within the RAG workflow. These nodes encapsulate the logic for document grading, document reranking, document retrieval, answer generation, metadata extraction, question decomposition, question rewriting, web searching, hallucination grading, answer grading, human-in-the-loop query clarification, query refinement, metadata formatting, and safety checking.

### 2.2. Edges

The `edges/` directory defines the decision-making logic, or "edges," that govern the connections between the nodes and the overall workflow. These scripts determine the flow of the RAG process, including sending decomposed questions, assessing document relevance, handling clarifying questions, evaluating hallucinations, and modifying queries for safety compliance.

### 2.3. Workflows

The `workflows/` directory contains the predefined RAG workflows that combine the nodes and edges to address different use cases. These include a naive RAG workflow, a workflow with document relevance and answer grading, a workflow with metadata-based document filtering, a workflow with question decomposition, and the comprehensive final workflow that integrates all the features.

### 2.4. Evaluation

The `evaluation/` directory houses the `eval.py` script, which defines the evaluation pipeline for benchmarking the performance of the RAG system across various metrics.

### 2.5. Supporting Components

The project also includes several supporting components:

1. **Vector Store**: The `vector_store.py` script defines the custom vector store client, metadata extraction logic, and the setup for the vector store server.
2. **State Management**: The `state.py` script introduces two classes, `OverallState` and `InternalRAGState`, to track the overall query flow and the internal state during a specific RAG iteration, respectively.
3. **Retriever Customization**: The `retriever.py` script customizes the vector store client with timeout mechanisms, extending the `PathwayVectorClient` for better control over retrieval operations.
4. **LLM and Embeddings Setup**: The `llm.py` and `embeddings.py` scripts set up the LLM (GPT-4) and embeddings (OpenAI) components used throughout the pipeline.
5. **Utilities**: The `utils.py` script provides utility functions for workflow visualization and logging.
6. **Entry Point**: The `main.py` script serves as the entry point for the RAG pipeline, handling user interactions and managing the overall process flow.

## 3. Directory Structure

The project directory structure is organized as follows:

```
├── nodes/
├── edges/
├── workflows/
├── evaluation/
├── vector_store.py
├── state.py
├── retriever.py
├── llm.py
├── config.py
├── embeddings.py
├── utils.py
├── main.py
├── data/
├── logs/
├── .env.example
├── requirements.txt
└── Dockerfile
```

A detailed breakdown of each directory and file is provided in the subsequent sections.

## 4. Components and Functionality

### 4.1. Nodes

The `nodes/` directory contains the following scripts, each responsible for a specific task within the RAG workflow:

1. **document_grader.py**: Evaluates the relevance of retrieved documents.
2. **document_retriever.py**: Retrieves documents using vector-based search, with or without metadata filtering.
3. **answer_generator.py**: Generates answers based on the retrieved documents.
4. **metadata_extractor.py**: Extracts metadata (e.g., company name, fiscal year) from documents.
5. **question_decomposer.py**: Decomposes complex questions into simpler sub-questions.
6. **question_rewriter.py**: Rewrites questions for improved clarity or generates alternative queries using a Hyde-based approach.
7. **web_searcher.py**: Performs web searches for additional information.
8. **hallucination_grader.py**: Evaluates the generated answers for potential hallucinations.
9. **answer_grader.py**: Assesses the quality of the generated answers.
10. **HITL_query_clarifier.py**: Handles human-in-the-loop interactions for asking clarifying questions.
11. **query_refiner.py**: Refines the initial query based on user input or feedback.
12. **format_metadata.py**: Converts metadata into JMESPath format for further processing.
13. **safety_checker.py**: Checks the query and response for safety and compliance.

### 4.2. Edges

The `edges/` directory contains the following scripts, which define the decision-making logic between the nodes:

1. **decomposed_questions.py**: Manages the flow of decomposed questions through the pipeline.
2. **docs_relevance.py**: Assesses the relevance of retrieved documents before using them in answer generation.
3. **clarifying_questions.py**: Determines if clarifying questions should be asked based on query ambiguity.
4. **hallucination_check.py**: Evaluates if the generated answer may contain hallucinations.
5. **modify_query_for_safety.py**: Decides if the query needs modification for safety compliance.

### 4.3. Workflows

The `workflows/` directory contains the following scripts, each implementing a distinct RAG workflow:

1. **naive_rag.py**: A basic retrieval-augmented generation workflow without advanced filtering.
2. **with_doc_relevance_and_answer_grader.py**: Incorporates document relevance checks and answer grading.
3. **with_metadata_filtering.py**: Filters documents based on extracted metadata before answer generation.
4. **with_question_decomposition.py**: Decomposes complex questions and handles them iteratively.
5. **final_workflow.py**: The comprehensive workflow combining all features, including metadata extraction, question decomposition, and hallucination grading.

### 4.4. Evaluation

The `evaluation/` directory contains:

1. **eval.py**: This script defines the evaluation pipeline for benchmarking the performance of the RAG system across various metrics. We use LLM-based evaluators for aspects like correctness and helpfulness, using custom prompts and grading configurations. Evaluators such as `EntityPrecision`, `EntityRecall`, and `EntityF1` use entity extraction to score predicted answers based on accuracy, useful for short and objective responses. We also plan to evaluate the quality of RAG pipeline through `RAGASEvaluator`.

### 4.5. Supporting Components

1. **vector_store.py**:

   - **FinancialStatementSchema**: A Pydantic model for storing extracted metadata (e.g., company name and year).
   - **CustomOpenParse**: An extension of Pathway's `OpenParse` parser using `pypdf` and LLM-based extraction.
   - **VectorStoreServer**: Sets up a server for document storage and retrieval with embeddings.

2. **state.py**:

   - **OverallState**: Manages the overall query flow, including sub-questions, answers, and clarifications.
   - **InternalRAGState**: Tracks the internal state during a specific RAG iteration, including retrieved documents and flags for hallucinations.

3. **retriever.py**:

   - Customizes the vector store client with timeout mechanisms, extending `PathwayVectorClient` for better control over retrieval operations.

4. **llm.py**:
   - Sets up the LLM instance using GPT-4.
   ```python
   llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
   ```
5. **embeddings.py**:

   - Configures embeddings using the OpenAI model.

   ```python
   embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
   ```

6. **utils.py**:

   - Provides utility functions for visualizing workflows and logging pipeline activities.

7. **main.py**:
   - The entry point for the RAG pipeline, handling user interaction and managing the overall process flow.

## 5. Setup and Deployment

```
# Environment Setup
cp .env.example .env
# Edit .env to include your API keys (OPENAI_API_KEY, TAVILY_API_KEY, LANGCHAIN_API_KEY)

# change config.py according to your requirements
# specify host, ports, data directories, cache directories

# Install dependencies
pip install -r requirements.txt
# For a non-GPU setup
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Client Setup
cd client
npm install
npm run dev

# Run Vector Store in a new terminal
cd server
python -m vector_store

# Run the main application in a new terminal
python main.py

# Open in browser
# Go to http://localhost:3000/
```

This flexibility allows you to experiment with different workflow configurations and evaluate their performance based on your specific requirements.

### 5.3. Docker Setup

The project also includes a `Dockerfile` for containerizing the application. Check `pathway_server/README.md` for more information.

## 6. Logging and Outputs

The project generates logs during execution, which are stored in the `logs/` directory. The following log files are created:

1. **pipeline_logs.txt**: Contains logs for the overall state of the RAG process.
2. **question_group{ID}.txt**: Stores logs for individual question group pipelines when parallel processing is enabled.

The input 10-K financial documents are stored in the `data/` directory.
