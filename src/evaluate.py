"""
Evaluation & Visualization Generator for Bio-Sentinel Frugal AI.

Generates:
1. Decision tree structure plot
2. Feature importance ranking
3. Confusion matrices (DT vs LR)
4. Flow vs ΔP trajectory scatter & contour
5. Cartridge degradation timeline plot
6. Feature distribution plots

DISCLAIMER ADDED TO ALL PLOTS:
"DEMONSTRATION / SYNTHETIC — NOT FIELD VALIDATED"
"""

import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import plot_tree

from feature_engineering import FEATURE_COLUMNS

DISCLAIMER_TEXT = "DEMONSTRATION / SYNTHETIC — NOT FIELD VALIDATED"

def set_style():
    sns.set_theme(style="darkgrid")
    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
    plt.rcParams['axes.edgecolor'] = '#334155'
    plt.rcParams['axes.linewidth'] = 1.2

def add_disclaimer(fig):
    fig.text(0.5, 0.01, DISCLAIMER_TEXT,
             ha='center', va='bottom', fontsize=10, color='#ef4444',
             weight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#fee2e2', edgecolor='#ef4444', alpha=0.9))

def plot_visualizations(results_dict, output_dir='visualizations'):
    os.makedirs(output_dir, exist_ok=True)
    set_style()
    
    dt_model = results_dict['dt_model']
    X_test = results_dict['X_test']
    y_test = results_dict['y_test']
    y_pred_dt = results_dict['y_pred_dt']
    y_pred_lr = results_dict['y_pred_lr']
    cm_dt = results_dict['cm_dt']
    cm_lr = results_dict['cm_lr']
    
    # 1. Decision Tree Diagram
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    plot_tree(dt_model, feature_names=FEATURE_COLUMNS, class_names=['NORMAL', 'CHECK', 'HIGH-RISK'],
              filled=True, rounded=True, fontsize=9, ax=ax)
    plt.title("Bio-Sentinel Frugal AI — Decision Tree Rules (max_depth=4)", fontsize=14, weight='bold', pad=15)
    add_disclaimer(fig)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(os.path.join(output_dir, 'decision_tree.png'))
    plt.close()
    
    # 2. Feature Importance
    importances = dt_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    top_n = min(12, np.count_nonzero(importances))
    
    top_indices = indices[:top_n]
    top_features = [FEATURE_COLUMNS[i] for i in top_indices]
    top_scores = importances[top_indices]
    
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    colors = sns.color_palette("viridis", top_n)
    sns.barplot(x=top_scores, y=top_features, palette=colors, ax=ax)
    ax.set_title("Decision Tree Feature Importance", fontsize=14, weight='bold', pad=15)
    ax.set_xlabel("Relative Importance Score")
    add_disclaimer(fig)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(os.path.join(output_dir, 'feature_importance.png'))
    plt.close()
    
    # 3. Confusion Matrix Comparison (DT vs LR)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=300)
    labels = ['NORMAL', 'CHECK', 'HIGH-RISK']
    
    sns.heatmap(cm_dt, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels, ax=axes[0], cbar=False)
    axes[0].set_title("Decision Tree (Primary Frugal AI)", weight='bold')
    axes[0].set_xlabel("Predicted Treatment State")
    axes[0].set_ylabel("True Treatment State")
    
    sns.heatmap(cm_lr, annot=True, fmt='d', cmap='Greens', xticklabels=labels, yticklabels=labels, ax=axes[1], cbar=False)
    axes[1].set_title("Logistic Regression (Baseline)", weight='bold')
    axes[1].set_xlabel("Predicted Treatment State")
    axes[1].set_ylabel("True Treatment State")
    
    add_disclaimer(fig)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(os.path.join(output_dir, 'confusion_matrix.png'))
    plt.close()
    
    # 4. Example Cartridge Trajectory Plot
    # Load synthetic dataset to plot a single full run
    df = pd.read_csv('data/synthetic/cartridge_runs_synthetic.csv')
    sample_run = df[df['run_id'] == 'RUN_001'].copy()
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True, dpi=300)
    
    # pH plot
    axes[0].plot(sample_run['cartridge_age'], sample_run['pH'], color='#0284c7', lw=1.5, label='pH')
    axes[0].axhline(6.5, color='#eab308', ls='--', alpha=0.7)
    axes[0].axhline(8.5, color='#eab308', ls='--', alpha=0.7)
    axes[0].set_ylabel("pH")
    axes[0].legend(loc='upper right')
    
    # Delta P vs Flow
    axes[1].plot(sample_run['cartridge_age'], sample_run['delta_p'], color='#ef4444', lw=1.5, label='ΔP (kPa)')
    ax1_twin = axes[1].twinx()
    ax1_twin.plot(sample_run['cartridge_age'], sample_run['flow'], color='#10b981', ls='-', lw=1.5, label='Flow (L/min)')
    axes[1].set_ylabel("ΔP (kPa)", color='#ef4444')
    ax1_twin.set_ylabel("Flow Rate (L/min)", color='#10b981')
    axes[1].set_title("Hydraulic Clogging Dynamics (ΔP increase & Flow decline)", fontsize=10, loc='left')
    
    # EC & Turbidity
    axes[2].plot(sample_run['cartridge_age'], sample_run['EC'], color='#8b5cf6', lw=1.5, label='EC (µS/cm)')
    axes[2].set_ylabel("EC (µS/cm)")
    ax2_twin = axes[2].twinx()
    ax2_twin.plot(sample_run['cartridge_age'], sample_run['turbidity'], color='#f97316', ls=':', lw=1.5, label='Turbidity (NTU)')
    ax2_twin.set_ylabel("Turbidity (NTU)", color='#f97316')
    
    # Treatment State Timeline
    state_colors = {0: '#10b981', 1: '#f59e0b', 2: '#ef4444'}
    states = sample_run['treatment_state'].values
    ages = sample_run['cartridge_age'].values
    
    for i in range(len(states)-1):
        axes[3].axvspan(ages[i], ages[i+1], color=state_colors[states[i]], alpha=0.6)
    
    axes[3].set_yticks([0, 1, 2])
    axes[3].set_yticklabels(['NORMAL', 'CHECK', 'HIGH-RISK'])
    axes[3].set_ylabel("Treatment State")
    axes[3].set_xlabel("Cartridge Age (Days)")
    
    fig.suptitle("Bio-Sentinel: Example Cartridge Degradation Trajectory (RUN_001)", fontsize=14, weight='bold')
    add_disclaimer(fig)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(os.path.join(output_dir, 'cartridge_degradation_trajectory.png'))
    plt.close()
    
    # 5. Flow vs ΔP Scatter Plot
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    sns.scatterplot(data=df, x='flow', y='delta_p', hue='treatment_state',
                    palette={0: '#10b981', 1: '#f59e0b', 2: '#ef4444'}, alpha=0.6, s=25, ax=ax)
    ax.set_title("Hydraulic Operational Envelope: Flow Rate vs Differential Pressure (ΔP)", weight='bold', pad=15)
    ax.set_xlabel("Flow Rate (L/min)")
    ax.set_ylabel("Differential Pressure ΔP (kPa)")
    add_disclaimer(fig)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(os.path.join(output_dir, 'flow_vs_deltap.png'))
    plt.close()
    
    print(f"✓ All visualization artifacts generated in '{output_dir}/'")

if __name__ == '__main__':
    from train import train_and_evaluate
    res = train_and_evaluate()
    plot_visualizations(res)
