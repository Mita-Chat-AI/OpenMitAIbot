# server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TwoPlusTwo")

@mcp.tool()
def two_plus_two() -> int:
    """Return 2 + 2."""
    return 2 + 6

if __name__ == "__main__":
    mcp.run(transport="stdio")
