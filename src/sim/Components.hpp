#pragma once

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
