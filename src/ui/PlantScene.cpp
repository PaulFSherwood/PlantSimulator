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
    for (auto it = m.nodes_.begin(); it != m.nodes_.end(); ++it) {
        const QString& id = it.key();
        const PlantNode& node = it.value();

        auto* item = new PlantItem(node);

        double x = m.col_[id] * X_SPACING;
        double y = m.row_[id] * Y_SPACING;

        item->setPos(x, y);
        addItem(item);

        items_[id] = item;
    }

    // Draw arrows
    for (auto it = m.edges_.begin(); it != m.edges_.end(); ++it) {
        const QString& a = it.key();
        const QList<QString>& outs = it.value();

        auto* A = items_[a];
        QPointF aCenter = A->sceneBoundingRect().center();

        for (const QString& b : outs) {
            auto* B = items_[b];
            QPointF bCenter = B->sceneBoundingRect().center();

            addLine(aCenter.x(), aCenter.y(),
                    bCenter.x(), bCenter.y(),
                    QPen(Qt::black, 2));
        }
    }
}

void PlantScene::updateValues(const PlantModel& m)
{
    for (auto it = m.nodes_.cbegin(); it != m.nodes_.cend(); ++it) {
        const QString& id = it.key();
        const PlantNode& node = it.value();
        items_[id]->updateFromNode(node);
    }
}
