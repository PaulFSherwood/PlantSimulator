#pragma once
#include <QObject>
#include <QTimer>
#include <entt/entt.hpp>

class SimCore : public QObject {
  Q_OBJECT
public:
  explicit SimCore(QObject* parent=nullptr);
  void loadDefaultScenario();
  void start(float hz=50.f);
  void stop();

  entt::registry& reg() { return registry_; }
  quint64 step() const { return step_; }

signals:
  void frameReady();

private slots:
  void onTick();

private:
  entt::registry registry_;
  QTimer timer_;
  float dt_{0.02f};
  quint64 step_{0};
};
