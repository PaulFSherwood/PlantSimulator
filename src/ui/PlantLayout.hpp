#pragma once
#include <vector>
#include <QGraphicsScene>

class PlantLayout {
public:
    template<typename T>
    static void addItem(QGraphicsScene* scene, T* item, int index) {
        const int spacing = 40;
        item->setPos(index * (160 + spacing), 0);
        scene->addItem(item);
    }
};
