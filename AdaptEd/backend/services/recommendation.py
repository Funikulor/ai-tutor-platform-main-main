from typing import List, Dict
from datetime import datetime

class RecommendationService:
    def __init__(self):
        self.user_data = {}
        self.user_history = {}

    def add_user_data(self, user_id: str, answers: List[int], task_results: List[Dict] = None):
        """Store user answers and results"""
        if user_id not in self.user_data:
            self.user_data[user_id] = []
            self.user_history[user_id] = []
        
        self.user_data[user_id] = answers
        
        if task_results:
            self.user_history[user_id].extend(task_results)
            self.user_history[user_id].append({
                "timestamp": datetime.now().isoformat(),
                "results": task_results
            })

    def analyze_performance(self, user_id: str) -> Dict:
        """Analyze user performance and provide insights"""
        if user_id not in self.user_data:
            return {"error": "User data not found."}

        history = self.user_history.get(user_id, [])
        
        # Calculate statistics
        total_tasks = len(history)
        correct_answers = sum(1 for entry in history 
                             for result in entry.get('results', []) 
                             if result.get('is_correct', False))
        
        accuracy = (correct_answers / total_tasks * 100) if total_tasks > 0 else 0
        
        # Determine difficulty level based on performance
        if accuracy >= 80:
            difficulty_level = "advanced"
            next_difficulty = "Keep challenging yourself!"
        elif accuracy >= 60:
            difficulty_level = "intermediate"
            next_difficulty = "You're doing great! Try more challenging problems."
        else:
            difficulty_level = "beginner"
            next_difficulty = "Focus on fundamentals before advancing."
        
        return {
            "accuracy": round(accuracy, 2),
            "total_tasks": total_tasks,
            "correct_answers": correct_answers,
            "difficulty_level": difficulty_level,
            "recommendation": next_difficulty,
            "timestamp": datetime.now().isoformat()
        }

    def get_recommendations(self, user_id: str) -> Dict:
        """Get personalized recommendations for the user"""
        performance = self.analyze_performance(user_id)
        
        if "error" in performance:
            return performance
        
        recommendations = []
        
        if performance["accuracy"] < 60:
            recommendations.append({
                "priority": "high",
                "category": "practice",
                "message": "Focus on basic arithmetic operations",
                "suggested_topics": ["Addition", "Subtraction", "Multiplication", "Division"]
            })
        elif performance["accuracy"] < 80:
            recommendations.append({
                "priority": "medium",
                "category": "improvement",
                "message": "Practice mixed operations and word problems",
                "suggested_topics": ["Mixed operations", "Word problems", "Estimation"]
            })
        else:
            recommendations.append({
                "priority": "low",
                "category": "maintenance",
                "message": "Excellent progress! Try advanced topics",
                "suggested_topics": ["Fractions", "Decimals", "Basic algebra"]
            })
        
        return {
            **performance,
            "recommendations": recommendations
        }

    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user statistics"""
        if user_id not in self.user_data:
            return {"error": "User data not found."}
        
        history = self.user_history.get(user_id, [])
        
        stats = {
            "total_sessions": len(history),
            "performance_trend": [],
            "best_subject": "Math (currently only subject)",
            "areas_to_improve": []
        }
        
        # Calculate trend from recent history
        if len(history) >= 3:
            recent_results = [entry.get('results', []) for entry in history[-3:]]
            trend = []
            for session_results in recent_results:
                session_correct = sum(1 for r in session_results if r.get('is_correct', False))
                trend.append(session_correct / len(session_results) if session_results else 0)
            stats["performance_trend"] = trend
        
        return stats