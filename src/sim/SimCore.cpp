#include "sim/Loader.hpp"
#include "sim/SimCore.hpp"
#include "sim/Systems.hpp"
#include "Components.hpp"
#include <algorithm>
#include <QDebug>

SimCore::SimCore(QObject* parent) : QObject(parent) {
  connect(&timer_, &QTimer::timeout, this, &SimCore::onTick);
  timer_.setTimerType(Qt::PreciseTimer);
}

// void SimCore::loadDefaultScenario() {
//   // Equipement entity
//   auto e = registry_.create();
//   registry_.emplace<Pump>(e, true, 1.8f, 0.f);
//   registry_.emplace<ValveActuator>(e);
//   registry_.emplace<Tank>(e, 0.30f, 2.0f, 0.f, 0.f);
//   registry_.emplace<Pipe>(e, 1.0f);
//   registry_.emplace<PID>(e, 2.0f, 0.5f, 0.0f, 0.60f);
//   registry_.emplace<HeatExchanger>(e, true, 1.0f, 1.0f, 1.0f, 5.0f, 70.0f, 1.0f);
//   registry_.emplace<Boiler>(e, 1.0f, 10.0f, 120.0f, 0.90f);               // efficiency as fraction 0..1
//   registry_.emplace<RefrigerationCompressor>(e, 50.0f, 50.0f, 1.0f, 120.0f);
//   registry_.emplace<CoolingTower>(e, 0.0f, 5.0f, 3.0f);                   // normalized fan_speed 0..1
//   registry_.emplace<AirSystem>(e, 7.0f, -20.0f, true);
//   registry_.emplace<WaterTreatment>(e, 10.0f, 1.0f, 50.0f);
//   registry_.emplace<Wastewater>(e, 10.0f, 10.0f, 2.0f, 7.0f);
//   registry_.emplace<SteamLoad>(e, 5.0f, 0.0f);
//   registry_.emplace<CoolingLoad>(e, 25.0f, 0.0f);
//   registry_.emplace<Alarmable>(e);
//   registry_.emplace<AlarmResponse>(e, false, false, 0.f, 0.f, 8.0f, 90.0f);


//   // Site singleton (human factors + KPIs + process buses)
//   auto site = registry_.create();
//   registry_.emplace<HumanFactors>(site, 0.70f, 0.20f, 8.0f, 3, 1.0f);
//   registry_.emplace<SiteKPI>(site);

//   // Put SteamHeader / ChilledWaterLoop on the site (not the equipment)
//   registry_.emplace<SteamHeader>(site, 10.0f, 0.0f, 0.0f, 0.0f);
//   registry_.emplace<ChilledWaterLoop>(site, 7.0f, 12.0f, 0.0f, 0.0f, 0.0f);
// }

void SimCore::start(float hz) {
  dt_ = 1.0f / std::max(1.0f, hz);
  int interval_ms = static_cast<int>(dt_ * 1000.0f);
  timer_.start(interval_ms);
}

void SimCore::stop() {
  timer_.stop();
}

// Control → Actuator → Hydraulics → HeatExchanger → Steam → Cooling → UtilitySystem → BoilerSystem → RefrigSystem → Alarm → HumanFactors → Response → Analytics
void SimCore::onTick() {
  ControlSystem(registry_, dt_);
  ActuatorSystem(registry_, dt_);
  HydraulicsSystem(registry_, dt_);
  HeatExchangerSystem(registry_, dt_);
  Steam(registry_, dt_);
  Cooling(registry_, dt_);
  UtilitySystem(registry_, dt_);
  BoilerSystem(registry_, dt_);
  RefrigSystem(registry_, dt_);
  AlarmSystem(registry_);
  HumanFactorsSystem(registry_, dt_);
  ResponseSystem(registry_, dt_);
  AnalyticsSystem(registry_, dt_);
  ++step_;
  emit frameReady();
}

void SimCore::loadDefaultScenario() {
    if (!Loader::loadPlant("plant_default.json", registry_)) {
        qDebug() << "Failed to load JSON, loading fallback";
    }

    // Site singletons
    auto site = registry_.create();
    registry_.emplace<HumanFactors>(site, 0.7f, 0.2f, 8.0f, 3, 1.0f);
    registry_.emplace<SiteKPI>(site);

}
