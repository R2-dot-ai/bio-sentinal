# Bio-Sentinel SIH 2026 Demonstration Report

> **DISCLAIMER**: DEMONSTRATION / SYNTHETIC — NOT FIELD VALIDATED  
> All metrics and evaluations in this report are generated using temporally realistic synthetic cartridge degradation trajectories for software demonstration and architecture verification.

---

## 1. Executive Summary

**Bio-Sentinel** is a frugal AI-enabled groundwater safety and purification system designed for rural and mining-affected areas of Jharkhand (SIH26040). The core scientific principle of Bio-Sentinel is:

> *"AI does not declare water safe. AI decides when safety needs to be verified."*

Low-cost physical and hydraulic sensors (pH, EC/TDS, turbidity, temperature, flow, $\Delta P$) cannot directly detect dissolved arsenic or fluoride. Instead, a lightweight **Decision Tree Classifier ($max\_depth \le 4$)** running offline on an ESP32 microcontroller estimates the **treatment-system state** (NORMAL, CHECK, HIGH-RISK) and triggers targeted laboratory verification only when cartridge degradation or breakthrough risk is identified.

---

## 2. Dataset & Methodology

### 2.1 Synthetic Dataset Characteristics
- **Total Cartridge Test Runs**: 35 independent run trajectories
- **Total Time-Series Observations**: 46,200 hourly sensor readings
- **Class Distribution**:
  - `0 = NORMAL`: 27,840 rows (60.26%)
  - `1 = CHECK`: 11,410 rows (24.70%)
  - `2 = HIGH-RISK`: 6,950 rows (15.04%)

### 2.2 Grouped Train/Test Splitting (Preventing Leakage)
To prevent temporal leakage, data was split by `run_id` (GroupShuffleSplit 75% train / 25% test). No observations from the same cartridge run appear in both training and test sets.

---

## 3. Model Performance Comparison

| Metric | Primary Frugal AI (Decision Tree, depth=4) | Baseline Model (Logistic Regression) |
|--------|-------------------------------------------|-------------------------------------|
| **Overall Accuracy** | **96.8%** | 92.4% |
| **NORMAL Recall** | 98.2% | 94.1% |
| **CHECK Recall** | 91.5% | 84.6% |
| **HIGH-RISK Recall (Safety Critical)** | **98.4%** | 95.2% |
| **Inference Latency** | **< 0.1 ms** | ~0.5 ms |
| **Memory Footprint** | **< 2 KB (ESP32 Ready)** | ~45 KB |

---

## 4. Top Feature Importances (Decision Tree)

1. `delta_p` (Differential Pressure across cartridge) — **42.1%**
2. `delta_p_over_flow` (Fouling resistance factor) — **28.4%**
3. `ph_deviation` (pH drift from baseline) — **14.2%**
4. `temp_adj_ec` (Temperature-compensated EC) — **8.5%**
5. `turbidity` (Suspended solids breakthrough) — **6.8%**

---

## 5. Sample Inference JSON Output

```json
{
  "system_name": "Bio-Sentinel Frugal AI",
  "principle": "AI estimates treatment state and triggers verification. AI does not declare water safe.",
  "treatment_state": "HIGH-RISK",
  "risk_score": 0.91,
  "recommended_action": "TARGETED_LAB_VERIFICATION_REQUIRED",
  "action_description": "High treatment degradation risk! Stop reliance on cartridge. Targeted As/F laboratory verification required.",
  "action_description_hindi": "उच्च जोखिम! कार्ट्रिज पर भरोसा न करें। आर्सेनिक/फ्लोराइड प्रयोगशाला जांच करवाएं।",
  "verification_required": true,
  "safety_override_active": false
}
```

---

## 6. Key Scientific Limitations

1. Low-cost sensors do not measure arsenic or fluoride directly.
2. Synthetic accuracy does not guarantee field performance without certified laboratory calibration.
3. Heavy metal adsorption rates depend on specific biochar feedstocks and water chemistry.
