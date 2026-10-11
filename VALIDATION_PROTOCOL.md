# Bio-Sentinel Experimental Validation Protocol

## 1. Overview & Objective

This document establishes the experimental protocol for calibrating and field-validating the **Bio-Sentinel Frugal AI** treatment-state estimation model.

> **Core Scientific Rule**: Low-cost physical and hydraulic sensors (pH, EC/TDS, turbidity, temperature, flow, ΔP) **do not measure arsenic or fluoride directly**. The role of the laboratory validation protocol is to pair sensor time-series data with independent certified laboratory chemical analyses to train and validate the AI's capacity to estimate **treatment cartridge degradation state** and trigger **targeted contaminant verification**.

---

## 2. Experimental Setup & Equipment

### 2.1 Treatment Train Assembly
1. **Raw Water Reservoir**: Spiked synthetic groundwater or real Jharkhand mining groundwater (target initial concentrations: $As = 50\text{–}200\,\mu\text{g/L}$, $F^- = 3.0\text{–}8.0\,\text{mg/L}$, $Fe = 2.0\text{–}5.0\,\text{mg/L}$, $pH = 5.5\text{–}7.5$).
2. **Seed-Based Biocoagulation Chamber**: *Moringa oleifera* / *Strychnos potatorum* seed powder dosing for natural flocculation.
3. **Lamellar Gravity Settler**: Inclined plate settler for solids drop-out and turbidity reduction.
4. **Fe-Biochar Composite Bead Fixed-Bed Cartridge**: Iron-impregnated biochar porous beads for simultaneous arsenic and fluoride adsorption.
5. **Sensor Chamber**: Inline flow-through chamber with:
   - Analog/I2C pH Probe
   - EC/TDS Conductivity Probe
   - Turbidity Sensor (Nephelometric)
   - Temperature Sensor (DS18B20)
   - Flow Meter (YF-S201 Hall Effect)
   - Differential Pressure Transducer ($\Delta P$) across cartridge inlet and outlet.

---

## 3. Data Collection Procedure

### 3.1 Continuous Telemetry Logging (Sensor Frequency: Every 10 Seconds)
Record the following parameters continuously to the telemetry logger:
- `timestamp` (YYYY-MM-DD HH:MM:SS)
- `flow` ($L/\text{min}$)
- `delta_p` ($\text{kPa}$)
- `pH`
- `EC` ($\mu\text{S/cm}$) / `TDS` ($\text{mg/L}$)
- `turbidity` ($\text{NTU}$)
- `temperature` ($^\circ\text{C}$)
- `cumulative_litres` ($L$)
- `cartridge_age` ($\text{Days}$)

### 3.2 Discrete Analytical Sampling Schedule (Ground Truth)
Collect treated effluent samples at predefined bed-volume (BV) or cumulative volume intervals:
- **Phase A (Initial 100 BV)**: Sample every 25 BV.
- **Phase B (Mid-life 100–500 BV)**: Sample every 50 BV.
- **Phase C (Near-breakthrough 500+ BV)**: Sample every 10 BV until complete exhaustion.

### 3.3 Certified Laboratory Testing Methods
For each collected sample, perform independent laboratory ground-truth measurements:
- **Arsenic ($As$)**: Atomic Absorption Spectrometry (AAS) or ICP-MS (Detection limit $< 1\,\mu\text{g/L}$).
- **Fluoride ($F^-$)**: Ion-Selective Electrode (ISE) or Ion Chromatography (IC) (Detection limit $< 0.1\,\text{mg/L}$).
- **Iron ($Fe$)**: Phenanthroline Colorimetric Method or AAS.

---

## 4. Ground-Truth Treatment-State Labeling

Each experimental sample interval is assigned a ground-truth `treatment_state` label based on BIS IS 10500:2012 drinking water standards:

$$\text{Treatment State} = \begin{cases} 
0 \quad (\text{NORMAL}) & \text{if } C_{As} < 10\,\mu\text{g/L} \text{ AND } C_F < 1.0\,\text{mg/L} \text{ AND } \Delta P < 40\,\text{kPa} \\
1 \quad (\text{CHECK}) & \text{if } 10 \le C_{As} < 15\,\mu\text{g/L} \text{ OR } 1.0 \le C_F < 1.5\,\text{mg/L} \text{ OR } 40 \le \Delta P < 65\,\text{kPa} \\
2 \quad (\text{HIGH-RISK}) & \text{if } C_{As} \ge 15\,\mu\text{g/L} \text{ OR } C_F \ge 1.5\,\text{mg/L} \text{ OR } \Delta P \ge 65\,\text{kPa}
\end{cases}$$

---

## 5. Model Evaluation Metrics

When evaluating Frugal AI performance against real laboratory ground truth:

1. **Breakthrough Curve ($C/C_0$)**: Plot normalized effluent concentration ($C/C_0$) against cumulative volume ($L$) alongside model risk score predictions.
2. **HIGH-RISK Recall (Sensitivity)**:
   $$\text{Recall}_{\text{HIGH-RISK}} = \frac{\text{True High-Risk Predictions}}{\text{True High-Risk Observations}}$$
   *Target: $> 98\%$ to guarantee user safety.*
3. **False Positive Rate (FPR)**: Unnecessary lab verification triggers.
4. **Cartridge Lifetime Estimation Error**: Difference between AI-predicted verification trigger volume and actual $C/C_0 = 0.5$ breakthrough volume.

---

## 6. Scientific Disclaimer

> **DISCLAIMER**: The synthetic dataset provided with the prototype is for architecture verification and demonstration only (`DEMONSTRATION / SYNTHETIC — NOT FIELD VALIDATED`). Full operational deployment requires conducting the experimental protocol outlined in this document using field water samples from targeted Jharkhand districts (e.g., Dhanbad, Bokaro, Palamu).
