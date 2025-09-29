"""FastAPI application for LLM intercept proxy."""

import hashlib
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from sqlmodel import Session, select
from sse_starlette.sse import EventSourceResponse

from .database import get_engine, init_db, get_session
from .models import LLMRequest
from .proxy import OpenAIProxy
from .admin import router as admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="LLM Intercept Proxy",
    description="Intercept and store LLM API calls for dataset collection",
    version="0.1.0",
)

# Include admin router
app.include_router(admin_router)

# Initialize database engine
engine = get_engine()


def get_base_url() -> str:
    """Get base URL for the target API from environment."""
    return os.getenv("BASE_URL", "https://openrouter.ai/api/v1/chat/completions")


def extract_assistant_message(response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract assistant message from response data.

    Returns the assistant message dict with content and optional tool_calls.
    """
    try:
        if not response_data or "choices" not in response_data:
            return None

        choices = response_data.get("choices", [])
        if not choices:
            return None

        message = choices[0].get("message")
        if not message:
            return None

        # Build assistant message
        assistant_msg = {
            "role": "assistant",
            "content": message.get("content", "")
        }

        # Add tool_calls if present
        if "tool_calls" in message and message["tool_calls"]:
            assistant_msg["tool_calls"] = message["tool_calls"]

        return assistant_msg
    except Exception as e:
        logger.error(f"Error extracting assistant message: {str(e)}")
        return None


def extract_tool_calls(response_data: Dict[str, Any]) -> Optional[str]:
    """Extract tool_calls from response data and return as JSON string."""
    try:
        if not response_data or "choices" not in response_data:
            return None

        choices = response_data.get("choices", [])
        if not choices:
            return None

        message = choices[0].get("message", {})
        tool_calls = message.get("tool_calls")

        if tool_calls:
            return json.dumps(tool_calls)
        return None
    except Exception as e:
        logger.error(f"Error extracting tool calls: {str(e)}")
        return None


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting LLM Intercept proxy server")
    logger.info(f"Target API: {get_base_url()}")
    init_db(engine)
    logger.info("Database initialized")


def get_db():
    """Dependency for database session."""
    with Session(engine) as session:
        yield session


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def extract_api_key(authorization: Optional[str]) -> str:
    """Extract API key from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    return authorization[7:]  # Remove "Bearer " prefix


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """
    OpenAI-compatible chat completions endpoint.
    Forwards requests to the configured base URL and stores them in the database.
    """
    # Extract API key
    api_key = extract_api_key(authorization)
    api_key_hash = hash_api_key(api_key)

    # Parse request body
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Extract parameters
    model = payload.get("model", "unknown")
    messages = payload.get("messages", [])
    temperature = payload.get("temperature")
    max_tokens = payload.get("max_tokens")
    top_p = payload.get("top_p")
    frequency_penalty = payload.get("frequency_penalty")
    presence_penalty = payload.get("presence_penalty")
    stream = payload.get("stream", False)
    functions = payload.get("functions")
    function_call = payload.get("function_call")
    tools = payload.get("tools")
    tool_choice = payload.get("tool_choice")

    logger.info(f"Received request - Model: {model}, Stream: {stream}, Messages: {len(messages)}")

    # Create proxy client
    base_url = get_base_url()
    proxy = OpenAIProxy(api_url=base_url)

    # Handle streaming vs non-streaming
    if stream:
        # For streaming, we need to collect the full response while streaming to client
        return await handle_streaming_request(
            proxy=proxy,
            payload=payload,
            api_key=api_key,
            api_key_hash=api_key_hash,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            functions=functions,
            function_call=function_call,
            tools=tools,
            tool_choice=tool_choice,
            db=db,
        )
    else:
        # Non-streaming request
        logger.info(f"Forwarding non-streaming request to {base_url}")
        response_data, response_time_ms, error = await proxy.forward_request(
            payload=payload,
            api_key=api_key,
            stream=False,
        )

        # Prepare messages with assistant response appended
        messages_with_response = messages.copy()
        status = "ok"
        tool_calls_json = None

        if error:
            logger.error(f"Error from upstream API: {error}")
            status = "error"
        else:
            logger.info(f"Received response in {response_time_ms}ms")

            # Extract and append assistant message
            assistant_msg = extract_assistant_message(response_data)
            if assistant_msg:
                messages_with_response.append(assistant_msg)
                logger.info(f"Appended assistant message to conversation")

            # Extract tool calls if present
            tool_calls_json = extract_tool_calls(response_data)
            if tool_calls_json:
                logger.info(f"Extracted tool calls from response")

        # Store in database
        db_request = LLMRequest(
            timestamp=datetime.utcnow(),
            model=model,
            messages=json.dumps(messages_with_response),
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stream=False,
            functions=json.dumps(functions) if functions else None,
            function_call=json.dumps(function_call) if function_call else None,
            tools=json.dumps(tools) if tools else None,
            tool_choice=json.dumps(tool_choice) if tool_choice else None,
            response=json.dumps(response_data) if response_data else None,
            response_time_ms=response_time_ms,
            tool_calls=tool_calls_json,
            api_key_hash=api_key_hash,
            status=status,
            status_code=200 if response_data else 500,
            error=error,
        )
        db.add(db_request)
        db.commit()
        logger.info(f"Stored request in database (ID: {db_request.id}, status: {status})")

        if error:
            raise HTTPException(status_code=500, detail=error)

        return JSONResponse(content=response_data)


async def handle_streaming_request(
    proxy: OpenAIProxy,
    payload: Dict[str, Any],
    api_key: str,
    api_key_hash: str,
    model: str,
    messages: list,
    temperature: Optional[float],
    max_tokens: Optional[int],
    top_p: Optional[float],
    frequency_penalty: Optional[float],
    presence_penalty: Optional[float],
    functions: Optional[Any],
    function_call: Optional[Any],
    tools: Optional[Any],
    tool_choice: Optional[Any],
    db: Session,
):
    """Handle streaming requests, collecting response while streaming to client."""
    import time as time_module
    from contextlib import asynccontextmanager

    logger.info(f"Forwarding streaming request to upstream API")

    collected_chunks = []
    start_time = datetime.utcnow()
    start_time_ms = time_module.time()
    error_occurred = None

    async def event_generator():
        nonlocal error_occurred
        try:
            chunk_count = 0
            async for chunk in proxy.forward_stream(payload, api_key):
                collected_chunks.append(chunk)
                chunk_count += 1
                yield chunk
            logger.info(f"Streaming completed - {chunk_count} chunks received")
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            error_occurred = str(e)
            error_chunk = f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            collected_chunks.append(error_chunk)
            yield error_chunk

    # Return the streaming response
    # Note: We store to DB in a background task after streaming starts
    response = EventSourceResponse(event_generator())

    # Store request in database immediately (without response yet)
    # For streaming, we store the request only (assistant message not appended for streaming)
    try:
        db_request = LLMRequest(
            timestamp=start_time,
            model=model,
            messages=json.dumps(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stream=True,
            functions=json.dumps(functions) if functions else None,
            function_call=json.dumps(function_call) if function_call else None,
            tools=json.dumps(tools) if tools else None,
            tool_choice=json.dumps(tool_choice) if tool_choice else None,
            response=None,  # Will be populated during/after streaming
            response_time_ms=None,  # Not available yet for streaming
            tool_calls=None,  # Not extracted for streaming responses
            api_key_hash=api_key_hash,
            status="ok" if not error_occurred else "error",
            status_code=200,
            error=error_occurred,
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        logger.info(f"Stored streaming request in database (ID: {db_request.id}, status: ok)")
    except Exception as e:
        logger.error(f"Failed to store request in database: {str(e)}")

    return response