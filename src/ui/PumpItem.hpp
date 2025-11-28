#pragma once
#include "PlantItem.hpp"

class PumpItem : public PlantItem {
public:
    PumpItem(bool running)
        : PlantItem("Pump", running ? QColor("#7DE77A") : QColor("#E77A7A")),
        running_(running)
    {}

    void setRunning(bool r) { running_ = r; }
    void updateState() override {
        setBrush(running_ ? QColor("#7DE77A") : QColor("#E77A7A"));
    }

private:
    bool running_;
};
