#pragma once
#include <chrono>
#include <entt/entt.hpp>

using HoursF = std::chrono::duration<float, std::ratio<3600>>;

// Plain-old ECS data (no methods)
struct Pump {
  bool  running{true};
  float dp_nominal{1.8f};  // nominal pressure rise (arb units)
  float flow{0.f};         // computed each tick
};

struct ValveActuator {
  float cmd{0.f};   // 0..1 command from control
  float pos{0.f};   // 0..1 actual position
  float speed{0.6f}; // fraction/sec travel
  bool  fail_ATC{true}; // air-to-close model flag (unused in MVP)
};

struct Tank {
  float level{0.30f}; // 0..1
  float area {2.0f};  // cross-section
  float inflow{0.f};
  float outflow{0.f};
};

struct Pipe {
  float k{1.0f}; // simple resistance
};

struct PID {
  float kp{2.0f}, ki{0.5f}, kd{0.0f};
  float sp{0.60f}; // setpoint
  float pv{0.30f}; // process variable (feedback)
  float out{0.0f};
  float integ{0.0f};
};

struct Alarmable {
  bool  hi{false}, lo{false}, latched{false};
  float hiSP{0.90f}, loSP{0.10f};
};

struct HumanFactors {
    float training{0.70f};           // 0..1 (higher = better)
    float fatigue{0.20f};            // 0..1 (higher = worse)
    float shift_length_hours{8.0f};  // typical 8..12
    int   staff_on_shift{3};         // responders available
    float reaction_time_mult{1.0f};  // computed each tick (0.5..2.0)
};

struct AlarmResponse {
    bool active{false};
    bool acknowledged{false};
    float ack_timer_s{1.0f};
    float repair_time_s{1.0f};
    float ack_delay_target_s{1.0f};
    float repair_time_target_s{120.0f};
};

struct SiteKPI {
  int alarms_raised{0};
  int alarms_active{0};
  float downtime_s{0.0f};
};

struct HeatExchanger {
    bool  power_on{true};            // enabled?
    float comp_inlet_stream{1.0f};   // arbitrary units (input)
    float comp_outlet_stream{1.0f};  // arbitrary units (output)
    float flow_rate{1.0f};           // 0..∞ (higher = faster response)
    float tau_s{5.0f};               // time constant (seconds)
    float temp{70.0f};               // placeholder for future thermal use
    float pressure{1.0f};            // placeholder for future hydraulic check
};

struct Boiler {
    float pressure{1.0f};
    float steam_flow{10.0f};
    float feedwater_temp{120.0f};
    float efficiency{90.0f};
};

struct RefrigerationCompressor {
    float suction{50.0f};
    float discharge_pressure{50.0f};
    float load{1.0f};
    float motor_kW{120.0f};
};

struct CoolingTower {
    float fan_speed{1500.0f};
    float approach_temp{160.0f};
    float cycles{20.0f};
};

struct AirSystem {
    float pressure{1.0f};
    float dewpoint{1.0f};
    float dryer_status{true};
};

struct WaterTreatment {
    float RO_pressure{10.0f};
    float hardness{10.0f};
    float chemical_dose{10.0f};
};

struct Wastewater {
    float flow_in{10.0f};
    float flow_out{10.0f};
    float DO{10.0f};
    float pH{10.0f};
};
