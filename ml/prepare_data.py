import pandas as pd
import os

def prepare_data():
    """
    Reads raw sample data from OpenAQ and NOAA, cleans it, merges it,
    and saves it to a final CSV file ready for model training.
    """
    print("Starting data preparation...")

    # Define file paths
    openaq_path = os.path.join('data', 'openaq_chicago_sample.csv')
    noaa_path = os.path.join('data', 'noaa_gsod_chicago_sample.csv')
    output_path = os.path.join('data', 'final_data.csv')

    # --- Load and Process OpenAQ Data ---
    try:
        aq_df = pd.read_csv(openaq_path)
    except FileNotFoundError:
        print(f"Error: Could not find {openaq_path}")
        return

    # Convert to datetime and keep only the date part
    aq_df['date'] = pd.to_datetime(aq_df['date.utc']).dt.date
    
    # Pivot the table to have pollutants as columns
    aq_pivot = aq_df.pivot_table(index='date', columns='parameter', values='value', aggfunc='mean').reset_index()
    
    # --- Load and Process NOAA Data ---
    try:
        weather_df = pd.read_csv(noaa_path)
    except FileNotFoundError:
        print(f"Error: Could not find {noaa_path}")
        return

    weather_df['date'] = pd.to_datetime(weather_df['DATE']).dt.date

    # --- Merge DataFrames ---
    # Merge the two dataframes on the date
    final_df = pd.merge(aq_pivot, weather_df, on='date', how='inner')

    # --- Clean and Finalize ---
    # Drop unnecessary columns
    final_df = final_df.drop(columns=['DATE', 'STATION', 'date.utc'], errors='ignore')

    # Handle potential missing values, e.g., by forward fill
    final_df.ffill(inplace=True)
    final_df.bfill(inplace=True)

    # Ensure all required columns exist, fill with 0 if not
    for col in ['pm25', 'o3', 'TEMP', 'WDSP', 'PRCP']:
        if col not in final_df.columns:
            final_df[col] = 0
            
    # Save the final prepared data
    os.makedirs('data', exist_ok=True)
    final_df.to_csv(output_path, index=False)

    print(f"Data preparation complete. Final data saved to {output_path}")
    print("\nFinal Data Head:")
    print(final_df.head())

if __name__ == '__main__':
    prepare_data() 