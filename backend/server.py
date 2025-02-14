from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random
from database import create_database_table, create_user_table, delete_table, create_set_table
import boto3
from login import register_user, verify_user
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from analysis import calculate_lifetime_metrics, calculate_rep_qualities
import uuid
import pickle
import pandas as pd
import decimal
from decimal import Decimal

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests
app.config["JWT_SECRET_KEY"] = "supersecretkey"
jwt = JWTManager(app)

# Allows correct parsing from Float to Decimal
context = decimal.getcontext()
context.traps[decimal.Inexact] = False
context.traps[decimal.Rounded] = False

# Connect the DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Delete tables
#delete_table("UserData")
#delete_table("Users")
#delete_table("SetData")

# Create tables
workouts_table = dynamodb.Table("UserData")
users_table = dynamodb.Table("Users")
set_table = dynamodb.Table("SetData")

def initialize_tables():
    create_database_table(dynamodb)
    create_user_table(dynamodb)
    create_set_table(dynamodb)

# Global dictionaries to store the reps of all users, Pi IDs, and the last workouts IDs
global_reps = {}
user_pi_id={}
global_user_workouts={}


############ MOBILE APP ROUTES ############

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

@app.route("/api/analysis", methods=["GET"])
@jwt_required()
def get_analysis():
    current_user = get_jwt_identity()  # Get the logged-in user's ID
    workout_id=global_user_workouts.get(current_user)
    if workout_id is not None:
        # Query all workouts for the user, sorted by date
        response = set_table.query(
            KeyConditionExpression="WorkoutID = :id",
            ExpressionAttributeValues={":id": workout_id},
        )
        items = response.get("Items", [])
        if not items:
            return jsonify({"error": "No analysis found for this workout"}), 404
        return jsonify(items)
    else:
        return jsonify({"error": "No workout in progress"}), 404

########## MOBILE CONTROL LOGIC ##########

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
    database_response=database_response.get("Items", [])
    pi_id=database_response[0]['pi_id']
    workout_id=str(uuid.uuid4())
    global_reps[current_user] = {
        "pi_id":pi_id,
        "exercise": exercise,
        "reps": 0,
        "workout": True,
        "set": True,
        "workoutID": workout_id
    }
    user_pi_id[pi_id]=current_user
    global_user_workouts[current_user]=workout_id
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
    global_reps[current_user]['set']=False
    return jsonify("Workout Ended")


############ RASPBERRY PI ROUTES ############

@app.route("/api/rep", methods=["POST"])
def count_rep():
    try:
        data = request.json
        pi_id = data.get("pi_id")
        current_user = user_pi_id.get(pi_id)
        if current_user is None:
            return jsonify({"response": "Idle"})  # If pi_id is not found, return "Idle"
        global_reps[current_user]['reps'] += 1
        return jsonify({"response": "success"})
    except Exception as e:
        print(f"Error processing data: {e}")
        return jsonify({"error": "Failed to process data"}), 500

@app.route("/api/pipoll", methods=["POST"])
def pi_poll():
    try: 
        data = request.json
        current_user = user_pi_id.get(data)
        if current_user is None:
            return jsonify({"response": "Idle"})  # If pi_id is not found, return "Idle"
        if global_reps[current_user]['workout'] and global_reps[current_user]['set']:
            return jsonify({"response":global_reps[current_user]['exercise']})
        elif global_reps[current_user]['workout'] and global_reps[current_user]['set']==False:
            return jsonify({"response":"Pseudo Idle"})
        return jsonify({"response":"Idle"})
    except Exception as e:
        print(f"Error processing data: {e}")
        return jsonify({"error": "Failed to process data"}), 500

@app.route("/api/anal", methods=["POST"])
def analyse_data():
    try:
        data = request.json
        pi_id = data.get("pi_id")
        current_user = user_pi_id.get(pi_id)
        workout_id=global_reps[current_user]['workoutID']
        global_user_workouts[current_user]=workout_id
        set_count = data.get("set_count")
        overall_score = data.get("score")
        distance_score = data.get("distance_score")
        distance_feedback = data.get("distance_feedback")
        consistency_score = data.get("time_consistency_score")
        consistency_feedback = data.get("time_consistency_feedback")
        shakiness_score = data.get("shakiness_score")
        shakiness_feedback = data.get("shakiness_feedback")
        set_item = {
                "WorkoutID": workout_id,
                "set_count": set_count,
                "overall_score": Decimal(str(round(overall_score, ndigits=2))),
                "distance_score": Decimal(str(round(distance_score, ndigits=2))),
                "distance_feedback": distance_feedback,
                "time_consistency_score": Decimal(str(round(consistency_score, ndigits=2))),
                "time_consistency_feedback": consistency_feedback,
                "shakiness_score": Decimal(str(round(shakiness_score, ndigits=2))),
                "shakiness_feedback": shakiness_feedback
            }
        
        set_table.put_item(Item=set_item)
    except Exception as e:
        print(f"Error processing data: {e}")
        return jsonify({"error": "Failed to process data"}), 500
    return jsonify("success"), 200
    
@app.route("/api/process", methods=["POST"])
def process_data():
    try:
        # Parse incoming form data
        data = request.json

        workout_name = data.get('name')
        pi_id=data.get('pi_id')
        current_user = user_pi_id.get(pi_id)
        all_sets_data= data.get('sets_data')
        formatted_data={
            'accel_x': all_sets_data.get('accel_x'),
            'accel_y': all_sets_data.get('accel_y'),
            'accel_z': all_sets_data.get('accel_z'),
            'vel_x': all_sets_data.get('vel_x'),
            'vel_y': all_sets_data.get('vel_y'),
            'vel_z': all_sets_data.get('vel_z'),
            'pos_x': all_sets_data.get('pos_x'),
            'pos_y': all_sets_data.get('pos_y'),
            'pos_z': all_sets_data.get('pos_z'),
            'mag_x': all_sets_data.get('mag_x'),
            'mag_y': all_sets_data.get('mag_y'),
            'mag_z': all_sets_data.get('mag_z')
        }
        flattened = {f"{outer}_{inner}": list(value) 
             for outer, subdict in formatted_data.items() 
             for inner, value in subdict.items()}
        
        data_to_predict=pd.DataFrame(flattened)

        # Predict the rep quality using saved model weights
        if workout_name=="Seated Cable Rows":
            with open("seated_cable_rows.pkl", "rb") as file:
                model = pickle.load(file)
                rep_qualities=model.predict(data_to_predict)
        elif workout_name=="Lat Pulldowns":
            with open("lat_pulldowns.pkl", "rb") as file:
                model = pickle.load(file)
                rep_qualities=model.predict(data_to_predict)

        # Format as YYYY-MM-DD
        current_date = datetime.now()
        formatted_date = current_date.strftime('%Y-%m-%d')
        
        workout_id=global_reps[current_user]['workoutID']
       
        # Save the workout in the database

        int_qualities=[]
        for value in rep_qualities:
            int_qualities.append(int(value))

        workout_item = {
            "UserID": current_user,
            "WorkoutID": workout_id,
            "date": formatted_date,
            "exercise": workout_name,
            "rep_number": len(int_qualities),
            "rep_quality": int_qualities,
        }
        
        workouts_table.put_item(Item=workout_item)
        # Delete user data when workout is completed
        user_pi_id.pop(pi_id)
        global_reps.pop(current_user)
        # Respond with JSON
        return jsonify("success"), 200
    
    except Exception as e:
        print(f"Error processing data: {e}")
        return jsonify({"error": "Failed to process data"}), 500

if __name__ == "__main__":
    with app.app_context():
        initialize_tables()  # Call directly inside app context
    app.run(host="0.0.0.0", port=80)
