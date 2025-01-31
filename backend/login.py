import bcrypt
import boto3
import uuid
from datetime import datetime

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Function to create a new user
def register_user(email, password, users_table):
    user_id = str(uuid.uuid4())  # Generate unique user ID
    hashed_pw = hash_password(password)
    users_table.put_item(Item={
        "UserID": user_id,
        "UserEmail": email,
        "HashedPassword": hashed_pw,
        "CreatedAt": datetime.now().isoformat()
    })
    return user_id

def verify_user(email, password, users_table):
    response = users_table.scan(
        FilterExpression="UserEmail = :email",
        ExpressionAttributeValues={":email": email}
    )
    
    if not response["Items"]:
        return None  # User not found

    user = response["Items"][0]
    
    # Verify password
    if bcrypt.checkpw(password.encode('utf-8'), user["HashedPassword"].encode('utf-8')):
        return user["UserID"]  # Return user ID if successful
    else:
        return None 