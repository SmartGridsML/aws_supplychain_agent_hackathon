# create_table.py
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

try:
    table = dynamodb.create_table(
        TableName='supply_chain_data',
        KeySchema=[
            {'AttributeName': 'order_id', 'KeyType': 'HASH'}  # Partition key
        ],
        AttributeDefinitions=[
            {'AttributeName': 'order_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    print("⏳ Waiting for table 'supply_chain_data' to be created...")
    table.wait_until_exists()
    print("✅ Table created successfully!")
except Exception as e:
    if "Table already exists" in str(e):
        print("ℹ️ Table 'supply_chain_data' already exists.")
    else:
        print(f"❌ Error creating table: {e}")