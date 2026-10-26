from mcp.server.fastmcp import FastMCP
import json
import os

# Ініціалізація сервера
mcp = FastMCP("TaskTracker")

@mcp.tool()
def create_ticket(title: str, description: str, assignee: str, project_id: str, priority: str) -> str:
    """Створює тікет у зовнішній системі."""
    db_path = "data/tickets_db.json"
    tasks = []
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            
    new_task = {
        "id": f"TICKET-{len(tasks) + 1}",
        "title": title,
        "description": description,
        "assignee": assignee,
        "project_id": project_id,
        "priority": priority,
        "status": "TODO"
    }
    tasks.append(new_task)
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
        
    return f"Тікет {new_task['id']} успішно експортовано."

if __name__ == "__main__":
    mcp.run(transport='stdio')