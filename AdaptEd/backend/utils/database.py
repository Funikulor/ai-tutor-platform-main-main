from typing import Dict, Any

# Simulated in-memory storage
database: Dict[str, Any] = {
    "users": {},
    "tasks": {}
}

def add_user(user_id: str, user_data: Dict[str, Any]) -> None:
    database["users"][user_id] = user_data

def get_user(user_id: str) -> Dict[str, Any]:
    return database["users"].get(user_id, {})

def add_task(task_id: str, task_data: Dict[str, Any]) -> None:
    database["tasks"][task_id] = task_data

def get_task(task_id: str) -> Dict[str, Any]:
    return database["tasks"].get(task_id, {})

def get_all_users() -> Dict[str, Any]:
    return database["users"]

def get_all_tasks() -> Dict[str, Any]:
    return database["tasks"]