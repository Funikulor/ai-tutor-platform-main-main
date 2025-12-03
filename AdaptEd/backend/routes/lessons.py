from fastapi import APIRouter, HTTPException
from typing import List, Dict
import random

router = APIRouter()

# In-memory storage for math tasks of different difficulty levels
math_tasks = {
    "beginner": [
        {"id": 1, "question": "5 + 3", "answer": 8, "category": "addition"},
        {"id": 2, "question": "10 - 4", "answer": 6, "category": "subtraction"},
        {"id": 3, "question": "7 * 2", "answer": 14, "category": "multiplication"},
        {"id": 4, "question": "12 / 3", "answer": 4, "category": "division"},
        {"id": 5, "question": "8 + 7", "answer": 15, "category": "addition"},
        {"id": 6, "question": "15 - 9", "answer": 6, "category": "subtraction"},
    ],
    "intermediate": [
        {"id": 7, "question": "24 / 4 + 3", "answer": 9, "category": "mixed"},
        {"id": 8, "question": "5 * 3 - 4", "answer": 11, "category": "mixed"},
        {"id": 9, "question": "15 + 20 - 10", "answer": 25, "category": "mixed"},
        {"id": 10, "question": "7 * 4 / 2", "answer": 14, "category": "mixed"},
        {"id": 11, "question": "36 / 6 + 5", "answer": 11, "category": "mixed"},
        {"id": 12, "question": "8 * 2 - 9", "answer": 7, "category": "mixed"},
    ],
    "advanced": [
        {"id": 13, "question": "(12 + 8) / 4", "answer": 5, "category": "expression"},
        {"id": 14, "question": "3 * (5 + 2) - 1", "answer": 20, "category": "expression"},
        {"id": 15, "question": "(20 - 8) / 3", "answer": 4, "category": "expression"},
        {"id": 16, "question": "2 * 4 + 3 * 3", "answer": 17, "category": "expression"},
        {"id": 17, "question": "(15 + 5) / 2", "answer": 10, "category": "expression"},
        {"id": 18, "question": "5 * 3 - 2 * 4", "answer": 7, "category": "expression"},
    ]
}

@router.get("/tasks", response_model=List[Dict])
async def get_tasks(difficulty: str = "all"):
    """Get tasks filtered by difficulty level"""
    if difficulty == "all":
        all_tasks = []
        for task_list in math_tasks.values():
            all_tasks.extend(task_list)
        return all_tasks
    elif difficulty in math_tasks:
        return math_tasks[difficulty]
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid difficulty level. Choose from: {', '.join(['all'] + list(math_tasks.keys()))}"
        )

@router.get("/tasks/random", response_model=Dict)
async def get_random_task(difficulty: str = "beginner"):
    """Get a random task of specified difficulty"""
    if difficulty not in math_tasks:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid difficulty. Choose from: {', '.join(math_tasks.keys())}"
        )
    
    task = random.choice(math_tasks[difficulty])
    # Remove answer for security
    return {
        "id": task["id"],
        "question": task["question"],
        "category": task.get("category", "general"),
        "difficulty": difficulty
    }

@router.post("/tasks/check", response_model=Dict)
async def check_answer(task_id: int, user_answer: int):
    """Check if user's answer is correct"""
    # Search through all difficulty levels
    task = None
    for task_list in math_tasks.values():
        found_task = next((t for t in task_list if t["id"] == task_id), None)
        if found_task:
            task = found_task
            break
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    is_correct = task["answer"] == user_answer
    
    return {
        "task_id": task_id,
        "is_correct": is_correct,
        "correct_answer": task["answer"],
        "user_answer": user_answer,
        "feedback": "Excellent!" if is_correct else f"Not quite. Try again!"
    }

@router.get("/tasks/categories")
async def get_categories():
    """Get all available task categories"""
    categories = set()
    for task_list in math_tasks.values():
        for task in task_list:
            categories.add(task.get("category", "general"))
    return {"categories": sorted(list(categories))}