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
    setBrush(QColor(50,50,60));

    text_ = new QGraphicsTextItem(this);
    updateFromNode(node);
}

void PlantItem::updateFromNode(const PlantNode& n)
{
    QString txt = QString("[%1]\n").arg(n.type);

    for (auto it = n.dparams.cbegin(); it != n.dparams.cend(); ++it) {
        txt += QString("%1: %2\n").arg(it.key()).arg(it.value(), 0, 'f', 2);
    }
    for (auto it = n.bparams.cbegin(); it != n.bparams.cend(); ++it) {
        txt += QString("%1: %2\n").arg(it.key()).arg(it.value() ? "true" : "false");
    }

    if (!text_) {
        text_ = new QGraphicsTextItem(this);
        text_->setDefaultTextColor(Qt::white);
        text_->setPos(10, 10);
    }

    text_->setPlainText(txt);
}

