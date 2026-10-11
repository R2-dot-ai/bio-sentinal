"""
Synthetic Cartridge Trajectory Generator for Bio-Sentinel Frugal AI.

IMPORTANT NOTICE:
"DEMONSTRATION / SYNTHETIC — NOT FIELD VALIDATED"
This synthetic dataset simulates realistic sensor and hydraulic degradation dynamics of an Fe-biochar
composite cartridge for software demonstration and architecture verification only.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_cartridge_run(run_id, num_days=60, readings_per_day=24, seed=42):
    np.random.seed(seed)
    
    total_readings = num_days * readings_per_day
    start_time = datetime(2026, 1, 1) + timedelta(days=int(run_id.split('_')[1]) * 5)
    timestamps = [start_time + timedelta(hours=i) for i in range(total_readings)]
    
    # Cartridge degradation progression (0.0 to 1.0+)
    # Non-linear curve mimicking adsorption saturation and biochar pore clogging
    t = np.linspace(0, 1, total_readings)
    degradation_base = t**1.8 + 0.05 * np.random.randn(total_readings)
    degradation = np.clip(degradation_base, 0, 1.2)
    
    # 1. Temperature (°C) - Seasonal + daily sinusoidal variation
    temp_base = 24.0 + 3.0 * np.sin(2 * np.pi * t * 2) # Slight seasonal drift
    daily_temp = 2.5 * np.sin(2 * np.pi * np.arange(total_readings) / 24.0 - np.pi/2)
    temperature = temp_base + daily_temp + np.random.normal(0, 0.4, total_readings)
    
    # 2. pH Dynamics
    # Initial steady pH (~7.2 - 7.5), slowly drifts down/up as adsorption sites saturate
    ph_baseline = 7.3 + np.random.uniform(-0.2, 0.2)
    ph_drift = -0.8 * (degradation**2) # acidic drift in mining groundwater
    ph_noise = np.random.normal(0, 0.08, total_readings)
    pH = np.clip(ph_baseline + ph_drift + ph_noise, 4.0, 9.5)
    
    # 3. Electrical Conductivity (EC in µS/cm) & TDS (mg/L)
    # EC increases as ion breakthrough occurs; TDS = ~0.64 * EC
    ec_baseline = 450.0 + np.random.uniform(-30, 30)
    ec_rise = 350.0 * (degradation**2.2)
    ec_noise = np.random.normal(0, 12.0, total_readings)
    EC = np.clip(ec_baseline + ec_rise + ec_noise, 200.0, 2000.0)
    TDS = EC * 0.64 + np.random.normal(0, 5.0, total_readings) # Linked measurement
    
    # 4. Turbidity (NTU)
    # Starts low (~0.5 NTU), rises slowly, spikes when biocoagulant/filter clogging leaks solids
    turb_baseline = 0.4 + np.random.uniform(0, 0.2)
    turb_rise = 8.0 * (degradation**3.0)
    turb_noise = np.abs(np.random.normal(0, 0.3, total_readings))
    turbidity = np.clip(turb_baseline + turb_rise + turb_noise, 0.1, 50.0)
    
    # 5. Flow Rate (L/min) & Differential Pressure (Delta P in kPa)
    # As biochar pores clog, Delta P increases exponentially and Flow rate decreases
    flow_baseline = 12.0 + np.random.uniform(-0.5, 0.5)
    flow_decline = 6.5 * (degradation**1.5)
    flow_noise = np.random.normal(0, 0.25, total_readings)
    flow = np.clip(flow_baseline - flow_decline + flow_noise, 1.0, 15.0)
    
    dp_baseline = 15.0 + np.random.uniform(-2, 2)
    dp_rise = 65.0 * (degradation**2.0)
    dp_noise = np.random.normal(0, 1.5, total_readings)
    delta_p = np.clip(dp_baseline + dp_rise + dp_noise, 5.0, 120.0)
    
    # 6. Cumulative Volume (Litres) & Cartridge Age (Days)
    hourly_litres = flow * 60.0 # L/min * 60 min
    cumulative_litres = np.cumsum(hourly_litres)
    cartridge_age = np.arange(total_readings) / 24.0
    
    # 7. Ground Truth Laboratory Contaminant Concentrations (Simulated)
    # As: 0-5 ppb baseline, spikes to 30+ ppb after breakthrough
    lab_As = 2.0 + 35.0 * np.maximum(0, degradation - 0.65)**2 + np.random.normal(0, 0.5, total_readings)
    lab_As = np.clip(lab_As, 0.5, 100.0)
    
    # F: 0.4 ppm baseline, spikes to 3.5+ ppm
    lab_F = 0.5 + 3.0 * np.maximum(0, degradation - 0.60)**2 + np.random.normal(0, 0.05, total_readings)
    lab_F = np.clip(lab_F, 0.1, 10.0)
    
    # Fe: 0.1 ppm baseline, spikes to 1.5+ ppm
    lab_Fe = 0.1 + 2.0 * np.maximum(0, degradation - 0.70)**2 + np.random.normal(0, 0.02, total_readings)
    lab_Fe = np.clip(lab_Fe, 0.05, 5.0)
    
    # 8. Treatment State Classification
    # 0 = NORMAL (0.0 to 0.50 degradation)
    # 1 = CHECK / DEGRADING (0.50 to 0.75 degradation)
    # 2 = HIGH-RISK / VERIFY (0.75+ degradation or severe hydraulic/contaminant breakthrough)
    treatment_state = np.zeros(total_readings, dtype=int)
    
    for i in range(total_readings):
        d = degradation[i]
        dp = delta_p[i]
        fl = flow[i]
        as_c = lab_As[i]
        f_c = lab_F[i]
        
        if d >= 0.75 or dp >= 65.0 or fl <= 6.5 or as_c >= 10.0 or f_c >= 1.5:
            treatment_state[i] = 2 # HIGH-RISK
        elif d >= 0.45 or dp >= 40.0 or fl <= 8.5 or as_c >= 7.0 or f_c >= 1.0:
            treatment_state[i] = 1 # CHECK / DEGRADING
        else:
            treatment_state[i] = 0 # NORMAL

    df = pd.DataFrame({
        'run_id': run_id,
        'timestamp': timestamps,
        'pH': np.round(pH, 2),
        'EC': np.round(EC, 1),
        'TDS': np.round(TDS, 1),
        'turbidity': np.round(turbidity, 2),
        'temperature': np.round(temperature, 1),
        'flow': np.round(flow, 2),
        'delta_p': np.round(delta_p, 2),
        'cumulative_litres': np.round(cumulative_litres, 1),
        'cartridge_age': np.round(cartridge_age, 2),
        'lab_As': np.round(lab_As, 2),
        'lab_F': np.round(lab_F, 2),
        'lab_Fe': np.round(lab_Fe, 2),
        'treatment_state': treatment_state
    })
    
    return df

def generate_synthetic_dataset(num_runs=35, output_path='data/synthetic/cartridge_runs_synthetic.csv'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    all_runs = []
    
    print(f"Generating synthetic dataset with {num_runs} independent cartridge runs...")
    for i in range(1, num_runs + 1):
        run_id = f"RUN_{i:03d}"
        days = np.random.randint(45, 75)
        df_run = generate_cartridge_run(run_id, num_days=days, seed=100 + i)
        all_runs.append(df_run)
        
    full_df = pd.concat(all_runs, ignore_index=True)
    full_df.to_csv(output_path, index=False)
    
    print(f"[OK] Synthetic dataset saved to {output_path}")
    print(f"Total rows: {len(full_df)}")
    print("Class distribution:")
    state_map = {0: 'NORMAL', 1: 'CHECK', 2: 'HIGH-RISK'}
    counts = full_df['treatment_state'].map(state_map).value_counts()
    percentages = full_df['treatment_state'].map(state_map).value_counts(normalize=True) * 100
    for state in ['NORMAL', 'CHECK', 'HIGH-RISK']:
        c = counts.get(state, 0)
        p = percentages.get(state, 0.0)
        print(f"  {state:10s}: {c:6d} rows ({p:.2f}%)")
        
    print("\nDisclaimer: DEMONSTRATION / SYNTHETIC — NOT FIELD VALIDATED")
    return full_df

if __name__ == '__main__':
    generate_synthetic_dataset()
