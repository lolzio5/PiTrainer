import bcrypt
import boto3
import uuid
from datetime import datetime

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Function to create a new user
def register_user(email, password, pi_id, users_table):
    hashed_pw = hash_password(password)
    users_table.put_item(Item={
        "UserID": email,
        "HashedPassword": hashed_pw,
        "pi_id": pi_id,
        "CreatedAt": datetime.now().isoformat()
    })
    return email

def verify_user(email, password, users_table):
    
    response = users_table.query(
        KeyConditionExpression="UserID = :user",
        ExpressionAttributeValues={":user": email},
    )
    items = response.get("Items", [])
    print(items)
    if not response["Items"]:
        return None  # User not found
    user = response["Items"][0]
    print(user)
    
    # Verify password
    if bcrypt.checkpw(password.encode('utf-8'), user["HashedPassword"].encode('utf-8')):
        return "Correct"
    else:
        return "Wrong"