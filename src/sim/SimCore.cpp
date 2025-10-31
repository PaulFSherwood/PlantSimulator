#include "sim/SimCore.hpp"
#include "Components.hpp"
#include "sim/Systems.hpp"
#include <algorithm>

SimCore::SimCore(QObject* parent) : QObject(parent) {
  connect(&timer_, &QTimer::timeout, this, &SimCore::onTick);
  timer_.setTimerType(Qt::PreciseTimer);
}

void SimCore::loadDefaultScenario() {
  // Equipement entity
  auto e = registry_.create();
  registry_.emplace<Pump>(e, true, 1.8f, 0.f);
  registry_.emplace<ValveActuator>(e);
  registry_.emplace<Tank>(e, 0.30f, 2.0f, 0.f, 0.f);
  registry_.emplace<Pipe>(e, 1.0f);
  registry_.emplace<PID>(e, 2.0f, 0.5f, 0.0f, 0.60f);
  registry_.emplace<HeatExchanger>(e, 1.0f, 1.0f, 1.0f, 70.0, 1.0f, true);
  registry_.emplace<Alarmable>(e);
  registry_.emplace<AlarmResponse>(e, false, false, 0.f, 0.f, 8.0f, 90.0f);

  // Site singleton (human factors + KPIs)
  auto site = registry_.create();
  registry_.emplace<HumanFactors>(site, 0.70f, 0.20f, 8.0f, 90.0f); // faster demo
  registry_.emplace<SiteKPI>(site);
}

void SimCore::start(float hz) {
  dt_ = 1.0f / std::max(1.0f, hz);
  int interval_ms = static_cast<int>(dt_ * 1000.0f);
  timer_.start(interval_ms);
}

void SimCore::stop() {
  timer_.stop();
}

void SimCore::onTick() {
  ControlSystem(registry_, dt_);
  ActuatorSystem(registry_, dt_);
  HydraulicsSystem(registry_, dt_);
  HeatExchangerSystem(registry_, dt_);
  AlarmSystem(registry_);
  HumanFactorsSystem(registry_, dt_);
  ResponseSystem(registry_, dt_);
  AnalyticsSystem(registry_, dt_);
  ++step_;
  emit frameReady();
}

