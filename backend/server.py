from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random
from database import create_database_table, create_user_table, delete_table
import boto3
from login import register_user, verify_user
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import uuid
import pickle
import pandas as pd
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

# Global dictionary to store the reps of all users
global_reps = {}
user_pi_id={}

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

# Routes for the mobile app
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    pi_id=data.get("pi_id")

    # Check if email is already registered
    response = users_table.get_item(Key={"UserID": email})
    if "Item" in response:
        return jsonify({"error": "Email already exists"}), 400

    user_id=register_user(email, password, pi_id, users_table)
    access_token = create_access_token(identity=email)
    #generate_mock_data(email)
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
    for workout in items:
        workout['rep_quality'] = [float(val) for val in workout['rep_quality']]
        workout['rep_number']=int(workout['rep_number'])

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
    sorted_items = sorted(items, key=lambda x: x['date'], reverse=True)

    # Process the rep_quality array of the most recent workout
    most_recent_workout = sorted_items[0]
    workout_qualities = calculate_rep_qualities(most_recent_workout)
        
    # Calculate lifetime metrics as you previously did
    metrics = calculate_lifetime_metrics(items)
    result={
        "lifetime_metrics": metrics,
        "last_workout": workout_qualities
    }
    return jsonify(result)

@app.route("/api/start", methods=["POST"])
@jwt_required()
def start_workout():
    data = request.json
    current_user = get_jwt_identity() 
    exercise = data.get('exercise_name')
    database_response = users_table.query(
        KeyConditionExpression="UserID = :user",
        ExpressionAttributeValues={":user": current_user},
    )
    database_response = database_response.get("Items", [])
    pi_id=database_response[0]['pi_id']
    global_reps[current_user] = {
        "pi_id":pi_id,
        "exercise": exercise,
        "reps": 0,
        "workout": True,
        "set": True
    }
    user_pi_id[pi_id]=current_user
    return jsonify(global_reps[current_user]['reps'])

@app.route("/api/reps", methods=["GET"])
@jwt_required()
def get_reps():
    current_user = get_jwt_identity()
    reps=global_reps[current_user]['reps']
    return jsonify(reps)

@app.route("/api/end_set", methods=["GET"])
@jwt_required()
def end_set():
    current_user = get_jwt_identity()
    # Reset the reps
    global_reps[current_user]['reps']=0
    global_reps[current_user]['set']=False
    return jsonify(global_reps[current_user]['reps'])

@app.route("/api/start_set", methods=["GET"])
@jwt_required()
def start_set():
    current_user = get_jwt_identity()
    # Reset the reps
    global_reps[current_user]['reps']=0
    global_reps[current_user]['set']=True
    return jsonify({"response": global_reps[current_user]['reps']})

@app.route("/api/end", methods=["GET"])
@jwt_required()
def end_workout():
    current_user = get_jwt_identity()
    global_reps[current_user]['workout']=False
    return jsonify("Workout Ended")

# Routes for the Pi
@app.route("/api/rep", methods=["POST"])
def count_rep():
    data = request.json
    pi_id = data.get("pi_id")
    rep_count = data.get("reps")
    current_user = user_pi_id.get(pi_id)
    if current_user is None:
        return jsonify({"response": "Idle"})  # If pi_id is not found, return "Idle"
    global_reps[current_user]['reps'] = rep_count
    return jsonify({"response": "success"})

@app.route("/api/pipoll", methods=["POST"])
def pi_poll():
    pi_id = request.json
    current_user = user_pi_id.get(pi_id)
    if current_user is None:
        return jsonify({"response": "Idle"})  # If pi_id is not found, return "Idle"
    if global_reps[current_user]['workout'] and global_reps[current_user]['set']:
        return jsonify({"response":global_reps[current_user]['exercise']})
    elif global_reps[current_user]['set']==False:
        return jsonify({"response":"Pseudo Idle"})
    return jsonify({"response":"Idle"})

@app.route("/api/process", methods=["POST"])
def process_data():
    try:
        # Parse incoming form data
        data = request.form.to_dict()

        workout_name = data.get('Name')
        rep_number = data.get('Rep Number')
        email = data.get('Email')
        pi_id=data.get('pi_id')
        formatted_data={
            'accel_x': data.get('accel_x'),
            'accel_y': data.get('accel_y'),
            'accel_z': data.get('accel_z'),
            'vel_x': data.get('vel_x'),
            'vel_y': data.get('vel_y'),
            'vel_z': data.get('vel_z'),
            'pos_x': data.get('pos_x'),
            'pos_y': data.get('pos_y'),
            'pos_z': data.get('pos_z'),
            'mag_x': data.get('mag_x'),
            'mag_y': data.get('mag_y'),
            'mag_z': data.get('mag_z')
        }
        data_to_predict=pd.Dataframe(formatted_data)

        # Debug print to verify data (can be removed in production)
        print(f"Received data from user {email}: {data_to_predict}")
        
        # Predict the rep quality using saved model weights
        if workout_name=="Seated Cable Rows":
            model = pickle.load("seated_cable_rows.pkl")
            rep_qualities=model.predict(data_to_predict)
        elif workout_name=="Lat Pulldowns":
            model = pickle.load("lat_pulldowns.pkl")
            rep_qualities=model.predict(data)

        # Format as YYYY-MM-DD
        current_date = datetime.now()
        formatted_date = current_date.strftime('%Y-%m-%d')
        
        # Save the workout in the database
        workout_item = {
            "UserID": email,
            "WorkoutID": str(uuid.uuid4()),
            "date": formatted_date,
            "exercise": workout_name,
            "rep_number": rep_number,
            "rep_quality": rep_qualities
        }
        workouts_table.put_item(Item=workout_item)
        # Delete user data when workout is completed
        user_pi_id.pop(pi_id)
        global_reps.pop(email)

        # Respond with JSON
        return jsonify("success"), 200
    except Exception as e:
        print(f"Error processing data: {e}")
        return jsonify({"error": "Failed to process data"}), 500

if __name__ == "__main__":
    with app.app_context():
        initialize_tables()  # Call directly inside app context
    app.run(host="0.0.0.0", port=80)