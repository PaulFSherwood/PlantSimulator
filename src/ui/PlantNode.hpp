#pragma once
#include <QHash>
#include <QString>
#include <vector>
#include <unordered_map>

struct PlantNode {
    QString id;
    QString type;
    // std::unordered_map<QString, double> dparams;
    // std::unordered_map<QString, bool> bparams;
    QHash<QString, double> dparams;                 // numeric params
    QHash<QString, bool> bparams;                   // bool params

    std::vector<QString> outputs;                   // connections (IDs)
};
