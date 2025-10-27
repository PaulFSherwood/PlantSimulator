#include "SimCore.hpp"
#include "Components.hpp"
#include "Systems.hpp"
#include <algorithm>

SimCore::SimCore(QObject* parent) : QObject(parent) {
  connect(&timer_, &QTimer::timeout, this, &SimCore::onTick);
  timer_.setTimerType(Qt::PreciseTimer);
}

void SimCore::loadDefaultScenario() {
  // One entity with Pump + Valve + Tank + PID + Alarmable + Pipe
  auto e = registry_.create();
  registry_.emplace<Pump>(e, true, 1.8f, 0.f);
  registry_.emplace<ValveActuator>(e);                 // defaults
  registry_.emplace<Tank>(e, 0.30f, 2.0f, 0.f, 0.f);
  registry_.emplace<Pipe>(e, 1.0f);
  registry_.emplace<PID>(e, 2.0f, 0.5f, 0.0f, 0.60f);  // level control
  registry_.emplace<Alarmable>(e);
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
  AlarmSystem(registry_);
  ++step_;
  emit frameReady();
}
