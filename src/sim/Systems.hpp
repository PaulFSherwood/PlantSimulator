#pragma once
#include <entt/entt.hpp>

void ControlSystem(entt::registry& r, float dt);
void ActuatorSystem(entt::registry& r, float dt);
void HydraulicsSystem(entt::registry& r, float dt);
void AlarmSystem(entt::registry& r);
void HumanFactorsSystem(entt::registry& r, float dt);
void ResponseSystem(entt::registry& r, float dt);
void AnalyticsSystem(entt::registry& r, float dt);
void HeatExchangerSystem(entt::registry& r, float dt);
void UtilitySystem(entt::registry& r, float dt);
void BoilerSystem(entt::registry& r, float dt);
void RefrigSystem(entt::registry& r, float dt);

// (Thermal, Failures, HumanFactors, Analytics can be added later)
