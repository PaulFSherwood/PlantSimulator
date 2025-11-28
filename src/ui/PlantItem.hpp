#pragma once
#include <QGraphicsRectItem>
#include <QGraphicsTextItem>
#include "../sim/Components.hpp"
#include "PlantNode.hpp"

class PlantItem : public QGraphicsRectItem {
public:
    PlantItem(const PlantNode& node);

    void updateFromNode(const PlantNode& node);

    QString id;
    QString type;

private:
    QGraphicsTextItem* text_;
};
