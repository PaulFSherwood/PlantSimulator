#include "Systems.hpp"
#include "Components.hpp"
#include <algorithm>

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
    auto& t = v.get<Tank>(e);
    auto& a = v.get<Alarmable>(e);

    // Compute instantaneous alarm states from current level vs setpoints
    const bool hi_now = (tank.level > alm.hiSP);
    const bool lo_now = (tank.level < alm.loSP);

    // Update non-latched "present" alarms
    a.hi = t.level > a.hiSP;
    a.lo = t.level < a.loSP;

    // Latch: once true, stays true until someone clears alm.latched elsewhere
    a.latched = a.latched || a.hi || a.lo;
  }
}

void HumanFactorsSystem(entt::registry& r) {
    // View all humans that work in production area

}
