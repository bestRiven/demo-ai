import pandas as pd
from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor
import os
from ml.aqi import get_overall_aqi

def train_timeseries_model():
    """
    Trains a time series model using AutoGluon TimeSeriesPredictor and evaluates it.
    """
    print("--- Starting Time Series Model Training ---")

    # --- 1. Load Data ---
    data_path = os.path.join('data', 'final_data.csv')
    try:
        df = pd.read_csv(data_path, parse_dates=['date'])
    except FileNotFoundError:
        print(f"Error: Processed data file not found at {data_path}")
        print("Please run `python ml/prepare_data.py` first.")
        return

    # --- 2. Prepare Data for Time Series Format ---
    # Calculate the daily AQI, which will be our target
    df['aqi'], _ = zip(*df.apply(lambda row: get_overall_aqi(row['pm25'], row['o3']), axis=1))
    
    # TimeSeriesDataFrame requires a unique item_id for each time series.
    # Since we only have one city, we'll create a constant ID.
    df['item_id'] = 'Chicago'
    
    # Rename 'date' to 'timestamp' as required by the library
    df.rename(columns={'date': 'timestamp'}, inplace=True)

    # Select columns: the item_id, the timestamp, the target, and any known future features
    ts_df = df[['item_id', 'timestamp', 'aqi']]

    # Convert to TimeSeriesDataFrame
    data = TimeSeriesDataFrame(ts_df)

    # --- 3. Split Data ---
    validation_period = 14
    train_data = data.slice(None, -validation_period)
    
    print(f"Training data size: {len(train_data)}")
    print(f"Validation data size: {validation_period} days")

    # --- 4. Model Training ---
    # We want to predict the next 14 days
    prediction_length = validation_period
    model_path = os.path.join('models', 'ag-aqi-predictor-timeseries')

    predictor = TimeSeriesPredictor(
        label='aqi',
        path=model_path,
        prediction_length=prediction_length,
        eval_metric='RMSE' # Root Mean Squared Error
    ).fit(
        train_data,
        presets="best_quality",
        time_limit=180
    )

    # --- 5. Evaluate Model ---
    # The `evaluate` function scores predictions on the data that follows the training data.
    print("\n--- Time Series Model Evaluation ---")
    performance = predictor.evaluate(data)
    print(f"Validation RMSE: {performance['RMSE']:.2f}")

    leaderboard = predictor.leaderboard(data, silent=True)
    print("\n--- Leaderboard on Validation Data ---")
    print(leaderboard)

    # --- 6. Forecast Future ---
    print("\n--- Example Forecast ---")
    # Forecast the next 14 days from the end of the full dataset
    forecast = predictor.predict(data)
    print("Forecast for the next 14 days:")
    print(forecast)

if __name__ == '__main__':
    train_timeseries_model() 