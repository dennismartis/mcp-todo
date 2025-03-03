#!/usr/bin/env python
import asyncio
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("minimal-server")

@mcp.tool()
def hello_world() -> str:
    """A simple hello world tool"""
    return "Hello, world from minimal MCP server!"

if __name__ == "__main__":
    print("Starting MCP server...")
    mcp.run()
