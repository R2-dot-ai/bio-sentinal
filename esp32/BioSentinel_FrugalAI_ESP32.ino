/*
 * =====================================================================================
 *  BIO-SENTINEL: Frugal AI Enabled Groundwater Safety and Purification System
 *  ESP32 Firmware — Offline Inference Engine
 *  
 *  Target Microcontroller: ESP32-WROOM-32 / ESP32-S3
 *  Architecture: Frugal AI (Embedded C/C++ Decision Tree Rules + Safety Overrides)
 *  
 *  IMPORTANT SCIENTIFIC PRINCIPLE:
 *  "AI does not declare water safe. AI decides when safety needs to be verified."
 *  This firmware DOES NOT measure arsenic or fluoride directly.
 *  It estimates Fe-biochar cartridge treatment state from physical & hydraulic sensors.
 * =====================================================================================
 */

#include <Arduino.h>

// --- System Configuration & Thresholds ---
const float HARD_PH_MIN = 6.0;
const float HARD_PH_MAX = 9.0;
const float HARD_TURBIDITY_MAX = 5.0; // NTU
const float HARD_EC_MAX = 1500.0;      // uS/cm
const float HARD_DELTA_P_MAX = 75.0;   // kPa
const float HARD_FLOW_MIN = 5.0;       // L/min

// Buffer size for short-term rolling trend calculations
const int BUFFER_SIZE = 12;

struct SensorReadings {
    float pH;
    float EC;          // uS/cm
    float TDS;         // mg/L
    float turbidity;   // NTU
    float temperature; // deg C
    float flow;        // L/min
    float delta_p;     // kPa
    float cumulative_litres;
    float cartridge_age_days;
};

struct FrugalAIResult {
    const char* treatment_state; // "NORMAL", "CHECK", "HIGH-RISK", "SENSOR_FAULT"
    float risk_score;             // 0.00 to 1.00
    const char* action_code;     // "CONTINUE", "INSPECT", "VERIFY_AND_SERVICE"
    bool verification_required;
    bool safety_override;
};

// Global Circular Rolling Buffers
float buf_pH[BUFFER_SIZE];
float buf_EC[BUFFER_SIZE];
float buf_delta_p[BUFFER_SIZE];
float buf_flow[BUFFER_SIZE];
int buffer_idx = 0;
bool buffer_filled = false;

// --- Helper Functions ---
float get_rolling_mean(float buf[]) {
    float sum = 0;
    int count = buffer_filled ? BUFFER_SIZE : (buffer_idx == 0 ? 1 : buffer_idx);
    for (int i = 0; i < count; i++) {
        sum += buf[i];
    }
    return sum / count;
}

// --- Frugal Decision Tree Rule Inference ---
// Extracted directly from Python DecisionTreeClassifier (max_depth <= 4)
int run_frugal_decision_tree(float delta_p, float delta_p_over_flow, float ph_dev, float temp_adj_ec, float turb) {
    // Rule Structure:
    // 0 = NORMAL, 1 = CHECK, 2 = HIGH-RISK
    if (delta_p > 60.0 || delta_p_over_flow > 8.5) {
        return 2; // HIGH-RISK: Severe hydraulic resistance / biochar clogging
    } else if (delta_p > 38.0 || delta_p_over_flow > 4.2 || turb > 3.0) {
        if (ph_dev < -0.4 || temp_adj_ec > 750.0) {
            return 2; // HIGH-RISK: High clogging + ion/acidic drift
        } else {
            return 1; // CHECK: Moderate clogging / degradation
        }
    } else {
        if (ph_dev < -0.5 || turb > 2.0) {
            return 1; // CHECK: Early chemical/solids breakthrough
        } else {
            return 0; // NORMAL: Optimal operating envelope
        }
    }
}

// --- Main Assessment Engine ---
FrugalAIResult evaluate_bio_sentinel(SensorReadings s) {
    FrugalAIResult res;
    res.safety_override = false;
    
    // 1. Sensor Fault & Range Check
    if (s.pH < 0.0 || s.pH > 14.0 || s.EC < 0.0 || s.EC > 5000.0 || 
        s.delta_p < 0.0 || s.turbidity < 0.0 || (s.flow <= 0.01 && s.cumulative_litres > 10.0)) {
        res.treatment_state = "SENSOR_FAULT";
        res.risk_score = 0.99;
        res.action_code = "SENSOR_FAULT_VERIFY";
        res.verification_required = true;
        return res;
    }
    
    // Update Rolling Buffers
    buf_pH[buffer_idx] = s.pH;
    buf_EC[buffer_idx] = s.EC;
    buf_delta_p[buffer_idx] = s.delta_p;
    buf_flow[buffer_idx] = s.flow;
    buffer_idx = (buffer_idx + 1) % BUFFER_SIZE;
    if (buffer_idx == 0) buffer_filled = true;
    
    // 2. Feature Computations
    float temp_adj_ec = s.EC / (1.0 + 0.02 * (s.temperature - 25.0));
    float ph_dev = s.pH - 7.3; // Baseline reference pH
    float delta_p_over_flow = s.delta_p / (s.flow + 0.001);
    
    // 3. Frugal AI Inference
    int ai_class = run_frugal_decision_tree(s.delta_p, delta_p_over_flow, ph_dev, temp_adj_ec, s.turbidity);
    
    // 4. Independent Safety Override Layer
    bool hard_violation = (s.pH < HARD_PH_MIN || s.pH > HARD_PH_MAX || 
                          s.turbidity > HARD_TURBIDITY_MAX || s.EC > HARD_EC_MAX ||
                          s.delta_p > HARD_DELTA_P_MAX || s.flow < HARD_FLOW_MIN);
                          
    if (hard_violation) {
        res.treatment_state = "HIGH-RISK";
        res.risk_score = 0.95;
        res.action_code = "TARGETED_LAB_VERIFICATION_REQUIRED";
        res.verification_required = true;
        if (ai_class != 2) res.safety_override = true;
        return res;
    }
    
    // Map AI Prediction
    if (ai_class == 2) {
        res.treatment_state = "HIGH-RISK";
        res.risk_score = 0.88;
        res.action_code = "TARGETED_LAB_VERIFICATION_REQUIRED";
        res.verification_required = true;
    } else if (ai_class == 1) {
        res.treatment_state = "CHECK";
        res.risk_score = 0.48;
        res.action_code = "INSPECT_AND_RECHECK";
        res.verification_required = false;
    } else {
        res.treatment_state = "NORMAL";
        res.risk_score = 0.12;
        res.action_code = "CONTINUE";
        res.verification_required = false;
    }
    
    return res;
}

// --- Setup & Main Loop ---
void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    Serial.println("\n==================================================");
    Serial.println("   BIO-SENTINEL FRUGAL AI — ESP32 FIRMWARE");
    Serial.println("   Groundwater Safety & Purification System");
    Serial.println("==================================================");
    Serial.println("Principle: AI estimates treatment state and triggers");
    Serial.println("           targeted laboratory verification.");
    Serial.println("Offline Mode: ACTIVE (No Cloud / Zero Internet)\n");
}

void loop() {
    // Simulated Sensor Inputs for Demonstration
    SensorReadings current_readings = {
        .pH = 7.1,
        .EC = 440.0,
        .TDS = 281.6,
        .turbidity = 0.6,
        .temperature = 25.2,
        .flow = 11.1,
        .delta_p = 18.0,
        .cumulative_litres = 1450.0,
        .cartridge_age_days = 6.2
    };
    
    FrugalAIResult result = evaluate_bio_sentinel(current_readings);
    
    Serial.println("--------------------------------------------------");
    Serial.print("TREATMENT STATE:       "); Serial.println(result.treatment_state);
    Serial.print("Risk Score:            "); Serial.println(result.risk_score, 2);
    Serial.print("Recommended Action:    "); Serial.println(result.action_code);
    Serial.print("Verification Required: "); Serial.println(result.verification_required ? "YES (Targeted As/F Lab Test)" : "NO");
    if (result.safety_override) {
        Serial.println("WARNING: Independent Hard Safety Override Active!");
    }
    Serial.println("--------------------------------------------------\n");
    
    delay(5000); // Sensor read interval
}
