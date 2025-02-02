from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random
from database import create_database_table, create_user_table, delete_table
import boto3
from login import register_user, verify_user
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import uuid
import json

# ssh -i "C:\Users\themi\Downloads\piTrainerKey.pem" ubuntu@18.134.249.18
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests
app.config["JWT_SECRET_KEY"] = "supersecretkey"  # Change this in production!
jwt = JWTManager(app)

# Connect the DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
#delete_table("UserData")
#delete_table("Users")
workouts_table = dynamodb.Table("UserData")
users_table = dynamodb.Table("Users")

# Mock workout data
def generate_rep_quality(min_val, max_val, num_reps=50):
    output=[]
    for _ in range(num_reps):
        output.append(random.randint(min_val, max_val))
    return output

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


def generate_mock_data(email):
    # Create mock workouts
    workouts = [
    {
        "id": str(uuid.uuid4()) ,
        "date": (datetime(2025, 1, 15) + timedelta(days=i)).strftime("%Y-%m-%d"),
        "rep_number": 50,
        "exercise": "Triceps Extension",
        "rep_quality": generate_rep_quality(50 - (i * 5), 95 - (i * 5))
    }
    for i in range(5)
    ]
    for data in workouts:

        workout_item = {
            "UserID": email,  # Associate workout with logged-in user
            "WorkoutID": data['id'],
            "date": data["date"],
            "exercise": data["exercise"],
            "rep_number": data["rep_number"],
            "rep_quality": data["rep_quality"]
        }

        workouts_table.put_item(Item=workout_item)  # Store in DynamoDB
    return jsonify({"message": "Workout added successfully!"}), 201

def initialize_tables():
    create_database_table(dynamodb)
    create_user_table(dynamodb)



@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    # Check if email is already registered
    response = users_table.get_item(Key={"UserID": email})
    if "Item" in response:
        return jsonify({"error": "Email already exists"}), 400

    user_id=register_user(email, password, users_table)
    access_token = create_access_token(identity=email)
    generate_mock_data(email)
    print(f"Registered {email}!")
    return jsonify({"access_token": access_token}), 200

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    verify=verify_user(email, password, users_table)
    if verify == "Correct":
        access_token = create_access_token(identity=email)
        return jsonify({"access_token": access_token}), 200

    elif verify == "Wrong":
        return jsonify({"error": "Incorrect password. Please try again."}), 401  # Unauthorized

    else:
        return jsonify({"error": "Account does not exist. Please register."}), 404  # Not Found

@app.route("/api/history", methods=["GET"])
@jwt_required()
def get_history():
    # Return the total workout history to be displayed in the graphs and the 
    print(f"Authorization header: {request.headers.get('Authorization')}")
    current_user = get_jwt_identity()  # Get the logged-in user's ID
    print(current_user)
    workouts_table = dynamodb.Table("UserData")

    
    # Query all workouts for the user, sorted by date
    response = workouts_table.query(
        KeyConditionExpression="UserID = :user",
        ExpressionAttributeValues={":user": current_user},
        ScanIndexForward=True  # Sort workouts from oldest to newest
    )
    items = response.get("Items", [])
    print(type(items))
    if not items:
        return jsonify({"error": "No workouts found for this user"}), 404
    for workout in items:
        workout['rep_quality'] = [float(val) for val in workout['rep_quality']]
        workout['rep_number']=int(workout['rep_number'])
    print(items)
    return jsonify(items)

@app.route("/api/home", methods=["GET"])
@jwt_required()
def get_home():
    current_user = get_jwt_identity()  # Get the logged-in user's ID
    workouts_table = dynamodb.Table("UserData")

    # Query all workouts for the user, sorted by date
    response = workouts_table.query(
        KeyConditionExpression="UserID = :user",
        ExpressionAttributeValues={":user": current_user},
        ScanIndexForward=True  # Sort workouts from oldest to newest
    )
    items = response.get("Items", [])

    if not items:
        return jsonify({"error": "No workouts found for this user"}), 404
    # Process the rep_quality array
    workout_qualities = calculate_rep_qualities(items[-1])
        
    # Calculate lifetime metrics as you previously did
    metrics = calculate_lifetime_metrics(items)

    return jsonify({
        "lifetime_metrics": metrics,
        "last_workout": workout_qualities
    })


@app.route("/api/process", methods=["POST"])
@jwt_required()
def process_data():
    # Process the data using Hector's code based on raw data
    # Calculate the rep quality and store it in the database
    return 0

@app.route("/api/pipoll", methods=["GET"])
def pi_poll():
    # Tell the Pi whether a workout has been started
    return jsonify("Triceps Extension")

if __name__ == "__main__":
    with app.app_context():
        initialize_tables()  # Call directly inside app context
    app.run(host="0.0.0.0", port=80)
