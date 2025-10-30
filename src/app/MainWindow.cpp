#include "MainWindow.hpp"
#include <QStatusBar>
#include <QToolBar>
#include <QAction>

#include <entt/entt.hpp>
#include "../sim/Components.hpp"

MainWindow::MainWindow(QWidget* parent)
  : QMainWindow(parent) {
  // Simple UI shell
  auto* tb = addToolBar("Sim");
  auto* actStart = tb->addAction("Start");
  auto* actStop  = tb->addAction("Stop");
  kpiLabel_ = new QLabel("KPIs will appear here…", this);
  setCentralWidget(kpiLabel_);
  statusBar()->showMessage("Ready");

  connect(&sim_, &SimCore::frameReady, this, &MainWindow::onFrameReady);        // Plant Brain
  connect(actStart, &QAction::triggered, this, [this] { sim_.start(50.f); });
  connect(actStop,  &QAction::triggered, this, [this] { sim_.stop();       });

  // Load a tiny in-memory/default scenario
  sim_.loadDefaultScenario();
  sim_.start(50.f); // start ticking
}

void MainWindow::onFrameReady() {
  // Pull a couple of KPIs from the registry (very simple for the first build)
  auto& r = sim_.reg();

  // Tank level (first tank for now)
  float level = 0.f;
  if (auto vt = r.view<Tank>(); !vt.empty()) level = vt.get<Tank>(*vt.begin()).level;

  // Pumps running
  int pumpsRunning = 0;
  for(auto vp = r.view<Pump>(); auto e : vp) if (vp.get<Pump>(e).running) pumpsRunning++;

  // Human factors + KPIs (site singletons)
  float rt_mult = 1.0f;
  int alarms_active = 0;
  float downtime_min = 0.0f;

  if (auto v = r.view<HumanFactors>(); !v.empty()) {
    rt_mult = v.get<HumanFactors>(*v.begin()).reaction_time_mult;
  }
  if (auto vk = r.view<SiteKPI>(); !vk.empty()) {
    const auto& k = vk.get<SiteKPI>(*vk.begin());
    alarms_active = k.alarms_active;
    downtime_min = k.downtime_s / 60.0f;
  }

  kpiLabel_->setText(
    QString("Tank level: %1 (0..1)\n \\
          Pumps running: %2\n \\
          Alarms active: %3\n \\
          Downtime: %4 min\n \\
          Reaction-time x: %5\n \\
          Step: %6")
      .arg(level, 0, 'f', 3)
      .arg(pumpsRunning)
      .arg(alarms_active);
      .arg(downtime_min, 0, 'f', 2)
      .arg(rt_mult, 0, 'f', 2)
      .arg(sim_.step())
      );
}
