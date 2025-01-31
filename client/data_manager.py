# Mock Data for Dashboard
user_metrics = {
    "Total Workouts": 15,
    "Calories Burned": 1200,
    "Total Reps": 450,
}
workout_history = [
    {"date": "2025-01-20", "exercise": "Triceps Extensions", "reps": 30},
    {"date": "2025-01-18", "exercise": "Lat Pulldowns", "reps": 25},
]

def update_dashboard_with_new_workout(exercise_name, reps_completed):
    global workout_history
    # Update user metrics
    user_metrics["Total Workouts"] += 1
    user_metrics["Total Reps"] += reps_completed[0]
    user_metrics["Calories Burned"] += reps_completed[0] * 5  # Mock calculation

    # Add to workout history
    workout_history.append({
        "date": "2025-01-22",  # Mock today's date
        "exercise": exercise_name,
        "reps": reps_completed,
    })
