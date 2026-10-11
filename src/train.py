"""
Model Training Pipeline for Bio-Sentinel Frugal AI.

Features:
- Grouped GroupKFold / Group train-val-test split by run_id (preventing row-level temporal leakage)
- Primary Model: Frugal Decision Tree Classifier (max_depth <= 4, interpretable, ultra-lightweight)
- Baseline Model: Logistic Regression (with StandardScaler pipeline)
- Metric Focus: Class-wise Recall, specifically HIGH-RISK Recall (Class 2)
- Artifact exports: `.joblib` models + C/C++ rule strings for ESP32
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, recall_score, f1_score

from preprocessing import preprocess_data
from feature_engineering import compute_derived_features, FEATURE_COLUMNS

def train_and_evaluate(data_path='data/synthetic/cartridge_runs_synthetic.csv', output_dir='models'):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    print(f"--- Loading dataset from: {data_path} ---")
    raw_df = pd.read_csv(data_path)
    
    # 1. Preprocess & Feature Engineering
    print("Preprocessing data & checking sensor fault masks...")
    clean_df = preprocess_data(raw_df)
    
    print("Computing causal derived time-series features...")
    df_featured = compute_derived_features(clean_df)
    
    # Filter out sensor faults for model training if any
    valid_df = df_featured[~df_featured['sensor_fault']].copy()
    
    X = valid_df[FEATURE_COLUMNS]
    y = valid_df['treatment_state']
    groups = valid_df['run_id']
    
    print(f"\nDataset Overview:")
    print(f"Total valid samples: {len(X)}")
    print(f"Total unique cartridge runs: {groups.nunique()}")
    print("Target class distribution (0=NORMAL, 1=CHECK, 2=HIGH-RISK):")
    print(y.value_counts(normalize=True).map(lambda v: f"{v*100:.1f}%"))

    # 2. Grouped Train / Test Split by run_id (Strictly preventing data leakage)
    print("\nExecuting Grouped Train/Test Split by run_id...")
    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    groups_train, groups_test = groups.iloc[train_idx], groups.iloc[test_idx]
    
    print(f"Train set: {len(X_train)} samples across {groups_train.nunique()} runs")
    print(f"Test set:  {len(X_test)} samples across {groups_test.nunique()} runs")

    # 3. Train Primary Frugal Model: Decision Tree (max_depth <= 4)
    print("\n[1/2] Training Frugal Decision Tree Classifier (max_depth=4)...")
    dt_model = DecisionTreeClassifier(
        max_depth=4,
        min_samples_leaf=50,
        class_weight='balanced',
        random_state=42
    )
    dt_model.fit(X_train, y_train)
    y_pred_dt = dt_model.predict(X_test)
    
    # 4. Train Baseline Model: Logistic Regression
    print("\n[2/2] Training Baseline Logistic Regression...")
    lr_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42))
    ])
    lr_pipeline.fit(X_train, y_train)
    y_pred_lr = lr_pipeline.predict(X_test)
    
    # 5. Evaluate Models
    print("\n" + "="*50)
    print("MODEL EVALUATION RESULTS")
    print("="*50)
    
    target_names = ['NORMAL (0)', 'CHECK (1)', 'HIGH-RISK (2)']
    
    print("\n--- DECISION TREE CLASSIFIER (Primary Frugal AI) ---")
    print(classification_report(y_test, y_pred_dt, target_names=target_names))
    cm_dt = confusion_matrix(y_test, y_pred_dt)
    print("Confusion Matrix:\n", cm_dt)
    dt_high_risk_recall = recall_score(y_test, y_pred_dt, average=None)[2]
    print(f"--> CRITICAL METRIC: HIGH-RISK (Class 2) Recall = {dt_high_risk_recall*100:.2f}%")

    print("\n--- LOGISTIC REGRESSION (Baseline) ---")
    print(classification_report(y_test, y_pred_lr, target_names=target_names))
    cm_lr = confusion_matrix(y_test, y_pred_lr)
    print("Confusion Matrix:\n", cm_lr)
    lr_high_risk_recall = recall_score(y_test, y_pred_lr, average=None)[2]
    print(f"--> Baseline HIGH-RISK (Class 2) Recall = {lr_high_risk_recall*100:.2f}%")

    # 6. Save Models
    dt_path = os.path.join(output_dir, 'decision_tree_frugal.joblib')
    lr_path = os.path.join(output_dir, 'logistic_regression_baseline.joblib')
    joblib.dump(dt_model, dt_path)
    joblib.dump(lr_pipeline, lr_path)
    print(f"\n[OK] Saved trained models to {output_dir}/")
    
    # 7. Print & Save Decision Tree Rules
    tree_rules = export_text(dt_model, feature_names=FEATURE_COLUMNS)
    print("\n--- EXTRACTED DECISION TREE RULES FOR ESP32 ---")
    print(tree_rules)
    
    with open(os.path.join(output_dir, 'decision_tree_rules.txt'), 'w') as f:
        f.write(tree_rules)
        
    return {
        'dt_model': dt_model,
        'lr_pipeline': lr_pipeline,
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'y_pred_dt': y_pred_dt,
        'y_pred_lr': y_pred_lr,
        'cm_dt': cm_dt,
        'cm_lr': cm_lr,
        'feature_names': FEATURE_COLUMNS
    }

if __name__ == '__main__':
    train_and_evaluate()
