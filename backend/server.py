from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import random

# ssh -i "C:\Users\themi\Downloads\tradingbotkey.pem" ubuntu@18.170.31.251
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Mock workout data
def generate_rep_quality(min_val, max_val, num_reps=50):
    return [random.randint(min_val, max_val) for _ in range(num_reps)]

# Function to calculate total workout metrics
def calculate_lifetime_metrics(workouts):
    total_reps = sum(workout["rep_number"] for workout in workouts)
    total_workouts = len(workouts)
    total_calories = round(total_reps * 0.1, 2)  # Estimate: 0.1 calories per rep

    # Flatten all rep qualities into one list and compute average
    all_rep_qualities = [rep for workout in workouts for rep in workout["rep_quality"]]
    avg_rep_quality = round(sum(all_rep_qualities) / len(all_rep_qualities), 2) if all_rep_qualities else 0

    # Find best workout (highest avg rep quality)
    best_workout = max(workouts, key=lambda w: sum(w["rep_quality"]) / len(w["rep_quality"]))

    return {
        "total_reps": total_reps,
        "total_workouts": total_workouts,
        "total_calories_burned": total_calories,
        "lifetime_avg_rep_quality": avg_rep_quality,
        "best_workout": {
            "date": best_workout["date"],
            "exercise": best_workout["exercise"],
            "avg_rep_quality": round(sum(best_workout["rep_quality"]) / len(best_workout["rep_quality"]), 2)
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

# Create mock workouts
workouts = [
    {
        "id": i + 1,
        "date": (datetime(2025, 1, 22) + timedelta(days=i)).strftime("%Y-%m-%d"),
        "rep_number": 50,
        "exercise": "Triceps Extension",
        "rep_quality": generate_rep_quality(50 - (i * 5), 95 - (i * 5))
    }
    for i in range(5)
]


@app.route("/api/history", methods=["GET"])
def get_history():
    # Return the total workout history to be displayed in the graphs and the 
    return jsonify(workouts)

@app.route("/api/home", methods=["GET"])
def get_home():
    # Assuming workouts is a list of all past workout records
    last_workout = workouts[-1] if workouts else None

    if last_workout:
        # Process the rep_quality array
        workout_qualities = calculate_rep_qualities(last_workout)
        
        # Calculate lifetime metrics as you previously did
        metrics = calculate_lifetime_metrics(workouts)

        return jsonify({
            "lifetime_metrics": metrics,
            "last_workout": workout_qualities
        })
    else:
        return jsonify({"error": "No workouts available"}), 404


@app.route("/api/process", methods=["POST"])
def process_data():
    # Process the data using Hector's code based on raw data
    # Calculate the rep quality and store it in the database
    return 0


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
