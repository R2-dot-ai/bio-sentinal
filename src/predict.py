"""
Real-Time Inference Script for Bio-Sentinel Frugal AI.

Inputs: Raw sensor readings (+ optional historical buffer for time-series features)
Outputs: JSON formatted assessment with treatment_state, risk_score, recommended_action, verification_required.
"""

import os
import json
import joblib
import argparse
import numpy as np
import pandas as pd

from preprocessing import detect_sensor_faults
from feature_engineering import compute_derived_features, FEATURE_COLUMNS
from safety_logic import evaluate_safety_layer, RECOMMENDED_ACTIONS

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/decision_tree_frugal.joblib')

class BioSentinelPredictor:
    def __init__(self, model_path=MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Trained model not found at {model_path}. Please run train.py first.")
        self.model = joblib.load(model_path)
        
    def predict_single(self, current_readings, history_buffer=None):
        """
        Perform inference for a single observation.
        
        Parameters:
        - current_readings (dict): e.g. {'pH': 7.1, 'EC': 450, 'TDS': 288, 'turbidity': 0.8, 'temperature': 25, 'flow': 11.2, 'delta_p': 18.5, 'cumulative_litres': 500, 'cartridge_age': 5.0}
        - history_buffer (list of dicts): Past 12-24 readings for computing trend & rolling features
        """
        # Assemble buffer
        if history_buffer is None:
            history_buffer = []
            
        full_readings = history_buffer + [current_readings]
        df_raw = pd.DataFrame(full_readings)
        
        if 'run_id' not in df_raw.columns:
            df_raw['run_id'] = 'LIVE_RUN'
        if 'timestamp' not in df_raw.columns:
            df_raw['timestamp'] = pd.date_range(end=pd.Timestamp.now(), periods=len(df_raw), freq='h')
            
        # Sensor Fault Check on current reading
        fault_series = detect_sensor_faults(df_raw)
        current_fault = bool(fault_series.iloc[-1])
        
        # Compute derived features
        df_featured = compute_derived_features(df_raw)
        current_row = df_featured.iloc[[-1]]
        
        X = current_row[FEATURE_COLUMNS]
        
        # AI Inference
        ai_pred = int(self.model.predict(X)[0])
        
        if hasattr(self.model, 'predict_proba'):
            ai_probs = self.model.predict_proba(X)[0]
        else:
            ai_probs = np.array([1.0 if i == ai_pred else 0.0 for i in range(3)])
            
        # Apply Safety Logic
        final_state, risk_score, overrode, override_reason = evaluate_safety_layer(
            sensor_readings=current_readings,
            ai_prediction=ai_pred,
            ai_probabilities=ai_probs,
            sensor_fault=current_fault
        )
        
        action_meta = RECOMMENDED_ACTIONS.get(final_state, RECOMMENDED_ACTIONS['CHECK'])
        
        output = {
            "system_name": "Bio-Sentinel Frugal AI",
            "principle": "AI estimates treatment state and triggers verification. AI does not declare water safe.",
            "treatment_state": final_state,
            "risk_score": risk_score,
            "recommended_action": action_meta['action_code'],
            "action_description": action_meta['display'],
            "action_description_hindi": action_meta['display_hindi'],
            "verification_required": action_meta['verification_required'],
            "safety_override_active": overrode,
            "safety_override_reason": override_reason if overrode else None,
            "disclaimer": "DEMONSTRATION / SYNTHETIC — NOT FIELD VALIDATED"
        }
        
        return output

def demo_predictions():
    predictor = BioSentinelPredictor()
    
    print("\n" + "="*60)
    print("BIO-SENTINEL REAL-TIME INFERENCE DEMONSTRATION")
    print("="*60)
    
    # 1. Normal State Observation
    normal_input = {
        'pH': 7.3, 'EC': 420.0, 'TDS': 268.8, 'turbidity': 0.5,
        'temperature': 24.5, 'flow': 11.5, 'delta_p': 16.0,
        'cumulative_litres': 1200.0, 'cartridge_age': 4.5
    }
    res_normal = predictor.predict_single(normal_input)
    print("\n--- TEST CASE 1: NORMAL OPERATION ---")
    print(json.dumps(res_normal, indent=2))
    
    # 2. Check / Degrading State Observation
    check_input = {
        'pH': 6.6, 'EC': 720.0, 'TDS': 460.8, 'turbidity': 3.2,
        'temperature': 26.0, 'flow': 8.2, 'delta_p': 48.0,
        'cumulative_litres': 8500.0, 'cartridge_age': 32.0
    }
    res_check = predictor.predict_single(check_input)
    print("\n--- TEST CASE 2: DEGRADING / CHECK ---")
    print(json.dumps(res_check, indent=2))
    
    # 3. High Risk / Cartridge Breakthrough Observation
    high_risk_input = {
        'pH': 5.8, 'EC': 1150.0, 'TDS': 736.0, 'turbidity': 9.5,
        'temperature': 27.5, 'flow': 4.5, 'delta_p': 82.0,
        'cumulative_litres': 16000.0, 'cartridge_age': 55.0
    }
    res_high_risk = predictor.predict_single(high_risk_input)
    print("\n--- TEST CASE 3: HIGH-RISK / VERIFY REQUIRED ---")
    print(json.dumps(res_high_risk, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Bio-Sentinel Frugal AI Real-Time Inference")
    parser.add_argument('--demo', action='store_true', help="Run demonstration test cases")
    args = parser.parse_args()
    
    if args.demo or True:
        demo_predictions()
