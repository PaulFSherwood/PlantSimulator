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

void SimCore::loadDefaultScenario() {
    // Load ECS entities based on JSON components
    if (!Loader::loadPlant("plant_default.json", registry_)) {
        qDebug() << "Could not load JSON plant_default.json";
    }

    // Site singletons
    auto site = registry_.create();
    registry_.emplace<HumanFactors>(site, 0.7f, 0.2f, 8.0f, 3, 1.0f);
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

void SimCore::updateModel(PlantModel& model)
{
    for (auto it = model.nodes_.begin(); it != model.nodes_.end(); ++it) {
        const QString& id = it.key();
        PlantNode& node = it.value();

        entt::entity e = entityFromId[id.toStdString()];

        if (auto* t = registry_.try_get<Tank>(e))
            node.dparams["level"] = t->level;

        if (auto* p = registry_.try_get<Pump>(e))
            node.dparams["flow"] = p->flow;

        if (auto* hx = registry_.try_get<HeatExchanger>(e))
            node.dparams["flow_rate"] = hx->flow_rate;

        if (auto* p = registry_.try_get<Pump>(e))
            node.bparams["running"] = p->running;

        if (auto* hx = registry_.try_get<HeatExchanger>(e))
            node.bparams["power_on"] = hx->power_on;
    }
}


