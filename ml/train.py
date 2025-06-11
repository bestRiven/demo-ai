import pandas as pd
from autogluon.tabular import TabularPredictor
import os
from ml.aqi import get_overall_aqi # Re-use the AQI calculation logic

def train_model():
    """
    Trains a machine learning model using AutoGluon to predict AQI.
    """
    print("Starting model training...")
    
    # --- 1. Load Data ---
    data_path = os.path.join('data', 'final_data.csv')
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: Processed data file not found at {data_path}")
        print("Please run `python ml/prepare_data.py` first.")
        return

    # --- 2. Feature Engineering ---
    # Calculate the overall AQI for each day
    # Note: The o3 value from OpenAQ is often in ppm, needs conversion to ppb for AQI calculation. 
    # Assuming sample data 'o3' is already in ppb as per requirement.
    df['aqi'], _ = zip(*df.apply(lambda row: get_overall_aqi(row['pm25'], row['o3']), axis=1))

    # The target is to predict the next day's AQI
    df['target_aqi'] = df['aqi'].shift(-1)

    # Drop the last row as it will have a NaN target
    df.dropna(subset=['target_aqi'], inplace=True)
    df['target_aqi'] = df['target_aqi'].astype(int)

    # Convert date to numeric features
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['weekday'] = df['date'].dt.weekday

    # Define features (X) and target (y)
    features = ['TEMP', 'WDSP', 'PRCP', 'month', 'day', 'weekday', 'pm25', 'o3']
    target = 'target_aqi'
    
    train_data = df[features + [target]]

    # --- 3. Model Training with AutoGluon ---
    model_path = os.path.join('models', 'ag-aqi-predictor')
    
    # Initialize the TabularPredictor
    predictor = TabularPredictor(
        label=target,
        path=model_path,
        problem_type='regression', # Predicting a continuous value
        eval_metric='root_mean_squared_error'
    ).fit(
        train_data,
        presets='best_quality', # Use 'medium_quality' for faster training
        time_limit=180 # Time limit in seconds
    )

    print("Model training complete.")
    
    # --- 4. Evaluate Model ---
    print("\n--- Model Evaluation ---")
    leaderboard = predictor.leaderboard(train_data, silent=True)
    print(leaderboard)
    
    # --- 5. Example Prediction ---
    print("\n--- Example Prediction ---")
    # Take the last row of the data as input for prediction
    test_data = train_data.tail(1).drop(columns=[target])
    print("Input features for prediction:")
    print(test_data)
    
    prediction = predictor.predict(test_data)
    print(f"\nPredicted AQI for the next day: {int(prediction.iloc[0])}")

if __name__ == '__main__':
    train_model() 