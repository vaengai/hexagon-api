from typing import List, Optional, Dict, Any
from .http_client import _make_request, _init, _shutdown
import asyncio
from . import logger
from mcp.server.fastmcp import FastMCP


mcp = FastMCP(name="hexagon-mcp")


@mcp.tool(name="health", description="Hexagon API health check (/health)")
async def health(bearer_token: Optional[str] = None) -> Dict[str, Any]:
    """Check the health status of the Hexagon API."""
    logger.info("Health check requested")
    result = await _make_request("GET", "/health", bearer_token)

    if "error" not in result:
        logger.info("Health check completed successfully")
    return result


@mcp.tool(name="get_habits", description="List all habits for the authenticated user.")
async def get_habits(
    bearer_token: Optional[str] = None, skip: int = 0, limit: int = 100
) -> List[Dict[str, Any]]:
    """Retrieve all habits for the authenticated user."""
    logger.info(f"Getting habits with skip={skip}, limit={limit}")

    params = {"skip": skip, "limit": limit}
    result = await _make_request("GET", "/habit", bearer_token, params=params)

    if isinstance(result, dict) and "error" in result:
        # Defensive: though _make_request now raises, keep guard if older errors leak
        raise RuntimeError(result.get("error", "Unknown error"))
    if not isinstance(result, list):
        raise RuntimeError("Expected a list of habits from /habit endpoint")

    if "error" not in result:
        # Log summary info
        if isinstance(result, list):
            logger.info(f"Retrieved {len(result)} habits")
        else:
            logger.info(f"Retrieved habits data: {type(result)}")

    return result


@mcp.tool(
    name="create_habit", description="Create a new habit with all required fields."
)
async def create_habit(
    title: str,
    description: str,
    category: str,
    target: int,
    frequency: str,
    status: str = "Pending",
    active: bool = True,
    progress: int = 0,
    bearer_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new habit with all required fields."""
    logger.info(f"Creating new habit: '{title}' in category '{category}'")
    logger.debug(
        f"Habit details: {description}, target={target}, frequency={frequency}, status={status}, active={active}, progress={progress}"
    )

    data = {
        "title": title,
        "description": description,
        "category": category,
        "target": target,
        "frequency": frequency,
        "status": status,
        "active": active,
        "progress": progress,
    }
    result = await _make_request("POST", "/habit", bearer_token, json=data)

    if "error" not in result:
        habit_id = result.get("id", "unknown")
        logger.info(f"Successfully created habit '{title}' with ID: {habit_id}")

    return result


@mcp.tool(
    name="update_habit_status",
    description="Update a habit’s status: pending | in_progress | done.",
)
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


@mcp.tool(name="get_habit", description="Get a habit by its ID.")
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


@mcp.tool(name="toggle_habit_active", description="Toggle a habit’s active flag.")
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


@mcp.tool(name="delete_habit", description="Delete a habit by its ID.")
async def delete_habit(
    habit_id: str, bearer_token: Optional[str] = None
) -> Dict[str, Any]:
    """Delete a specific habit by its ID."""
    logger.info(f"Deleting habit: {habit_id}")
    logger.warning(f"DESTRUCTIVE ACTION: Deleting habit {habit_id}")

    endpoint = f"/habit/{habit_id}"
    result = await _make_request("DELETE", endpoint, bearer_token)

    if not isinstance(result, dict):
        raise RuntimeError("Expected an object response from DELETE /habit/{id}")

    if "error" not in result:
        logger.info(f"Successfully deleted habit: {habit_id}")
        result["message"] = "Habit deleted successfully"

    return result


@mcp.tool(
    name="get_user_profile",
    description="Return the user profile for the current session.",
)
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

    try:
        logger.info("MCP server starting...")
        asyncio.run(_init())
        mcp.run()
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server crashed: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("MCP server shutdown complete")
        asyncio.run(_shutdown())


if __name__ == "__main__":
    main()
