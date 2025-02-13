# Function to calculate total workout metrics
def calculate_lifetime_metrics(workouts):
    total_reps = sum(workout["rep_number"] for workout in workouts)
    total_workouts = len(workouts)
    total_calories = round(float(total_reps) * 0.1, 2)  # Estimate: 0.1 calories per rep

    # Flatten all rep qualities into one list and compute average
    all_rep_qualities = [rep for workout in workouts for rep in workout["rep_quality"]]
    avg_rep_quality = round(sum(all_rep_qualities) / len(all_rep_qualities), 2) if all_rep_qualities else 0

    # Find best workout (highest avg rep quality)
    best_workout = max(workouts, key=lambda w: sum(w["rep_quality"]) / len(w["rep_quality"]))

    return {
        "total_reps": int(total_reps),
        "total_workouts": int(total_workouts),
        "total_calories_burned": float(total_calories),
        "lifetime_avg_rep_quality": float(avg_rep_quality),
        "best_workout": {
            "date": best_workout["date"],
            "exercise": best_workout["exercise"],
            "avg_rep_quality": float(round(sum(best_workout["rep_quality"]) / len(best_workout["rep_quality"]), 2))
        }
    }

def calculate_rep_qualities(last_workout):
    rep_quality = last_workout['rep_quality']
        
    # Initialize counters for each quality
    perfect_count = 0
    good_count = 0
    fair_count = 0
    poor_count = 0
        
    # Classify each rep into one of the quality categories
    for quality in rep_quality:
        if quality > 70:
            perfect_count += 1
        elif 60 <= quality <= 70:
            good_count += 1
        elif 50 <= quality < 60:
            fair_count += 1
        else:
            poor_count += 1
        
        # Structure the workout qualities in the required format
    return [
        {"quality": "Perfect", "reps": perfect_count},
        {"quality": "Good", "reps": good_count},
        {"quality": "Fair", "reps": fair_count},
        {"quality": "Poor", "reps": poor_count}
    ]