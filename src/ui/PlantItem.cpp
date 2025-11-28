#include "PlantItem.hpp"
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
    for (auto& [k,v] : node.dparams)
        t += k + ": " + QString::number(v, 'f', 2) + "\n";
    for (auto& [k,v] : node.bparams)
        t += k + ": " + (v?"true":"false") + "\n";

    text_->setPlainText(t);
    text_->setPos(10, 10);
}
