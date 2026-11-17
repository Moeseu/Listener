import json
import os
from mcp.server.fastmcp import FastMCP
from src.config import TICKETS_DB_PATH

mcp = FastMCP("TaskTracker")


@mcp.tool()
def create_ticket(title: str, description: str, assignee: str, project_id: str,
                  priority: str, source: str = "") -> str:
    """Створює тікет у зовнішній системі."""
    tasks = []
    if os.path.exists(TICKETS_DB_PATH):
        with open(TICKETS_DB_PATH, "r", encoding="utf-8") as f:
            tasks = json.load(f)

    new_task = {
        "id": f"TICKET-{len(tasks) + 1}",
        "title": title,
        "description": description,
        "assignee": assignee,
        "project_id": project_id,
        "priority": priority,
        "status": "TODO",
        "source": source,
    }
    tasks.append(new_task)

    with open(TICKETS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    return f"Тікет {new_task['id']} успішно експортовано."


if __name__ == "__main__":
    mcp.run(transport="stdio")
