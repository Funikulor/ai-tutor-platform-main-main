from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    user_id: str
    answers: List[Optional[int]] = []  # List to store user answers, can be integers or None for unanswered questions
    progress: float = 0.0  # Progress percentage from 0 to 100
    completed_tasks: int = 0  # Number of tasks completed by the user

    def update_answers(self, new_answers: List[Optional[int]]):
        self.answers = new_answers
        self.completed_tasks = sum(1 for answer in new_answers if answer is not None)
        self.progress = (self.completed_tasks / len(new_answers)) * 100 if new_answers else 0.0