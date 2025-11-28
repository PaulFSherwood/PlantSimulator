#include "MainWindow.hpp"
#include <QToolBar>
#include <QStatusBar>
#include <QAction>

MainWindow::MainWindow(QWidget* parent)
    : QMainWindow(parent)
{
    auto* tb = addToolBar("Sim");
    auto* actStart = tb->addAction("Start");
    auto* actStop  = tb->addAction("Stop");
    statusBar()->showMessage("Ready");

    // Scene + view
    pscene_ = new PlantScene(this);
    view_ = new QGraphicsView(pscene_, this);
    view_->setRenderHint(QPainter::Antialiasing);
    view_->setBackgroundBrush(QColor("#303030"));
    setCentralWidget(view_);

    // Load JSON model
    model_.loadFromFile("plant_default.json");

    // Compute layout
    PlantLayout::computeLayout(model_);

    // Build visuals
    pscene_->build(model_);

    // Connect simulation and start
    connect(&sim_, &SimCore::frameReady, this, &MainWindow::onFrameReady);
    sim_.loadDefaultScenario();
    sim_.start(50.f);

    connect(actStart, &QAction::triggered, this, [this] { sim_.start(50.f); });
    connect(actStop,  &QAction::triggered, this, [this] { sim_.stop(); });
}

void MainWindow::onFrameReady() {
    // Update JSON model with ECS values
    sim_.updateModel(model_);

    // Update scene text
    pscene_->updateValues(model_);
}
