import pandas as pd
from autogluon.tabular import TabularPredictor
import os
from ml.aqi import get_overall_aqi

def train_tabular_model():
    """
    Trains a machine learning model using AutoGluon TabularPredictor on data
    with engineered features and evaluates it.
    """
    print("--- Starting Tabular Model Training ---")
    
    # --- 1. Load Data ---
    data_path = os.path.join('data', 'final_data.csv')
    try:
        df = pd.read_csv(data_path, parse_dates=['date'])
    except FileNotFoundError:
        print(f"Error: Processed data file not found at {data_path}")
        print("Please run `python ml/prepare_data.py` first.")
        return

    # --- 2. Target Variable Engineering ---
    # Calculate the daily AQI to use as the target for the next day's prediction
    df['aqi'], _ = zip(*df.apply(lambda row: get_overall_aqi(row['pm25'], row['o3']), axis=1))
    df['target_aqi'] = df['aqi'].shift(-1)
    df.dropna(subset=['target_aqi'], inplace=True)
    df['target_aqi'] = df['target_aqi'].astype(int)

    # --- 3. Split Data into Training and Validation Sets ---
    # Use the last 14 days for validation to simulate a real-world forecasting scenario
    validation_period = 14
    train_data = df.iloc[:-validation_period]
    validation_data = df.iloc[-validation_period:]
    
    print(f"Training data size: {len(train_data)}")
    print(f"Validation data size: {len(validation_data)}")

    # --- 4. Model Training with AutoGluon ---
    model_path = os.path.join('models', 'ag-aqi-predictor-tabular') # New path for clarity
    
    # Define features to use. 'date' is excluded as we use its components.
    features = [col for col in train_data.columns if col not in ['date', 'aqi', 'target_aqi']]
    target = 'target_aqi'
    
    predictor = TabularPredictor(
        label=target,
        path=model_path,
        problem_type='regression',
        eval_metric='root_mean_squared_error'
    ).fit(
        train_data[features + [target]],
        presets='best_quality',
        time_limit=180
    )

    # --- 5. Evaluate Model on Validation Set ---
    print("\n--- Tabular Model Evaluation on Validation Set ---")
    performance = predictor.evaluate(validation_data)
    print(f"Validation RMSE: {performance['root_mean_squared_error']:.2f}")

    leaderboard = predictor.leaderboard(validation_data, silent=True)
    print("\n--- Leaderboard on Validation Data ---")
    print(leaderboard)
    
    # --- 6. Example Prediction ---
    print("\n--- Example Prediction ---")
    # Take the last row of the known data to predict the next day
    test_data = validation_data.tail(1).drop(columns=[target])
    prediction = predictor.predict(test_data)
    print(f"Input features for prediction:\n{test_data[features]}")
    print(f"\nPredicted AQI for the next day: {int(prediction.iloc[0])}")

if __name__ == '__main__':
    train_tabular_model() 