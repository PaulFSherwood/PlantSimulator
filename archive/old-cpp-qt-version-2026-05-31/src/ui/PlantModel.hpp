#pragma once
#include "PlantNode.hpp"
#include <QHash>
#include <QJsonObject>
#include <QString>
#include <unordered_map>

class PlantModel {
public:
    bool loadFromFile(const QString& path);

    const PlantNode& node(const QString& id) const { return nodes_.value(id); }

    bool has(const QString& id) const { return nodes_.count(id) > 0; }

    QHash<QString, PlantNode> nodes_;

    // adjacency
    QHash<QString, QVector<QString>> edges_;

    // layout columns
    QHash<QString, int> col_;
    QHash<QString, int> row_;

};
