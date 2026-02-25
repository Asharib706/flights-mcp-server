import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from load_mcp import load_flight_tools


async def run_agent():
    """
    Sets up the LangGraph React Agent with Gemini and the MCP Flight tools,
    and runs an interactive chat loop where the human can converse with it.
    """
    
    # 1. Connect to Gemini API using 2.5 Pro
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        api_key="AIzaSyAUYYDbyEUd_W67FikxzqjEjoJG4lHR7mU",
        temperature=0.7
    )
    
    # Define a system prompt that guides the LLM to use the flight tools
    system_prompt = (
        "You are a helpful and professional travel assistant with access to flight search tools.\n\n"
        "GENERAL BEHAVIOR:\n"
        "- Be friendly, clear, and conversational.\n"
        "- Guide the user step-by-step when required information is missing.\n"
        "- Only call tools when all required parameters are confirmed.\n\n"
        "CRITICAL WORKFLOW RULES:\n"
        "1. ALWAYS call `get_current_date` FIRST before performing any flight search "
        "to ensure you are using the correct year and today's date context.\n\n"
        "2. Flight search tools require 3-letter IATA airport codes (e.g., 'SEA', 'HND').\n\n"
        "3. If the user provides a city or country instead of a specific airport:\n"
        "   - Use your own knowledge to identify the correct airport(s) and IATA codes.\n"
        "   - If you are unsure about the correct IATA code of a particular airport, THEN call `get_airport` to retrieve it.\n"
        "   - If multiple airports serve that area, present all matching options to the user.\n"
        "   - Ask the user to confirm the specific airport before proceeding.\n"
        "   - Do NOT call flight search tools until the airport is confirmed.\n\n"
        "4. ALL flight search tools REQUIRE a `departure_date` in 'YYYY-MM-DD' format.\n"
        "   - If the user does not provide a specific departure date, ask for it.\n"
        "   - NEVER call flight tools without a confirmed departure date.\n\n"
        "5. Only after confirming:\n"
        "   - Origin airport (IATA code)\n"
        "   - Destination airport (IATA code)\n"
        "   - Departure date (YYYY-MM-DD)\n"
        "   may you call a flight search tool such as `get_cheapest_flights` or `get_best_flights`.\n\n"
        "6. After receiving tool results, present them in a friendly, structured, and easy-to-read format.\n"
    )

    print("Initializing Gemini Agent...")

    # 2. Load the MCP tools using the separate file
    async with load_flight_tools() as tools:
        
        # 3. Create the LangGraph React Agent
        # The local version of langgraph accepts `prompt` for the system message
        agent_executor = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
        
        print("\n=== Agent Ready! ===")
        print("Type 'quit' or 'exit' to stop.\n")
        
        # 4. Interactive chat loop
        # We need to maintain a history of messages so the agent has memory!
        chat_history = []
        
        while True:
            try:
                user_msg = input("\nYou: ")
                if user_msg.lower() in ["quit", "exit"]:
                    print("Goodbye!")
                    break
                    
                if not user_msg.strip():
                    continue

                # Add the user's message to the conversation history
                chat_history.append(HumanMessage(content=user_msg))

                # Stream the agent's thought process and response
                inputs = {"messages": chat_history}
                
                print("\nAgent:")
                
                # Keep track of events happening in this turn to append them to history
                async for event in agent_executor.astream(inputs, stream_mode="values"):
                    message = event["messages"][-1]
                    
                    # Ensure we don't double-process the user message we just added
                    if message.type == "human" and message.content == user_msg:
                        continue
                        
                    if message.type == "ai":
                        if message.content:
                            print(f"{message.content}")
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            print(f"  [Tool Call]: Calling {message.tool_calls[0]['name']}...")
                    
                    elif message.type == "tool":
                        print(f"  [Tool Result]: {str(message.content)[:200]}...")
                
                # After the stream finishes, update our chat_history to match the final state
                # The agent_executor returns the full updated list of messages!
                chat_history = event["messages"]

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nOops, an error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(run_agent())
