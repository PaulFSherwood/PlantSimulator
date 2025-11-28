#pragma once
#include "PlantItem.hpp"

class TankItem : public PlantItem {
public:
    TankItem(float level)
        : PlantItem("Tank", QColor("#A0C8FF")),
        level_(level)
    {}

    void setLevel(float l) { level_ = l; }

    void updateState() override {
        // Draw water level inside
        if (!levelItem_) {
            levelItem_ = new QGraphicsRectItem(this);
            levelItem_->setBrush(QColor("#3A7DFF"));
            levelItem_->setPen(Qt::NoPen);
        }
        float h = 60 * level_;
        levelItem_->setRect(10, 70 - h, 120, h);
    }

private:
    float level_;
    QGraphicsRectItem* levelItem_{nullptr};
};
