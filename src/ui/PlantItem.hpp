#pragma once
#include <QGraphicsRectItem>
#include <QGraphicsTextItem>

class PlantItem : public QGraphicsRectItem {
public:
    PlantItem(const QString& label, const QColor& color, QGraphicsItem* parent = nullptr)
        : QGraphicsRectItem(parent)
    {
        setRect(0, 0, 140, 80);
        setBrush(color);
        setPen(QPen(Qt::black, 2));

        label_ = new QGraphicsTextItem(label, this);
        label_->setDefaultTextColor(Qt::black);
        label_->setPos(10, 10);
    }

    virtual void updateState() {} // overridden by subclasses

protected:
    QGraphicsTextItem* label_{nullptr};
};
