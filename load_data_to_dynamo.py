# load_data_to_dynamodb.py

import pandas as pd
import boto3
from decimal import Decimal
import json
import numpy as np
import os

# --- Configuration ---
CSV_FILE_PATH = 'dataset/DataCoSupplyChainDataset.csv'
TABLE_NAME = 'supply_chain_data'
AWS_REGION = 'us-east-1'  # Change to your preferred region
NUM_ROWS_TO_LOAD = 5000 # Keep this small for a quick demo setup

def clean_data_for_dynamodb(row):
    """
    Cleans a pandas Series object to be compatible with DynamoDB's JSON format.
    - Converts numpy types to native Python types.
    - Replaces NaN/NaT with None, which will be stripped by DynamoDB.
    - Converts floats to Decimal for precision.
    """
    # Convert the row to a dictionary
    item = row.to_dict()
    
    # Use json.dumps with a custom handler to clean the data
    # This is a robust way to handle various data types (datetime, numpy int/float, etc.)
    cleaned_item = json.loads(json.dumps(item, default=str), parse_float=Decimal)

    # Remove empty strings and None values, as DynamoDB doesn't like them
    return {k: v for k, v in cleaned_item.items() if v is not None and v != ""}

def load_data():
    """Reads data from a CSV and loads it into a DynamoDB table."""
    
    if not os.path.exists(CSV_FILE_PATH):
        print(f"❌ Error: The file was not found at '{CSV_FILE_PATH}'.")
        print("Please download the DataCo dataset and place it in the correct directory.")
        return

    print("📖 Reading and preparing CSV data...")
    # Use latin1 encoding as the file has special characters
    df = pd.read_csv(CSV_FILE_PATH, encoding='latin1')
    
    # --- Data Preparation ---
    # Select a subset of columns relevant for the demo
    columns_to_keep = [
        'Order Id', 'Order Status', 'Delivery Status', 'Late_delivery_risk',
        'Customer City', 'Customer Country', 'Order Region',
        'Product Name', 'Category Name', 'Shipping Mode',
        'Days for shipment (scheduled)', 'Days for shipping (real)', 'Order Item Total'
    ]
    df = df[columns_to_keep]
    
    # Rename columns to be more code-friendly (no spaces)
    df.columns = [
        'order_id', 'order_status', 'delivery_status', 'late_delivery_risk',
        'customer_city', 'customer_country', 'order_region',
        'product_name', 'product_category', 'shipping_mode',
        'scheduled_shipping_days', 'actual_shipping_days', 'order_item_total'
    ]

    # Take a small subset for the hackathon demo
    df_subset = df.head(NUM_ROWS_TO_LOAD)
    
    # Remove duplicates based on order_id to match DynamoDB primary key constraint
    df_subset = df_subset.drop_duplicates(subset=['order_id'], keep='first')
    df_subset = df_subset.reset_index(drop=True)

    print(f"✅ Data prepared. Ready to load {len(df_subset)} unique rows into DynamoDB.")

    # --- DynamoDB Loading ---
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table(TABLE_NAME)

        print(f"🚀 Starting upload to DynamoDB table: '{TABLE_NAME}'...")
        # Use batch_writer for efficient bulk uploads
        with table.batch_writer() as batch:
            for index, row in df_subset.iterrows():
                if 'order_id' in row and pd.notna(row['order_id']):
                    item_to_load = clean_data_for_dynamodb(row)
                    # Ensure order_id is a string for DynamoDB
                    item_to_load['order_id'] = str(item_to_load['order_id'])
                    
                    batch.put_item(Item=item_to_load)
                
                if (index + 1) % 100 == 0:
                    print(f"   ... {index + 1}/{len(df_subset)} rows processed.")

        print("🎉 Success! All items have been loaded into DynamoDB.")
        print(f"💡 Note: Removed duplicate order_ids to match table schema.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        print("   Please check your AWS credentials and DynamoDB table configuration.")

if __name__ == "__main__":
    load_data()