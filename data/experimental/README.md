# Experimental Dataset Schema — Bio-Sentinel

This directory is designated for **real laboratory and field experimental data**.

## Expected CSV Schema

To replace the synthetic demonstration dataset with real experimental observations, save your CSV file as `cartridge_runs_experimental.csv` in this folder with the following schema:

| Column Name | Unit | Type | Description |
|-------------|------|------|-------------|
| `run_id` | - | string/int | Unique identifier for the cartridge test run (e.g., `RUN_001`) |
| `timestamp` | YYYY-MM-DD HH:MM:SS | datetime | Timestamp of observation |
| `pH` | pH units | float | Measured pH value (0–14) |
| `EC` | µS/cm | float | Measured Electrical Conductivity |
| `TDS` | mg/L | float | Measured Total Dissolved Solids |
| `turbidity` | NTU | float | Measured Turbidity |
| `temperature` | °C | float | Water temperature |
| `flow` | L/min | float | Measured flow rate |
| `delta_p` | kPa | float | Differential pressure across cartridge |
| `cumulative_litres` | Litres | float | Cumulative treated water volume |
| `cartridge_age` | Days | float | Age of cartridge in days |
| `lab_As` | µg/L (ppb) | float | Independent laboratory ground-truth Arsenic concentration |
| `lab_F` | mg/L (ppm) | float | Independent laboratory ground-truth Fluoride concentration |
| `lab_Fe` | mg/L (ppm) | float | Independent laboratory ground-truth Iron concentration |
| `treatment_state` | int | int (0, 1, 2) | Ground truth treatment state: `0` = NORMAL, `1` = CHECK, `2` = HIGH-RISK |

## Ground Truth Definition in Laboratory Testing

In real experimental validation:
- `treatment_state = 0` (NORMAL): `lab_As < 10 µg/L` AND `lab_F < 1.5 mg/L` AND `lab_Fe < 0.3 mg/L` AND hydraulic parameters normal.
- `treatment_state = 1` (CHECK / DEGRADING): Approaching breakthrough (`10 <= lab_As < 15` OR `1.2 <= lab_F < 1.5` OR elevated ΔP/turbidity).
- `treatment_state = 2` (HIGH-RISK / VERIFY): Breakthrough occurred (`lab_As >= 15 µg/L` OR `lab_F >= 1.5 mg/L` OR severe fouling ΔP > 80 kPa).

*Note: AI relies ONLY on sensor + hydraulic measurements for real-time state estimation; laboratory measurements serve as training labels during calibration.*
