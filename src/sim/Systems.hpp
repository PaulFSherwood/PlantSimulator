#pragma once
#include <entt/entt.hpp>

void ControlSystem(entt::registry& r, float dt);
void ActuatorSystem(entt::registry& r, float dt);
void HydraulicsSystem(entt::registry& r, float dt);
void AlarmSystem(entt::registry& r);

// (Thermal, Failures, HumanFactors, Analytics can be added later)
