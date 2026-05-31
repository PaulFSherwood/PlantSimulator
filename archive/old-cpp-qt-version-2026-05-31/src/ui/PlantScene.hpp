#pragma once
#include <QHash>
#include <QGraphicsScene>
#include "PlantModel.hpp"
#include "PlantItem.hpp"

class PlantScene : public QGraphicsScene {
public:
    PlantScene(QObject* parent=nullptr);

    void build(const PlantModel& model);
    void updateValues(const PlantModel& model);

private:
    QHash<QString, PlantItem*> items_;
};
