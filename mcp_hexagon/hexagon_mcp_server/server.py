import os
import anyio
import httpx
from typing import Optional, Literal, Dict, Any, List

from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP


load_dotenv()

BASE_URL = os.getenv("HEXAGON_API_BASE_URL", "http://localhost:8000")
DEFAULT_BEARER = os.getenv("HEXAGON_API_BEARER")

mcp = FastMCP(name="hexagon-mcp")


def _auth_headers(bearer_override: Optional[str] = None) -> Dict[str, str]:
    token = bearer_override or DEFAULT_BEARER
    return {"Authorization": f"Bearer {token}"} if token else {}


def _client(headers: Optional[Dict[str, str]] = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=httpx.Timeout(30.0, read=30.0, connect=10.0),
        headers=headers or {},
    )


@mcp.tool(name="health", description="Hexagon API health check (/health)")
async def health(bearer_token: Optional[str] = None) -> Dict[str, Any]:
    async with _client(_auth_headers(bearer_token)) as client:
        r = await client.get("/health")
        r.raise_for_status()
        return r.json()


def main():
    """Entry point for the direct execution server."""
    mcp.run()


if __name__ == "__main__":
    main()
