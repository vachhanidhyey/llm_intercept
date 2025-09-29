"""Proxy client for forwarding requests to OpenAI-compatible APIs."""

import json
import time
from typing import AsyncIterator, Dict, Any, Optional
import httpx


class OpenAIProxy:
    """Handles forwarding requests to OpenAI-compatible API endpoints."""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.timeout = httpx.Timeout(300.0, connect=10.0)

    async def forward_request(
        self,
        payload: Dict[str, Any],
        api_key: str,
        stream: bool = False,
    ) -> tuple[Optional[Dict[str, Any]], int, Optional[str]]:
        """
        Forward request to OpenAI-compatible API.

        Returns:
            tuple: (response_data, response_time_ms, error)
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    # For streaming, we'll return None and handle streaming separately
                    return None, 0, None
                else:
                    response = await client.post(
                        self.api_url,
                        json=payload,
                        headers=headers,
                    )
                    response_time_ms = int((time.time() - start_time) * 1000)

                    if response.status_code == 200:
                        return response.json(), response_time_ms, None
                    else:
                        error = f"HTTP {response.status_code}: {response.text}"
                        return None, response_time_ms, error

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return None, response_time_ms, str(e)

    async def forward_stream(
        self,
        payload: Dict[str, Any],
        api_key: str,
    ) -> AsyncIterator[str]:
        """
        Forward streaming request to OpenAI-compatible API.

        Yields:
            str: SSE formatted chunks
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                self.api_url,
                json=payload,
                headers=headers,
            ) as response:
                async for chunk in response.aiter_text():
                    yield chunk