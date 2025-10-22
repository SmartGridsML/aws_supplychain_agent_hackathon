# download_and_unzip_dataset.py

import os
import shutil
import zipfile
from pathlib import Path
import pandas as pd

def setup_kaggle_api():
    """Ensures the Kaggle API key is in the correct location."""
    kaggle_dir = Path.home() / '.kaggle'
    api_key_path = kaggle_dir / 'kaggle.json'

    if api_key_path.exists():
        print("✅ Kaggle API key already exists.")
        return

    print("🔑 Kaggle API key not found.")
    # Prompt the user for the path to their downloaded kaggle.json
    user_key_path_str = input("Please enter the full path to your downloaded kaggle.json file: ").strip()
    user_key_path = Path(user_key_path_str)

    if not user_key_path.is_file():
        print(f"❌ Error: The file was not found at '{user_key_path_str}'. Please try again.")
        exit()

    # Create the .kaggle directory if it doesn't exist
    kaggle_dir.mkdir(exist_ok=True)
    
    # Copy the key to the correct location
    shutil.copy(user_key_path, api_key_path)
    
    # Set permissions to be secure (required by Kaggle)
    os.chmod(api_key_path, 0o600)
    
    print(f"✅ Kaggle API key successfully set up at '{api_key_path}'")

def download_and_prepare_dataset():
    """Downloads, unzips, and prepares the DataCo dataset."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("❌ Error: 'kaggle' library not found. Please run 'pip install kaggle'.")
        return

    # --- Step 1: Authenticate ---
    api = KaggleApi()
    api.authenticate()
    
    dataset_id = 'shashwatwork/dataco-smart-supply-chain-for-big-data-analysis'
    download_path = Path('./dataset')
    download_path.mkdir(exist_ok=True)
    
    print(f"\n📥 Downloading dataset: {dataset_id}...")
    
    # --- Step 2: Download the dataset zip file ---
    api.dataset_download_files(dataset_id, path=download_path, quiet=False)
    
    zip_filename = 'dataco-smart-supply-chain-for-big-data-analysis.zip'
    zip_filepath = download_path / zip_filename
    
    if not zip_filepath.exists():
        print("❌ Download failed. Please check the dataset ID and your Kaggle credentials.")
        return
        
    print("📦 Unzipping dataset...")
    
    # --- Step 3: Unzip the file ---
    with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
        zip_ref.extractall(download_path)
        
    # --- Step 4: Clean up the zip file ---
    os.remove(zip_filepath)
    
    # --- Step 5: Verify the CSV file ---
    csv_filename = 'DataCoSupplyChainDataset.csv'
    csv_filepath = download_path / csv_filename
    
    if csv_filepath.exists():
        # Read the CSV to get its shape for confirmation
        df = pd.read_csv(csv_filepath, encoding='latin1', nrows=1)
        print(f"\n🎉 Success! Dataset ready.")
        print(f"   -> CSV File: '{csv_filepath}'")
        print(f"   -> It contains columns like: {', '.join(df.columns)}")
    else:
        print(f"❌ Error: Expected CSV file '{csv_filename}' not found after unzipping.")

if __name__ == "__main__":
    setup_kaggle_api()
    download_and_prepare_dataset()