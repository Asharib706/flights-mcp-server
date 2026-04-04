import os
from contextlib import AsyncExitStack, asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools


@asynccontextmanager
async def load_all_tools():
    """
    Connects to both the flights.py and hotels.py MCP servers sequentially
    and loads their tools as LangChain tools. Yields the combined tools list.
    """
    repo_dir = os.path.dirname(os.path.abspath(__file__))

    flights_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "flights.py"],
        cwd=repo_dir,
    )

    hotels_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "hotels.py"],
        cwd=repo_dir,
    )

    async with AsyncExitStack() as stack:
        print("Connecting to flights.py MCP Server...")
        f_read, f_write = await stack.enter_async_context(stdio_client(flights_params))
        flights_session = await stack.enter_async_context(ClientSession(f_read, f_write))
        await flights_session.initialize()
        flight_tools = await load_mcp_tools(flights_session)
        print(f"Loaded {len(flight_tools)} tools from flights.py")

        print("Connecting to hotels.py MCP Server...")
        h_read, h_write = await stack.enter_async_context(stdio_client(hotels_params))
        hotels_session = await stack.enter_async_context(ClientSession(h_read, h_write))
        await hotels_session.initialize()
        hotel_tools = await load_mcp_tools(hotels_session)
        print(f"Loaded {len(hotel_tools)} tools from hotels.py")

        all_tools = flight_tools + hotel_tools
        print(f"Total tools available: {len(all_tools)}")
        yield all_tools


# Backwards-compatible alias for any code still importing load_flight_tools
load_flight_tools = load_all_tools
