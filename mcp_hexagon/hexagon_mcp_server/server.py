import os
import httpx
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "hexagon_mcp.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler(LOG_FILE),  # File output
    ],
)

logger = logging.getLogger("hexagon-mcp")

load_dotenv()

BASE_URL = os.getenv("HEXAGON_API_BASE_URL", "http://localhost:8000")
DEFAULT_BEARER = os.getenv("HEXAGON_API_BEARER")

mcp = FastMCP(name="hexagon-mcp")

# Singleton HTTP client - created only when needed
_http_client: Optional[httpx.AsyncClient] = None


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


async def _get_client() -> httpx.AsyncClient:
    """Get or create the singleton HTTP client."""
    global _http_client

    if _http_client is None:
        logger.info(f"Creating HTTP client for base URL: {BASE_URL}")
        _http_client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=httpx.Timeout(30.0, read=30.0, connect=10.0),
        )
        logger.debug("HTTP client created successfully")
    else:
        logger.debug("Reusing existing HTTP client")

    return _http_client


async def _make_request(
    method: str, endpoint: str, bearer_token: Optional[str] = None, **kwargs
) -> Dict[str, Any]:
    """Make a safe HTTP request with shared client."""
    try:
        headers = _auth_headers(bearer_token)
        client = await _get_client()

        logger.debug(f"Making {method} request to {endpoint}")
        r = await client.request(method, endpoint, headers=headers, **kwargs)
        logger.debug(f"Response status: {r.status_code}")
        r.raise_for_status()

        # Handle different response types
        if r.content:
            result = r.json()
        else:
            result = {"message": "Success"}

        return result

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error {e.response.status_code} for {method} {endpoint}: {e.response.text}"
        )
        return {
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "status_code": e.response.status_code,
        }
    except httpx.RequestError as e:
        logger.error(f"Request error for {method} {endpoint}: {str(e)}")
        return {"error": f"Request failed: {str(e)}"}
    except ValueError as e:
        logger.error(f"Auth error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(
            f"Unexpected error for {method} {endpoint}: {str(e)}", exc_info=True
        )
        return {"error": f"Unexpected error: {str(e)}"}


async def _close_client():
    """Close the HTTP client when shutting down."""
    global _http_client
    if _http_client is not None:
        logger.info("Closing HTTP client")
        await _http_client.aclose()
        _http_client = None


def safe_api_call(
    func: Callable[..., Awaitable[Dict[str, Any]]],
) -> Callable[..., Awaitable[Dict[str, Any]]]:
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


@mcp.tool(name="health", description="Hexagon API health check (/health)")
async def health(bearer_token: Optional[str] = None) -> Dict[str, Any]:
    """Check the health status of the Hexagon API."""
    logger.info("Health check requested")
    result = await _make_request("GET", "/health", bearer_token)

    if "error" not in result:
        logger.info("Health check completed successfully")

    return result


@mcp.tool()
async def get_habits(
    bearer_token: Optional[str] = None, skip: int = 0, limit: int = 100
) -> Dict[str, Any]:
    """Retrieve all habits for the authenticated user."""
    logger.info(f"Getting habits with skip={skip}, limit={limit}")

    params = {"skip": skip, "limit": limit}
    result = await _make_request("GET", "/habit", bearer_token, params=params)

    if "error" in result:
        return result

    # API returns a plain array, wrap it in a structured response
    if isinstance(result, list):
        habits_data = result
        logger.info(f"Retrieved {len(habits_data)} habits")

        # Count active vs inactive habits
        active_habits = [h for h in habits_data if h.get("active", False)]
        inactive_habits = [h for h in habits_data if not h.get("active", False)]

        # Count by status
        status_counts = {}
        for habit in habits_data:
            status = habit.get("status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "success": True,
            "total_habits": len(habits_data),
            "active_habits_count": len(active_habits),
            "inactive_habits_count": len(inactive_habits),
            "status_breakdown": status_counts,
            "habits": habits_data,
            "pagination": {"skip": skip, "limit": limit, "returned": len(habits_data)},
            "message": f"Successfully retrieved {len(habits_data)} habits",
        }
    else:
        logger.warning(f"Unexpected response type: {type(result)}")
        return {
            "error": f"Expected array but got {type(result)}",
            "raw_response": str(result)[:200],
        }


@mcp.tool()
async def get_active_habits(bearer_token: Optional[str] = None) -> Dict[str, Any]:
    """Get only active habits with summary information."""
    logger.info("Getting active habits only")

    # Get all habits first
    all_habits_result = await get_habits(bearer_token, skip=0, limit=1000)

    if "error" in all_habits_result:
        return all_habits_result

    # Filter for active habits
    all_habits = all_habits_result.get("habits", [])
    active_habits = [habit for habit in all_habits if habit.get("active", False)]

    # Group by status
    pending = [h for h in active_habits if h.get("status") == "Pending"]
    done = [h for h in active_habits if h.get("status") == "Done"]
    in_progress = [h for h in active_habits if h.get("status") == "In Progress"]

    # Group by category
    categories = {}
    for habit in active_habits:
        category = habit.get("category", "Unknown")
        if category not in categories:
            categories[category] = []
        categories[category].append(habit)

    return {
        "success": True,
        "active_habits": active_habits,
        "summary": {
            "total_active": len(active_habits),
            "pending": len(pending),
            "done": len(done),
            "in_progress": len(in_progress),
            "categories": {cat: len(habits) for cat, habits in categories.items()},
        },
        "by_status": {"pending": pending, "done": done, "in_progress": in_progress},
        "by_category": categories,
        "message": f"Found {len(active_habits)} active habits",
    }


@mcp.tool()
async def create_habit(
    title: str, description: str, bearer_token: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new habit with the given title and description."""
    logger.info(f"Creating new habit: '{title}'")
    logger.debug(f"Habit description: {description}")

    data = {"title": title, "description": description}
    result = await _make_request("POST", "/habit", bearer_token, json=data)

    if "error" not in result:
        habit_id = result.get("id", "unknown")
        logger.info(f"Successfully created habit '{title}' with ID: {habit_id}")

    return result


@mcp.tool()
async def update_habit_status(
    habit_id: str, status: str, bearer_token: Optional[str] = None
) -> Dict[str, Any]:
    """Update the status of a specific habit (pending, in_progress, done)."""
    logger.info(f"Updating habit {habit_id} status to '{status}'")

    # Validate inputs
    if not habit_id or not habit_id.strip():
        logger.warning("Empty habit_id provided")
        return {"error": "habit_id is required and cannot be empty"}

    valid_statuses = ["pending", "in_progress", "done"]
    if status not in valid_statuses:
        logger.warning(f"Invalid status '{status}' provided")
        return {"error": f"Invalid status. Must be one of: {valid_statuses}"}

    endpoint = f"/habit/{habit_id}/status/{status}"
    result = await _make_request("PATCH", endpoint, bearer_token)

    if "error" not in result:
        logger.info(f"Successfully updated habit {habit_id} status to '{status}'")

    return result


@mcp.tool()
async def get_habit(
    habit_id: str, bearer_token: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve a specific habit by its ID."""
    logger.info(f"Getting habit details for ID: {habit_id}")

    endpoint = f"/habit/{habit_id}"
    result = await _make_request("GET", endpoint, bearer_token)

    if "error" not in result:
        habit_title = result.get("title", "unknown")
        logger.info(f"Successfully retrieved habit '{habit_title}' (ID: {habit_id})")

    return result


@mcp.tool()
async def toggle_habit_active(
    habit_id: str, bearer_token: Optional[str] = None
) -> Dict[str, Any]:
    """Toggle the active/inactive status of a habit."""
    logger.info(f"Toggling active status for habit: {habit_id}")

    endpoint = f"/habit/{habit_id}/toggle-active"
    result = await _make_request("PATCH", endpoint, bearer_token)

    if "error" not in result:
        new_status = result.get("active", "unknown")
        logger.info(
            f"Successfully toggled habit {habit_id} active status to: {new_status}"
        )

    return result


@mcp.tool()
async def delete_habit(
    habit_id: str, bearer_token: Optional[str] = None
) -> Dict[str, Any]:
    """Delete a specific habit by its ID."""
    logger.info(f"Deleting habit: {habit_id}")
    logger.warning(f"DESTRUCTIVE ACTION: Deleting habit {habit_id}")

    endpoint = f"/habit/{habit_id}"
    result = await _make_request("DELETE", endpoint, bearer_token)

    if "error" not in result:
        logger.info(f"Successfully deleted habit: {habit_id}")
        result["message"] = "Habit deleted successfully"

    return result


@mcp.tool()
async def get_user_profile(bearer_token: Optional[str] = None) -> Dict[str, Any]:
    """Get the user's profile information."""
    logger.info("Getting user profile")

    result = await _make_request("GET", "/profile", bearer_token)

    if "error" not in result:
        user_id = result.get("id", "unknown")
        logger.info(f"Successfully retrieved profile for user: {user_id}")

    return result


def main():
    """Entry point for the direct execution server."""
    logger.info("Starting Hexagon MCP Server")
    logger.info(f"Base URL: {BASE_URL}")
    logger.info(f"Token configured: {'Yes' if DEFAULT_BEARER else 'No'}")

    if DEFAULT_BEARER:
        # Log token info safely
        token_preview = (
            f"***{DEFAULT_BEARER[-10:]}" if len(DEFAULT_BEARER) > 10 else "***"
        )
        logger.info(f"Token preview: {token_preview}")

    try:
        logger.info("MCP server starting...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server crashed: {str(e)}", exc_info=True)
        raise
    finally:
        # Clean up the HTTP client on shutdown
        import asyncio

        if _http_client is not None:
            asyncio.create_task(_close_client())
        logger.info("MCP server shutdown complete")


if __name__ == "__main__":
    main()
