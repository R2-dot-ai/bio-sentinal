"""
Safety Logic & Hard Override Module for Bio-Sentinel Frugal AI.

Core Principles:
1. Safety override layer operates independently of ML model predictions.
2. Direct sensor limit violations override AI predictions (AI cannot override a clearly unsafe measured value).
3. Sensor fault detection triggers 'SENSOR FAULT / VERIFY' to prevent silent failures.
4. Output nomenclature strictly adheres to treatment-state estimation (NEVER claiming direct As/F detection).
"""

import numpy as np

# Configurable Hard Safety Limits (Independent of AI)
CONFIGURABLE_LIMITS = {
    'ph_min': 6.0,
    'ph_max': 9.0,
    'turbidity_max': 5.0,     # BIS IS 10500 permissible limit
    'ec_max': 1500.0,         # ~1000 mg/L TDS
    'delta_p_max': 75.0,      # High fouling pressure limit (kPa)
    'flow_min': 5.0           # Minimum acceptable hydraulic throughput (L/min)
}

RECOMMENDED_ACTIONS = {
    'NORMAL': {
        'action_code': 'CONTINUE',
        'display': 'Treatment operating normally within validated envelope. Continue operation.',
        'display_hindi': 'शोधन प्रणाली सामान्य रूप से कार्य कर रही है। उपयोग जारी रखें।',
        'verification_required': False
    },
    'CHECK': {
        'action_code': 'INSPECT_AND_RECHECK',
        'display': 'Treatment degradation detected. Inspect pre-filter biocoagulant and recheck sensors.',
        'display_hindi': 'प्रणाली में गिरावट के संकेत। बायोकोगुलेंट और फिल्टर की जांच करें।',
        'verification_required': False
    },
    'HIGH-RISK': {
        'action_code': 'TARGETED_LAB_VERIFICATION_REQUIRED',
        'display': 'High treatment degradation risk! Stop reliance on cartridge. Targeted As/F laboratory verification required.',
        'display_hindi': 'उच्च जोखिम! कार्ट्रिज पर भरोसा न करें। आर्सेनिक/फ्लोराइड प्रयोगशाला जांच करवाएं।',
        'verification_required': True
    },
    'SENSOR_FAULT': {
        'action_code': 'SENSOR_FAULT_VERIFY',
        'display': 'Sensor fault or unrealistic reading detected. Verify sensor connections and calibration.',
        'display_hindi': 'सेंसर में गड़बड़ी या अमान्य रीडिंग। सेंसर की जांच करें।',
        'verification_required': True
    }
}

def evaluate_safety_layer(sensor_readings, ai_prediction, ai_probabilities, sensor_fault=False):
    """
    Applies safety rules over AI predictions.
    
    Parameters:
    - sensor_readings (dict): Raw & basic sensor values (pH, EC, TDS, turbidity, flow, delta_p)
    - ai_prediction (int): 0=NORMAL, 1=CHECK, 2=HIGH-RISK
    - ai_probabilities (array-like): Model class probability distribution [p0, p1, p2]
    - sensor_fault (bool): Sensor fault flag from preprocessing
    
    Returns:
    - final_state (str): 'NORMAL', 'CHECK', 'HIGH-RISK', or 'SENSOR_FAULT'
    - risk_score (float): Calculated operational risk score (0.0 to 1.0)
    - override_triggered (bool): True if safety layer overrode AI prediction
    - override_reason (str): Reason for safety override if triggered
    """
    if sensor_fault:
        return 'SENSOR_FAULT', 0.99, True, "Sensor fault or out-of-range value detected."

    override_triggered = False
    override_reason = ""
    
    # Extract key raw parameters
    ph = sensor_readings.get('pH', 7.0)
    turb = sensor_readings.get('turbidity', 0.5)
    ec = sensor_readings.get('EC', 400.0)
    dp = sensor_readings.get('delta_p', 15.0)
    flow = sensor_readings.get('flow', 10.0)
    
    # 1. Hard Limit Safety Overrides (Force HIGH-RISK)
    hard_violations = []
    if ph < CONFIGURABLE_LIMITS['ph_min'] or ph > CONFIGURABLE_LIMITS['ph_max']:
        hard_violations.append(f"pH out of safe bounds ({ph})")
    if turb > CONFIGURABLE_LIMITS['turbidity_max']:
        hard_violations.append(f"Turbidity exceeds limit ({turb} NTU)")
    if ec > CONFIGURABLE_LIMITS['ec_max']:
        hard_violations.append(f"EC exceeds limit ({ec} µS/cm)")
    if dp > CONFIGURABLE_LIMITS['delta_p_max']:
        hard_violations.append(f"Cartridge ΔP critical ({dp} kPa)")
    if flow < CONFIGURABLE_LIMITS['flow_min']:
        hard_violations.append(f"Flow rate severely restricted ({flow} L/min)")

    if hard_violations:
        final_state = 'HIGH-RISK'
        risk_score = max(0.85, float(ai_probabilities[2]) if ai_probabilities is not None else 0.85)
        if ai_prediction != 2:
            override_triggered = True
            override_reason = "Hard safety threshold violated: " + "; ".join(hard_violations)
        return final_state, risk_score, override_triggered, override_reason

    # 2. State Determination based on AI Prediction
    state_map = {0: 'NORMAL', 1: 'CHECK', 2: 'HIGH-RISK'}
    final_state = state_map.get(ai_prediction, 'CHECK')
    
    # Compute Risk Score
    if ai_probabilities is not None and len(ai_probabilities) == 3:
        # Weighted sum: 0.0 * p0 + 0.5 * p1 + 1.0 * p2
        risk_score = float(0.0 * ai_probabilities[0] + 0.45 * ai_probabilities[1] + 1.0 * ai_probabilities[2])
    else:
        risk_score = 0.1 if final_state == 'NORMAL' else (0.5 if final_state == 'CHECK' else 0.9)
        
    risk_score = round(float(np.clip(risk_score, 0.0, 1.0)), 2)

    return final_state, risk_score, override_triggered, override_reason

if __name__ == '__main__':
    print("Safety Logic Module initialized.")
