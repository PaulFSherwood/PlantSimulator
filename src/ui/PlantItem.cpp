#include "PlantItem.hpp"
#include <QPen>
#include <QBrush>
#include <QColor>
#include <QStringBuilder>

PlantItem::PlantItem(const PlantNode& node)
    : QGraphicsRectItem(0, 0, 160, 120),
    id(node.id),
    type(node.type)
{
    setPen(QPen(Qt::black, 2));
    setBrush(QColor("#dcecff"));

    text_ = new QGraphicsTextItem(this);
    updateFromNode(node);
}

void PlantItem::updateFromNode(const PlantNode& node)
{
    QString t = node.type + "\n";
    // numeric params
    for (auto it = node.dparams.constBegin(); it != node.dparams.constEnd(); ++it) {
        const QString& k = it.key();
        double v = it.value();
        // render parameter text here...
    }

    // boolean params
    for (auto it = node.bparams.constBegin(); it != node.bparams.constEnd(); ++it) {
        const QString& k = it.key();
        bool v = it.value();
        // render boolean values here...
    }

    text_->setPlainText(t);
    text_->setPos(10, 10);
}
