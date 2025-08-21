from mcp.server.stdio import stdio_server
from mcp.server import Server

# Create server instance
server = Server("hexagon-api")

async def _main():
    async with stdio_server() as (reader, writer):


def main():
    import anyio
    anyio.run(_main)

def main():
    anyio.run(_main)


if __name__ == "__main__":
    main()
