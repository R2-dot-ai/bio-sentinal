# BIO-SENTINEL: Frugal AI Enabled Groundwater Safety and Purification System

> **SIH 2026 Problem Statement**: SIH26040 — Smart Water Purification and Quality Monitoring System for Rural and Mining-Affected Areas.

---

> [!WARNING]  
> **EXACT SCIENTIFIC DISCLAIMER**  
> **"This prototype does not claim that low-cost pH, TDS/EC, turbidity, temperature, flow or differential-pressure sensors directly measure arsenic or fluoride. The Frugal AI estimates treatment-system state and identifies conditions that warrant targeted laboratory contaminant verification."**

---

## 1. Core Principles & Philosophy

- **Nomenclature & Output**: AI does NOT classify water as "safe" or "arsenic detected". AI classifies **TREATMENT STATE** (`NORMAL`, `CHECK`, `HIGH-RISK`).
- **Core Principle**: *"AI does not declare water safe. AI decides when safety needs to be verified."*
- **Slogan**: *"Sense cheaply. Verify only when necessary."*
- **Frugal AI**: Ultra-lightweight Decision Tree rules running completely offline on low-cost microcontrollers (ESP32). Zero cloud dependency. Never called TinyML.

---

## 2. System Architecture

```
Raw Groundwater (Rural & Jharkhand Mining Belts)
    │
    ▼
1. Seed-based Biocoagulation
   (Natural flocculation stage using plant-derived biocoagulants)
    │
    ▼
2. Flamingo-Inspired Lamellar Gravity Pretreatment
   (Suspended solids / turbidity reduction & downstream cartridge protection)
    │
    ▼
3. Fe-Biochar Composite Bead Fixed-Bed Cartridge
   (Principal dissolved-contaminant adsorption stage for As & F⁻)
    │
    ▼
4. Intermittent Sensor Chamber
   (Low-cost sensors: pH, TDS/EC, Turbidity, Temp, Flow, Differential Pressure ΔP)
    │
    ▼
5. Frugal AI Edge Engine (ESP32)
   (Feature engineering & decision tree rule inference)
    │
    ▼
6. Treatment-State Assessment
   ┌───────────────────┬───────────────────┬───────────────────┐
   │      NORMAL       │       CHECK       │     HIGH-RISK     │
   │  Operating inside │  Degrading state; │  Cartridge risk;  │
   │  safe envelope    │  inspect filter   │  stop reliance    │
   └───────────────────┴───────────────────┴───────────────────┘
                                                     │
                                                     ▼
                                     Targeted Laboratory Verification
                                     (Certified As / F⁻ ICP-MS/AAS testing)
```

---

## 3. Sensor Inputs & Derived Features

| Raw Sensor Input | Unit | Primary Role | Derived Time-Series Feature |
|------------------|------|--------------|-----------------------------|
| `pH` | pH units | Acid Mine Drainage / Chemical drift | `ph_deviation` from baseline |
| `EC` / `TDS` | µS/cm / mg/L | Ionic breakthrough & mineral concentration | `temp_adj_ec`, `ec_tds_ratio`, `EC_trend` |
| `turbidity` | NTU | Suspended solids / floc leakage | `turbidity_trend`, `rolling_mean_turbidity` |
| `temperature` | °C | Thermal compensation | `temp_adj_ec` (25°C normalized) |
| `flow` | L/min | Hydraulic throughput | `flow_decline_rate`, `normalized_flow` |
| `delta_p` ($\Delta P$) | kPa | Cartridge pore clogging & resistance | `delta_p_increase_rate`, `delta_p_over_flow` |

---

## 4. Frugal AI Model & Training Pipeline

- **Primary Model**: Decision Tree Classifier (`max_depth=4`, `min_samples_leaf=50`).
- **Baseline Comparison**: Logistic Regression with StandardScaler.
- **Grouped Train/Test Split**: Split by `run_id` to eliminate temporal row-level leakage.
- **Primary Metric**: **HIGH-RISK Recall** (Target: $> 98\%$).

---

## 5. ESP32 Deployment & Offline Inference

The Decision Tree model rules are compiled into native C `if/else` logic inside `esp32/BioSentinel_FrugalAI_ESP32.ino`.

- **Memory**: $< 2\,\text{KB}$ RAM / flash usage
- **Inference Time**: $< 0.1\,\text{ms}$
- **Cloud Dependency**: ZERO (Fully offline)

---

## 6. Project Structure

```
BioSentinel_FrugalAI/
│
├── data/
│   ├── synthetic/          # Synthetic trajectory generation scripts & dataset
│   └── experimental/       # Schema documentation for laboratory experiments
│
├── notebooks/              # Jupyter research & analysis notebooks
│
├── src/
│   ├── preprocessing.py    # Sensor fault detection & cleaning
│   ├── feature_engineering.py # Causal derived time-series features
│   ├── train.py            # Grouped train/test model training script
│   ├── evaluate.py         # Visualizations & metrics generation
│   ├── predict.py          # Real-time JSON inference API
│   └── safety_logic.py     # Independent hard safety override layer
│
├── models/                 # Saved .joblib model files & C rule strings
│
├── visualizations/         # Generated figures (Tree, Confusion Matrix, Trajectories)
│
├── esp32/
│   └── BioSentinel_FrugalAI_ESP32.ino # Offline C++ firmware for ESP32
│
├── dashboard/
│   └── index.html          # Interactive local dashboard & simulator
│
├── reports/
│   └── demo_report.md      # Detailed SIH demonstration report
│
├── requirements.txt        # Python dependencies
├── VALIDATION_PROTOCOL.md  # Protocol for laboratory ground-truth calibration
└── README.md               # Project documentation
```

---

## 7. How to Run

### 7.1 Setup Environment & Train Model
```bash
# Navigate to project directory
cd BioSentinel_FrugalAI

# Install dependencies
pip install -r requirements.txt

# 1. Generate Synthetic Dataset
python data/synthetic/generate_synthetic.py

# 2. Train Models (Grouped Split)
python src/train.py

# 3. Generate Evaluation Plots & Visualizations
python src/evaluate.py

# 4. Test Real-Time Inference Script
python src/predict.py --demo
```

### 7.2 Launch Local Interactive Dashboard
Open `dashboard/index.html` in any web browser to view real-time telemetry, risk score gauge, and interactive cartridge degradation simulator.
