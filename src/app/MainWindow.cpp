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

  connect(&sim_, &SimCore::frameReady, this, &MainWindow::onFrameReady);
  connect(actStart, &QAction::triggered, this, [this] { sim_.start(50.f); });
  connect(actStop,  &QAction::triggered, this, [this] { sim_.stop();       });

  // Load a tiny in-memory/default scenario
  sim_.loadDefaultScenario();
  sim_.start(50.f); // start ticking
}

void MainWindow::onFrameReady() {
  // Pull a couple of KPIs from the registry (very simple for the first build)
  auto& r = sim_.reg();
  float level = 0.f;
  int pumpsRunning = 0;

  auto vt = r.view<Tank>();
  if(!vt.empty()) level = vt.get<Tank>(*vt.begin()).level;

  auto vp = r.view<Pump>();
  for(auto e : vp) if (vp.get<Pump>(e).running) pumpsRunning++;

  kpiLabel_->setText(
    QString("Tank level: %1 (0..1)\nPumps running: %2\nStep: %3")
      .arg(level, 0, 'f', 3).arg(pumpsRunning).arg(sim_.step()));
}
