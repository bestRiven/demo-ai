import pandas as pd
import os
import boto3
from botocore import UNSIGNED
from botocore.client import Config

def download_data_from_s3():
    """
    Downloads the required datasets from public AWS S3 buckets if they don't already exist.
    - NOAA GSOD (Global Surface Summary of the Day) for Chicago O'Hare.
    - OpenAQ data for Chicago (PM2.5 and O3).
    """
    print("Checking for required data files...")
    os.makedirs('data', exist_ok=True)
    
    # Initialize S3 client for public access
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    
    # --- File 1: NOAA GSOD Weather Data ---
    noaa_bucket = 'noaa-gsod-pds'
    noaa_key = '2024/725300-94846.csv' # Chicago O'Hare International Airport for 2024
    noaa_local_path = os.path.join('data', 'noaa-chicago-2024.csv')
    
    if not os.path.exists(noaa_local_path):
        print(f"Downloading NOAA data from s3://{noaa_bucket}/{noaa_key}...")
        try:
            s3.download_file(noaa_bucket, noaa_key, noaa_local_path)
            print("NOAA data download complete.")
        except Exception as e:
            print(f"Error downloading NOAA data: {e}")
            raise
    else:
        print("NOAA data already exists.")

    # --- File 2: OpenAQ Air Quality Data (using v2 parquet for efficiency) ---
    openaq_bucket = 'openaq-v2-post-etl-bucket'
    # Download PM2.5 and O3 data for Chicago for a few months in 2023
    openaq_local_path = os.path.join('data', 'openaq-chicago-2024.parquet')
    
    if not os.path.exists(openaq_local_path):
        print("Downloading OpenAQ data for Chicago (this may take a moment)...")
        try:
            # For this prototype, we'll fetch PM2.5 data for a few months and save it.
            # In a real scenario, you'd query a wider range of data.
            keys_to_download = [
                'data/v2/measures/parquet/city=Chicago/month=2024-01/parameter=pm25/',
                'data/v2/measures/parquet/city=Chicago/month=2024-02/parameter=pm25/',
                'data/v2/measures/parquet/city=Chicago/month=2024-01/parameter=o3/',
                'data/v2/measures/parquet/city=Chicago/month=2024-02/parameter=o3/'
            ]
            
            all_files = []
            paginator = s3.get_paginator('list_objects_v2')
            for prefix in keys_to_download:
                pages = paginator.paginate(Bucket=openaq_bucket, Prefix=prefix)
                for page in pages:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            all_files.append(obj['Key'])
            
            if not all_files:
                raise Exception("No OpenAQ files found for the specified paths.")

            df_list = []
            for i, key in enumerate(all_files):
                print(f"  Downloading part {i+1}/{len(all_files)}: {key}")
                obj = s3.get_object(Bucket=openaq_bucket, Key=key)
                df_list.append(pd.read_parquet(obj['Body']))

            full_df = pd.concat(df_list, ignore_index=True)
            full_df.to_parquet(openaq_local_path)
            print("OpenAQ data download and consolidation complete.")
        except Exception as e:
            print(f"Error downloading OpenAQ data: {e}")
            raise
    else:
        print("OpenAQ data already exists.")

def prepare_data():
    """
    Reads the downloaded data, cleans it, merges it, performs feature engineering,
    and saves the final dataset.
    """
    # Step 1: Ensure data is downloaded
    # download_data_from_s3()

    print("\nStarting data preparation and feature engineering...")
    
    # Step 2: Load and process OpenAQ data
    openaq_df = pd.read_csv(os.path.join('data', 'openaq_chicago_sample.csv'))
    openaq_df['date'] = pd.to_datetime(openaq_df['date.utc']).dt.date
    aq_pivot = openaq_df.pivot_table(index='date', columns='parameter', values='value', aggfunc='mean').reset_index()
    
    # Step 3: Load and process NOAA data
    noaa_df = pd.read_csv(os.path.join('data', 'noaa_gsod_chicago_sample.csv'))
    noaa_df['date'] = pd.to_datetime(noaa_df['DATE']).dt.date
    
    # Step 4: Merge data
    final_df = pd.merge(aq_pivot, noaa_df, on='date', how='inner')
    final_df = final_df.drop(columns=['DATE', 'STATION', 'LATITUDE', 'LONGITUDE', 'ELEVATION', 'NAME'])

    # Step 5: Clean and handle missing values
    # We select key columns and fill missing values
    features_to_keep = ['date', 'pm25', 'o3', 'TEMP', 'WDSP', 'PRCP']
    final_df = final_df[features_to_keep]
    final_df.ffill(inplace=True)
    final_df.bfill(inplace=True)

    # Step 6: Advanced Feature Engineering
    print("Performing feature engineering...")
    final_df.set_index('date', inplace=True)
    final_df.index = pd.to_datetime(final_df.index)
    
    # Create rolling average features
    rolling_features = ['pm25', 'o3', 'TEMP', 'WDSP']
    for feature in rolling_features:
        # Calculate 7-day rolling mean, shift by 1 to prevent data leakage (use past data to predict future)
        final_df[f'{feature}_7d_mean'] = final_df[feature].rolling(window=7, min_periods=1).mean().shift(1)
    
    # Create time-based features
    final_df['month'] = final_df.index.month
    final_df['day_of_year'] = final_df.index.dayofyear
    final_df['weekday'] = final_df.index.weekday
    
    final_df.reset_index(inplace=True)
    final_df.dropna(inplace=True) # Drop rows with NaNs created by rolling features

    # Step 7: Save final data
    output_path = os.path.join('data', 'final_data.csv')
    final_df.to_csv(output_path, index=False)
    
    print(f"Data preparation complete. Final data with engineered features saved to {output_path}")
    print("\nFinal Data Head:")
    print(final_df.head())

if __name__ == '__main__':
    prepare_data() 