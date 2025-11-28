#include "MainWindow.hpp"
#include "../sim/Components.hpp"

#include <QToolBar>
#include <QStatusBar>
#include <QAction>
#include <QPen>
#include <QBrush>
#include <QColor>
#include <cmath>

MainWindow::MainWindow(QWidget* parent)
    : QMainWindow(parent)
{
    auto* tb = addToolBar("Sim");
    auto* actStart = tb->addAction("Start");
    auto* actStop  = tb->addAction("Stop");
    statusBar()->showMessage("Ready");

    // --- Scene and View setup ---
    scene_ = new QGraphicsScene(this);
    view_ = new QGraphicsView(scene_, this);
    view_->setRenderHint(QPainter::Antialiasing);
    view_->setBackgroundBrush(Qt::white);
    setCentralWidget(view_);


    // --- Connect simulation ---
    connect(&sim_, &SimCore::frameReady, this, &MainWindow::onFrameReady);
    connect(actStart, &QAction::triggered, this, [this] { sim_.start(50.f); });
    connect(actStop,  &QAction::triggered, this, [this] { sim_.stop(); });

    sim_.loadDefaultScenario();
    sim_.start(50.f);

    createVisuals();
}

void MainWindow::createVisuals() {
    auto& r = sim_.reg();
    scene_->clear();
    visuals_.clear();

    int index = 0;
    const double spacing = 200.0;

    // Iterate over ALL entities
    for (auto e : r.view<entt::entity>()) {

        bool hasComponent =
            r.any_of<Pump>(e) ||
            r.any_of<Tank>(e) ||
            r.any_of<HeatExchanger>(e);

        if (!hasComponent)
            continue;

        QString name = "Entity " + QString::number(index + 1);
        double x = 50.0 + index * spacing;
        double y = 100.0;

        auto rect = scene_->addRect(
            QRectF(x, y, 140, 80),
            QPen(Qt::darkBlue, 2),
            QBrush(QColor(200, 230, 255))
            );
        rect->setData(0, QVariant::fromValue(static_cast<int>(e)));

        auto text = scene_->addText(name);
        text->setPos(x + 10, y + 10);

        visuals_[e] = {rect, text};
        index++;
    }
}


void MainWindow::updateVisuals() {
    auto& r = sim_.reg();

    for (auto& [e, vis] : visuals_) {
        QString info;

        if (auto* t = r.try_get<Tank>(e))
            info += QString("Lvl: %1\n").arg(t->level, 0, 'f', 2);

        if (auto* p = r.try_get<Pump>(e))
            info += QString("Flow: %1\n").arg(p->flow, 0, 'f', 2);

        if (auto* hx = r.try_get<HeatExchanger>(e))
            info += QString("HX Out: %1\n").arg(hx->comp_outlet_stream, 0, 'f', 2);

        vis.text->setPlainText(info);

        // Adaptive coloring
        QColor fill = QColor(180, 220, 250);

        if (auto* t = r.try_get<Tank>(e)) {
            if (t->level > 0.8)      fill = QColor(255, 180, 180);
            else if (t->level < 0.2) fill = QColor(180, 255, 180);
        }

        vis.rect->setBrush(fill);
    }
}


void MainWindow::onFrameReady() {
    updateVisuals();
    scene_->update();
}
