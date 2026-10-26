import sys
import os
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def export_tasks_via_mcp(action_items):
    # Гарантований абсолютний шлях до сервера
    server_script = os.path.abspath("src/mcp_server.py")
    
    # Передаємо копію поточних змінних середовища для збереження ізоляції .venv
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy() 
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            for task in action_items:
                result = await session.call_tool(
                    "create_ticket",
                    arguments={
                        "title": task.title,
                        "description": task.description,
                        "assignee": task.assignee or "Unassigned",
                        "project_id": task.project_id or "NONE",
                        "priority": task.priority
                    }
                )
                print(f"MCP Сервер відповідає: {result.content[0].text}")