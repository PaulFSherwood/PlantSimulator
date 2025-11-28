#pragma once
#include "PlantItem.hpp"

class HeatExchangerItem : public PlantItem {
public:
    HeatExchangerItem(bool on)
        : PlantItem("HeatExchanger", QColor("#FFE9A0")),
        power_on_(on)
    {}

    void setPower(bool p) { power_on_ = p; }

    void updateState() override {
        setPen(power_on_ ? QPen(Qt::yellow, 3) : QPen(Qt::darkGray, 2));
    }

private:
    bool power_on_;
};
