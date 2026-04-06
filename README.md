# Enterprise Knowledge graph with llms

A lightweight CLI project for building an enterprise-style knowledge memory system with LLMs.
It combines:

- Vector memory (Qdrant)
- Optional graph memory (Neo4j)
- LLM-powered retrieval and response generation (OpenAI)

## What This Project Does

This app lets you chat in the terminal and automatically stores conversation memory.

- It searches prior memory before every response.
- It uses memory context to improve answers.
- It saves new user and assistant messages after each turn.
- It supports a graph + vector setup, and automatically falls back to vector-only mode if graph storage is unavailable.

## Architecture

- `main.py`: Main CLI loop and memory orchestration.
- `Qdrant`: Vector store for semantic memory.
- `Neo4j` (optional): Graph store for relationship-aware memory.
- `OpenAI`: Embeddings + chat completion.

## Prerequisites

- Python 3.10+
- Docker (for Qdrant)
- OpenAI API key
- (Optional) Neo4j instance for graph memory

## Setup

### 1. Install dependencies

```bash
pip install python-dotenv mem0 openai
```

### 2. Configure environment variables

Create/update `.env` in the project root:

```env
OPENAI_API_KEY=your_openai_api_key

# Qdrant (optional if using defaults)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Neo4j (optional)
NEO4J_CONNECTION=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

Note: The code also accepts `NEO_CONNNECTION` (legacy typo key) as a fallback for Neo4j URL.

### 3. Start Qdrant

```bash
docker compose up -d
```

## Run

```bash
python main.py
```

Type messages at the prompt.
Use `exit` to quit.

## Runtime Behavior

- If Neo4j settings are valid and reachable, graph memory is enabled.
- If Neo4j fails during startup or runtime, the app prints a warning and switches to vector-only memory.
- Memory is stored per user id currently hardcoded as `Srikartik` in `main.py`.

## Example Session

```text
> What do you know about my previous project?
AI: Based on your saved memory, you worked on...
Memory has been saved...

> exit
Thank you for using
```

## Notes for Enterprise Use

- Move hardcoded user id to auth/session context.
- Add structured logging and monitoring.
- Add retry and timeout policies for external services.
- Add access controls and encryption for production deployments.
- Add test coverage for memory fallback behavior.
