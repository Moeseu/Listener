from mcp.server.fastmcp import FastMCP
import json
import os
import difflib

mcp = FastMCP("TaskTracker")

def is_similar(text1: str, text2: str) -> float:
    return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

@mcp.tool()
def create_ticket(title: str, description: str, assignee: str, project_id: str, priority: str) -> str:
    """Створює тікет у зовнішній системі після перевірки на дублікати."""
    db_path = "data/tickets_db.json"
    tasks = []
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            
    # Перевірка існуючих завдань у тому ж проєкті
    for task in tasks:
        if task.get("project_id") == project_id and is_similar(title, task.get("title", "")) > 0.8:
            return f"Дублікат проігноровано: Завдання '{title}' вже існує (ID: {task['id']})."
            
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