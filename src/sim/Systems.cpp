#include "Systems.hpp"
#include "Components.hpp"
#include <algorithm>
#include <cmath>

void ControlSystem(entt::registry& r, float dt) {
  auto view = r.view<PID>();
  for(auto e : view) {
    auto& pid = view.get<PID>(e);
    float err = pid.sp - pid.pv;
    pid.integ += err * dt;
    pid.out = std::clamp(pid.kp*err + pid.ki*pid.integ /*+ pid.kd*deriv*/, 0.f, 1.f);
  }
}

void ActuatorSystem(entt::registry& r, float dt) {
  auto view = r.view<ValveActuator, PID>();
  for(auto e : view) {
    auto& v   = view.get<ValveActuator>(e);
    auto& pid = view.get<PID>(e);
    float target = pid.out;
    float delta  = std::clamp(target - v.pos, -v.speed*dt, v.speed*dt);
    v.pos += delta;
  }
}

void HydraulicsSystem(entt::registry& r, float dt) {
  auto pumps = r.view<Pump>();
  for(auto e : pumps) {
    auto& p = pumps.get<Pump>(e);
    float valve_open = 1.f;
    if (auto v = r.try_get<ValveActuator>(e)) valve_open = v->pos;
    float k = 1.f;
    if (auto pipe = r.try_get<Pipe>(e)) k = pipe->k;

    float dp = p.running ? p.dp_nominal : 0.f;
    p.flow = valve_open * dp / (k + 1e-3f);

    if (auto t = r.try_get<Tank>(e)) {
      t->inflow = p.flow;
      t->outflow = 0.f; // no outlet yet
      t->level = std::clamp(t->level + (t->inflow - t->outflow)/t->area * dt, 0.f, 1.f);
      if (auto pid = r.try_get<PID>(e)) pid->pv = t->level;
    }
  }
}

void AlarmSystem(entt::registry& r) {
  // View of all entities that have BOTH Tanks and Alarmable
  auto v = r.view<Tank, Alarmable>();

  // Iterate entities
  for (auto e : v) {

    // Get components by reference (no copies)
    auto& tank = v.get<Tank>(e);
    auto& alarm = v.get<Alarmable>(e);

    // Compute instantaneous alarm states from current level vs setpoints
    const bool hi_now = (tank.level > alarm.hiSP);
    const bool lo_now = (tank.level < alarm.loSP);

    // Update non-latched "present" alarms
    alarm.hi = tank.level > alarm.hiSP;
    alarm.lo = tank.level < alarm.loSP;

    // Latch: once true, stays true until someone clears alm.latched elsewhere
    alarm.latched = alarm.latched || alarm.hi || alarm.lo;
  }
}

void HumanFactorsSystem(entt::registry& r, float /*dt*/) {
    // View all humans that work in production area
  auto v = r.view<HumanFactors>();
  for (auto e : v) {
    auto& hf = v.get<HumanFactors>(e);

    // Simple, tunable model: 
    // [fatigue ^ or > slower; longer shifts > slower; training ^ or > faster; more staff > faster ]
    float f_fatigue   = 1.0f + 0.6f * std::clamp(hf.fatigue, 0.0f, 1.0f);
    float f_shift     = 1.0f + 0.15f * std::clamp((hf.shift_length_hours - 8.0f) / 4.0f, -1.0f, 1.0f);
    float f_training  = 1.0f - 0.4f * std::clamp(hf.training, 0.0f, 1.0f);
    float f_staff     = 1.0f - 0.05f * std::clamp(0, hf.staff_on_shift, 3);

    float mult = f_fatigue * f_shift * f_training * f_staff;
    hf.reaction_time_mult = std::clamp(mult, 0.5f, 2.0f);
  }
}

// Drive acknowlege + repair timers for each alarmable thing, scaled by human factors.
void ResponseSystem(entt::registry& r, float dt) {
  // Get site multiplier (default 1.0 if none)
  float rt_mult = 1.0f;
  if (auto site = r.view<HumanFactors>(); !site.empty()) {
    rt_mult = site.get<HumanFactors>(*site.begin()).reaction_time_mult;
  }

  // Optionally grap KPIs (singleton)  // should this be here?
  SiteKPI* kpi_ptr = nullptr;
  if (auto vk = r.view<SiteKPI>();  !vk.empty()) kpi_ptr = &vk.get<SiteKPI>(*vk.begin());
  
  // Iterate over all alarmable entities that also have a response state 
  auto v = r.view<Alarmable, AlarmResponse>();
  for (auto e : v) {
    auto& a = v.get<Alarmable>(e);
    auto& ar = v.get<AlarmResponse>(e);

    const bool alarm_now = (a.hi || a.lo);

    // Rising edge of alarm -> start response
    if (alarm_now && !ar.active) {
      ar.active = true;
      ar.acknowledged = false;
      ar.ack_timer_s  = std::max(0.0f, ar.ack_delay_target_s * rt_mult);
      ar.repair_time_s = std::max(0.0f, ar.repair_time_target_s * rt_mult);
      if (kpi_ptr) { kpi_ptr->alarms_raised++; kpi_ptr->alarms_active++; }
    }

    if (ar.active) {
      // Downtime accruse while active 
      if (kpi_ptr) kpi_ptr->downtime_s += dt;

      // acknowlege, then repair
      if (!ar.acknowledged) {
        ar.ack_timer_s = std::max(0.0f, ar.ack_timer_s - dt);
        if (ar.ack_timer_s <= 0.0f) {
          // Repair complete: clear alarm & response (simple model)
          a.latched = false;
          ar.active = false;
          ar.acknowledged = false;
          if (kpi_ptr && kpi_ptr->alarms_active > 0) kpi_ptr->alarms_active--;
        }
      }
    }

    // If alarm condition cleared before we started -> ensure not stuck active
    if (!alarm_now && !a.latched && ar.active && !ar.acknowledged && ar.ack_timer_s > 0.0f) {
      // Allow auto-clear if it was a transient pre-ack blip
      ar.active = false;
      if (kpi_ptr && kpi_ptr->alarms_active > 0) kpi_ptr->alarms_active--;
    }
  }
}

// (Optional) place for rolling aggregates: MVP just exists for future use.
void AnalyticsSystem(entt::registry& /*r*/, float /*dt*/) {
  // Intentionally minimal for now.
}
