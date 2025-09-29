"""Database models for storing LLM requests and responses."""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class LLMRequest(SQLModel, table=True):
    """Model for storing LLM API requests and responses."""

    __tablename__ = "llm_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    model: str = Field(index=True)

    # Request data
    messages: str = Field()  # JSON string of messages array (includes appended assistant response)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stream: bool = False
    functions: Optional[str] = None  # JSON string of functions if provided
    function_call: Optional[str] = None  # JSON string of function_call if provided
    tools: Optional[str] = None  # JSON string of tools if provided
    tool_choice: Optional[str] = None  # JSON string of tool_choice if provided

    # Response data
    response: Optional[str] = None  # JSON string of complete raw response
    response_time_ms: Optional[int] = None
    tool_calls: Optional[str] = None  # JSON string of tool_calls if present in response

    # Metadata
    api_key_hash: Optional[str] = None  # Hash of API key for tracking
    status: str = Field(default="ok", index=True)  # "ok" or "error"
    status_code: int = Field(default=200)
    error: Optional[str] = None