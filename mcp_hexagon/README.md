# Hexagon MCP Server

A Model Context Protocol (MCP) server for the Hexagon Habit Tracker API. This server allows Claude Desktop to interact with your Hexagon habit tracking system directly.

## Features

- ✅ **Health Check** - Monitor API status
- 📋 **Get Habits** - Retrieve all user habits with pagination
- ➕ **Create Habit** - Add new habits to track
- 🔄 **Update Status** - Change habit status (pending, in_progress, done)
- 👁️ **Get Single Habit** - Retrieve specific habit details
- 🔀 **Toggle Active** - Enable/disable habit tracking
- 🗑️ **Delete Habit** - Remove habits from the system
- 👤 **User Profile** - Get user information

## Prerequisites

- Python 3.11+
- Hexagon API running locally (default: `http://localhost:8000`)
- Claude Desktop application
- Valid Clerk JWT token for authentication

## Installation

1. **Clone and navigate to the MCP directory:**

   ```bash
   cd /path/to/hexagon-api/mcp_hexagon
   ```

2. **Install dependencies:**

   ```bash
   uv sync
   ```

3. **Create environment file:**

   ```bash
   cp .env.example .env
   ```

4. **Configure environment variables in `.env`:**
   ```env
   HEXAGON_API_BASE_URL=http://localhost:8000
   HEXAGON_API_BEARER=your_jwt_token_here
   ```

## Claude Desktop Configuration

### 1. Locate Claude Desktop Config

Find your Claude Desktop configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

### 2. Add MCP Server Configuration

Add the Hexagon MCP server to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hexagon": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/hexagon-api/mcp_hexagon",
        "hexagon-mcp"
      ],
      "env": {
        "HEXAGON_API_BASE_URL": "http://localhost:8000",
        "HEXAGON_API_BEARER": "your_fresh_jwt_token_here"
      }
    }
  }
}
```

**Alternative configuration (direct Python execution):**

```json
{
  "mcpServers": {
    "hexagon": {
      "command": "/path/to/hexagon-api/mcp_hexagon/.venv/bin/python",
      "args": ["/path/to/hexagon-api/mcp_hexagon/hexagon_mcp_server/server.py"],
      "env": {
        "HEXAGON_API_BASE_URL": "http://localhost:8000",
        "HEXAGON_API_BEARER": "your_fresh_jwt_token_here"
      }
    }
  }
}
```

### 3. Get Fresh JWT Token

Your JWT token expires regularly. To get a fresh token:

1. **From your frontend app:**
   - Open browser developer tools (F12)
   - Go to Network tab
   - Make any authenticated request
   - Copy the `Authorization` header value

2. **Using the token checker script:**
   ```bash
   python check_token.py
   ```

### 4. Restart Claude Desktop

After updating the configuration:

1. **Quit Claude Desktop** completely
2. **Restart Claude Desktop**
3. **Verify the connection** by asking Claude to check the health status

## Usage Examples

Once configured, you can interact with your habits through Claude Desktop:

### Basic Commands

```
"Check the health of my Hexagon API"
"Get all my habits"
"Show me my active habits"
"Create a new habit called 'Drink Water' with description 'Drink 8 glasses daily'"
"Update habit [habit-id] status to done"
"Delete the habit with ID [habit-id]"
```

### Advanced Queries

```
"What's my habit progress summary?"
"Show me habits I completed today"
"List all habits created in the last week"
"Toggle the active status of habit [habit-id]"
```

## Available Tools

| Tool                  | Description                    | Parameters                             |
| --------------------- | ------------------------------ | -------------------------------------- |
| `health`              | Check API health status        | `bearer_token` (optional)              |
| `get_habits`          | Get all habits with pagination | `bearer_token`, `skip`, `limit`        |
| `create_habit`        | Create a new habit             | `title`, `description`, `bearer_token` |
| `update_habit_status` | Update habit status            | `habit_id`, `status`, `bearer_token`   |
| `get_habit`           | Get specific habit by ID       | `habit_id`, `bearer_token`             |
| `toggle_habit_active` | Toggle habit active status     | `habit_id`, `bearer_token`             |
| `delete_habit`        | Delete a habit                 | `habit_id`, `bearer_token`             |
| `get_user_profile`    | Get user profile info          | `bearer_token` (optional)              |

## Troubleshooting

### Common Issues

1. **"Invalid token" or 401 errors:**
   - Your JWT token has expired
   - Get a fresh token from your frontend app
   - Update the `HEXAGON_API_BEARER` in your Claude config

2. **"Connection refused" errors:**
   - Make sure your Hexagon API is running on `http://localhost:8000`
   - Check the `HEXAGON_API_BASE_URL` in your configuration

3. **MCP server not found:**
   - Verify the file paths in your Claude config are correct
   - Make sure `uv` is installed and accessible
   - Try the alternative Python execution method

### Testing Locally

Test the MCP server directly:

```bash
# Test the server locally
uv run hexagon-mcp

# Test with curl (if API is running)
curl -X GET "http://localhost:8000/health"
```

### Debug Mode

Enable debug logging by modifying `server.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
