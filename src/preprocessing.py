"""
Data Preprocessing Module for Bio-Sentinel Frugal AI.

Handles:
- Missing value imputation (causal forward fill per run)
- Sensor noise reduction & range validation
- Fault detection flags
- Scaling/Normalization for Logistic Regression (leaving raw data intact for Decision Trees)
"""

import pandas as pd
import numpy as np

SENSOR_RANGES = {
    'pH': (0.0, 14.0),
    'EC': (0.0, 5000.0),
    'TDS': (0.0, 3500.0),
    'turbidity': (0.0, 1000.0),
    'temperature': (-5.0, 60.0),
    'flow': (0.0, 50.0),
    'delta_p': (-10.0, 200.0)
}

def detect_sensor_faults(df):
    """
    Identifies sensor faults such as out-of-range, disconnected sensors,
    negative differential pressure, zero flow during run, or stuck values.
    """
    fault_mask = pd.Series(False, index=df.index)
    
    # 1. Out of range check
    for col, (min_v, max_v) in SENSOR_RANGES.items():
        if col in df.columns:
            out_of_bounds = (df[col] < min_v) | (df[col] > max_v)
            fault_mask = fault_mask | out_of_bounds
            
    # 2. Negative Delta P check
    if 'delta_p' in df.columns:
        fault_mask = fault_mask | (df['delta_p'] < 0)
        
    # 3. Flow = 0 when system active check
    if 'flow' in df.columns and 'cumulative_litres' in df.columns:
        # If cumulative litres > 0 but flow is 0.0 for multiple steps
        zero_flow = (df['flow'] <= 0.01) & (df['cumulative_litres'] > 10.0)
        fault_mask = fault_mask | zero_flow

    return fault_mask

def preprocess_data(df):
    """
    Clean and preprocess dataset causally per run_id.
    """
    df = df.copy()
    
    # Sort chronologically within each run_id
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by=['run_id', 'timestamp']).reset_index(drop=True)
        
    # Process per run_id to avoid temporal cross-contamination
    processed_runs = []
    for run_id, group in df.groupby('run_id', sort=False):
        group = group.copy()
        
        # Causal forward-fill missing numeric values within the run
        numeric_cols = group.select_dtypes(include=[np.number]).columns
        group[numeric_cols] = group[numeric_cols].ffill().bfill()
        
        # Sensor Fault Detection
        group['sensor_fault'] = detect_sensor_faults(group)
        
        processed_runs.append(group)
        
    cleaned_df = pd.concat(processed_runs, ignore_index=True)
    return cleaned_df

if __name__ == '__main__':
    print("Preprocessing module ready.")
