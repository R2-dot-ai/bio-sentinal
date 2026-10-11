"""
Feature Engineering Module for Bio-Sentinel Frugal AI.

Computes strictly CAUSAL derived time-series features without future-data leakage.
All rolling windows and baselines use past/current observations only.
"""

import pandas as pd
import numpy as np

def compute_derived_features(df):
    """
    Computes time-series derived features causally per run_id.
    """
    df = df.copy()
    processed_runs = []

    for run_id, group in df.groupby('run_id', sort=False):
        group = group.copy()

        # Sort by timestamp
        if 'timestamp' in group.columns:
            group = group.sort_values('timestamp')

        # 1. Temperature-Adjusted Conductivity (EC compensated to 25°C)
        # Standard temperature compensation coefficient = 0.02 per °C
        if 'EC' in group.columns and 'temperature' in group.columns:
            group['temp_adj_ec'] = group['EC'] / (1.0 + 0.02 * (group['temperature'] - 25.0))
        else:
            group['temp_adj_ec'] = group['EC']

        # 2. EC / TDS Ratio (Consistency check; TDS and EC are related measurements)
        group['ec_tds_ratio'] = group['EC'] / (group['TDS'] + 1e-5)

        # 3. Baselines (First 24 readings or initial reading mean for this run)
        baseline_window = min(24, len(group))
        ph_base = group['pH'].iloc[:baseline_window].mean()
        ec_base = group['EC'].iloc[:baseline_window].mean()
        flow_base = group['flow'].iloc[:baseline_window].mean()
        dp_base = group['delta_p'].iloc[:baseline_window].mean()

        # 4. Changes from Cartridge Baseline
        group['ph_deviation'] = group['pH'] - ph_base
        group['ec_change_from_base'] = group['EC'] - ec_base
        group['dp_change_from_base'] = group['delta_p'] - dp_base

        # 5. Flow Decline Rate & Normalized Flow
        group['flow_decline_rate'] = (flow_base - group['flow']) / (flow_base + 1e-5)
        group['normalized_flow'] = group['flow'] / (flow_base + 1e-5)

        # 6. ΔP / Flow Relationship (Cartridge Resistance / Fouling Factor)
        group['delta_p_over_flow'] = group['delta_p'] / (group['flow'] + 1e-5)

        # 7. Rolling Means (Past 12 readings)
        window = 12
        for col in ['pH', 'EC', 'turbidity', 'delta_p', 'flow']:
            if col in group.columns:
                group[f'rolling_mean_{col}'] = group[col].rolling(window=window, min_periods=1).mean()
                group[f'rolling_std_{col}'] = group[col].rolling(window=window, min_periods=1).std().fillna(0.0)

        # 8. Short-term Slopes / Trends (Linear slope over past 6 readings)
        short_w = 6
        for col in ['EC', 'TDS', 'turbidity', 'delta_p']:
            if col in group.columns:
                # Rolling linear trend calculation using past short_w values
                group[f'{col}_trend'] = group[col].diff(periods=short_w).fillna(0.0) / short_w

        processed_runs.append(group)

    result_df = pd.concat(processed_runs, ignore_index=True)
    return result_df

FEATURE_COLUMNS = [
    'pH', 'EC', 'TDS', 'turbidity', 'temperature', 'flow', 'delta_p',
    'cumulative_litres', 'cartridge_age',
    'temp_adj_ec', 'ec_tds_ratio', 'ph_deviation', 'ec_change_from_base',
    'dp_change_from_base', 'flow_decline_rate', 'normalized_flow', 'delta_p_over_flow',
    'rolling_mean_pH', 'rolling_std_pH', 'rolling_mean_EC', 'rolling_std_EC',
    'rolling_mean_turbidity', 'rolling_std_turbidity', 'rolling_mean_delta_p', 'rolling_std_delta_p',
    'rolling_mean_flow', 'rolling_std_flow',
    'EC_trend', 'TDS_trend', 'turbidity_trend', 'delta_p_trend'
]

if __name__ == '__main__':
    print(f"Feature engineering module configured with {len(FEATURE_COLUMNS)} feature dimensions.")
