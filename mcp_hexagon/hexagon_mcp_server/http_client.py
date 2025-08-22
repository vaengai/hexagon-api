from typing import Optional, Dict, Any
from functools import wraps
import httpx
from dotenv import load_dotenv
import os
from . import logger

load_dotenv()

BASE_URL = os.getenv("HEXAGON_API_BASE_URL", "http://localhost:8000")
DEFAULT_BEARER = os.getenv("HEXAGON_API_BEARER")


_http_client: Optional[httpx.AsyncClient] = None


async def _init():
    logger.info(f"Base URL: {BASE_URL}")
    logger.info(f"Token configured: {'Yes' if DEFAULT_BEARER else 'No'}")

    if DEFAULT_BEARER:
        # Log token info safely
        token_preview = (
            f"***{DEFAULT_BEARER[-10:]}" if len(DEFAULT_BEARER) > 10 else "***"
        )
        logger.info(f"Token preview: {token_preview}")


def _auth_headers(bearer_override: Optional[str] = None) -> Dict[str, str]:
    token = bearer_override or DEFAULT_BEARER
    if not token:
        logger.error("No authentication token provided")
        raise ValueError(
            "No authentication token provided. Set HEXAGON_API_BEARER or pass bearer_token parameter."
        )

    # Log token info (safely)
    logger.debug(f"Using token: {'***' + token[-10:] if len(token) > 10 else '***'}")
    return {"Authorization": f"Bearer {token}"}


def _create_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        logger.debug(f"Creating singleton HTTP client for base URL: {BASE_URL}")
        _http_client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=httpx.Timeout(30.0, read=30.0, connect=10.0),
        )
    return _http_client


async def _make_request(
    method: str, endpoint: str, bearer_token: Optional[str] = None, **kwargs
) -> Any:
    """Make a safe HTTP request with proper client management."""
    try:
        headers = _auth_headers(bearer_token)
        client = _create_client()
        # Update headers for this request
        client.headers.update(headers)

        logger.debug(f"Making {method} request to {endpoint}")
        r = await client.request(method, endpoint, **kwargs)
        logger.debug(f"Response status: {r.status_code}")
        r.raise_for_status()

        # If there's no content, return a simple message
        if not r.content:
            return {"message": "Success"}

        # Return JSON as-is (can be object or array)
        return r.json()

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error {e.response.status_code} for {method} {endpoint}: {e.response.text}"
        )
        # Raise so the MCP client treats this as a tool error (not a schema-mismatched payload)
        raise RuntimeError(f"HTTP {e.response.status_code}: {e.response.text}") from e
    except httpx.RequestError as e:
        logger.error(f"Request error for {method} {endpoint}: {str(e)}")
        raise RuntimeError(f"Request failed: {str(e)}") from e
    except ValueError as e:
        logger.error(f"Auth error: {str(e)}")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error for {method} {endpoint}: {str(e)}", exc_info=True
        )
        raise


def safe_api_call(
    func,
):
    """Decorator to wrap API calls with error handling and logging."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Dict[str, Any]:
        func_name = func.__name__
        logger.info(f"Starting API call: {func_name}")
        logger.debug(f"Function args: {args}, kwargs: {kwargs}")

        try:
            result = await func(*args, **kwargs)
            logger.info(f"API call {func_name} completed successfully")
            logger.debug(
                f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'non-dict result'}"
            )
            return result

        except Exception as e:
            logger.error(f"Unexpected error in {func_name}: {str(e)}", exc_info=True)
            return {"error": f"Unexpected error: {str(e)}"}

    return wrapper


async def _shutdown():
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
