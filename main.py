from dotenv import load_dotenv
from mem0 import Memory
from openai import OpenAI
import json
import os


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing in .env")

client = OpenAI(api_key=OPENAI_API_KEY)
GRAPH_ENABLED = False


def build_base_config() -> dict:
    return {
        "version": "v1.1",
        "embedder": {
            "provider": "openai",
            "config": {"api_key": OPENAI_API_KEY, "model": "text-embedding-3-small"},
        },
        "llm": {
            "provider": "openai",
            "config": {"api_key": OPENAI_API_KEY, "model": "gpt-4.1"},
        },
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "host": os.getenv("QDRANT_HOST", "localhost"),
                "port": int(os.getenv("QDRANT_PORT", "6333")),
            },
        },
    }


def build_full_config() -> dict:
    config = build_base_config()

    neo4j_url = os.getenv("NEO4J_CONNECTION") or os.getenv("NEO_CONNNECTION")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_database = os.getenv("NEO4J_DATABASE")

    if neo4j_url and neo4j_username and neo4j_password:
        graph_config = {
            "provider": "neo4j",
            "config": {
                "url": neo4j_url,
                "username": neo4j_username,
                "password": neo4j_password,
            },
        }
        if neo4j_database:
            graph_config["config"]["database"] = neo4j_database

        config["graph_store"] = graph_config

    return config


def init_memory_client() -> Memory:
    global GRAPH_ENABLED
    config = build_full_config()
    try:
        mem = Memory.from_config(config)
        GRAPH_ENABLED = "graph_store" in config
        return mem
    except Exception as exc:
        if "graph_store" in config:
            print(f"Warning: Neo4j unavailable ({exc}). Running with vector-only memory.")
            GRAPH_ENABLED = False
            return Memory.from_config(build_base_config())
        raise


def switch_to_vector_only(reason: Exception) -> None:
    global mem_client, GRAPH_ENABLED
    if not GRAPH_ENABLED:
        return

    print(f"Warning: Graph memory disabled due to runtime error: {reason}")
    mem_client = Memory.from_config(build_base_config())
    GRAPH_ENABLED = False


def safe_search(query: str):
    try:
        return mem_client.search(query=query, user_id="Srikartik")
    except Exception as exc:
        if GRAPH_ENABLED:
            switch_to_vector_only(exc)
            return mem_client.search(query=query, user_id="Srikartik")
        raise


def safe_add(user_query: str, ai_response: str) -> None:
    messages = [
        {"role": "user", "content": user_query},
        {"role": "assistant", "content": ai_response},
    ]
    try:
        mem_client.add(user_id="Srikartik", messages=messages)
    except Exception as exc:
        if GRAPH_ENABLED:
            switch_to_vector_only(exc)
            mem_client.add(user_id="Srikartik", messages=messages)
            return
        raise


mem_client = init_memory_client()


while True:
    user_query = input("> ").strip()
    if user_query.lower() == "exit":
        print("Thank you for using")
        break

    search_memory = safe_search(user_query)
    memories = [
        f"ID: {mem.get('id')}\\nMemory: {mem.get('memory')}"
        for mem in search_memory.get("results", [])
    ]

    system_prompt = f"""
    Here is the context about the user:
    {json.dumps(memories)}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
    )

    ai_response = response.choices[0].message.content
    print("AI:", ai_response)

    safe_add(user_query, ai_response)
    print("Memory has been saved...")