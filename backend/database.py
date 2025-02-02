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


def delete_and_recreate_table(dynamodb, table_name):
    db_properties = dynamodb.describe_table(table_name)
    schema = db_properties["Table"]

    # Delete table
    try:
        dynamodb.delete_table(TableName=table_name)
        print(f"Deleting table {table_name}...")
        waiter = dynamodb.get_waiter("table_not_exists")
        waiter.wait(TableName=table_name)
        print(f"Table {table_name} deleted.")

    except dynamodb.exceptions.ResourceNotFoundException:
        print(f"Table {table_name} does not exist.")

    dynamodb.create_table(*schema)