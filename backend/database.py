import boto3

def create_database_table(dynamodb=None):

    table_name = "UserData"

    # Check if table exists
    existing_tables = dynamodb.meta.client.list_tables()["TableNames"]
    if table_name in existing_tables:
        print(f"Table {table_name} already exists.")
        return dynamodb.Table(table_name)
    
    table = dynamodb.create_table(
        TableName='UserData',
        KeySchema=[
            {'AttributeName': 'UserID', 'KeyType': 'HASH'},  # Primary Key
            {'AttributeName': 'WorkoutID', 'KeyType': 'RANGE'}   # Sort Key
        ],
        AttributeDefinitions=[
            {'AttributeName': 'UserID', 'AttributeType': 'S'},  # String
            {'AttributeName': 'WorkoutID', 'AttributeType': 'S'}     # String
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table

def create_set_table(dynamodb=None):

    table_name = "SetData"

    # Check if table exists
    existing_tables = dynamodb.meta.client.list_tables()["TableNames"]
    if table_name in existing_tables:
        print(f"Table {table_name} already exists.")
        return dynamodb.Table(table_name)
    
    table = dynamodb.create_table(
        TableName='SetData',
        KeySchema=[
            {'AttributeName': 'WorkoutID', 'KeyType': 'HASH'},  # Primary Key
        ],
        AttributeDefinitions=[
            {'AttributeName': 'WorkoutID', 'AttributeType': 'S'},  # String
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table

def create_user_table(dynamodb=None):

    table_name = "Users"

    # Check if table exists
    existing_tables = dynamodb.meta.client.list_tables()["TableNames"]
    if table_name in existing_tables:
        print(f"Table {table_name} already exists.")
        return dynamodb.Table(table_name)

    table = dynamodb.create_table(
        TableName='Users',
        KeySchema=[
            {'AttributeName': 'UserID', 'KeyType': 'HASH'}  # Primary Key
        ],
        AttributeDefinitions=[
            {'AttributeName': 'UserID', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

    return table


def delete_table(table_name):
    # Delete table
    dynamodb=boto3.client('dynamodb',region_name='us-east-1')
    dynamodb.delete_table(TableName=table_name)
    print(f"Deleting table {table_name}...")
