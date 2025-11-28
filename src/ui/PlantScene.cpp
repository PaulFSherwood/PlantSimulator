#include "PlantScene.hpp"
#include <QGraphicsLineItem>

PlantScene::PlantScene(QObject* parent)
    : QGraphicsScene(parent)
{}

void PlantScene::build(const PlantModel& m)
{
    clear();
    items_.clear();

    const int X_SPACING = 220;
    const int Y_SPACING = 160;

    // Create components
    for (auto& [id, node] : m.nodes_) {
        auto* item = new PlantItem(node);

        double x = m.col_.at(id) * X_SPACING;
        double y = m.row_.at(id) * Y_SPACING;

        item->setPos(x, y);
        addItem(item);

        items_[id] = item;
    }

    // Draw arrows
    for (auto& [a, outs] : m.edges_) {
        auto* A = items_[a];
        QPointF aCenter = A->sceneBoundingRect().center();

        for (auto& b : outs) {
            auto* B = items_[b];
            QPointF bCenter = B->sceneBoundingRect().center();

            auto* line = addLine(
                aCenter.x(), aCenter.y(),
                bCenter.x(), bCenter.y(),
                QPen(Qt::black, 2)
                );
        }
    }
}

void PlantScene::updateValues(const PlantModel& m)
{
    for (auto& [id, node] : m.nodes_) {
        items_[id]->updateFromNode(node);
    }
}
