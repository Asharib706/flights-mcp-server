import asyncio
import os
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools


@asynccontextmanager
async def load_flight_tools():
    """
    Connects to the local flights.py MCP server and loads its tools 
    as LangChain tools. Yields the tools list so it can be used within the context.
    """
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "flights.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    print("Connecting to flights.py MCP Server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # Load the MCP tools as LangChain tools
            tools = await load_mcp_tools(session)
            print(f"Successfully loaded {len(tools)} tools from flights.py MCP server")
            
            yield tools
