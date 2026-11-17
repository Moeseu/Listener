import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.config import BASE_DIR


async def export_tasks_via_mcp(action_items, source: str = ""):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.mcp_server"],   # запуск як модуль, щоб працював імпорт src.config
        env=os.environ.copy(),
        cwd=str(BASE_DIR),
    )
    replies = []
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
                        "priority": task.priority,
                        "source": source,
                    },
                )
                text = result.content[0].text
                print(f"   MCP: {text}")
                replies.append(text)
    return replies
