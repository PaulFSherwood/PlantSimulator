#include "PlantModel.hpp"
#include <QFile>
#include <QJsonDocument>
#include <QJsonArray>

bool PlantModel::loadFromFile(const QString& path)
{
    QFile f(path);
    if (!f.open(QIODevice::ReadOnly))
        return false;

    QByteArray data = f.readAll();
    QJsonDocument doc = QJsonDocument::fromJson(data);
    if (!doc.isObject()) return false;

    auto root = doc.object();
    auto arr = root["components"].toArray();

    for (auto compVal : arr) {
        auto comp = compVal.toObject();

        PlantNode n;
        n.id = comp["id"].toString();
        n.type = comp["type"].toString();

        // load params
        auto params = comp["params"].toObject();
        for (auto it = params.begin(); it != params.end(); ++it) {
            if (it.value().isBool()) {
                n.bparams[it.key()] = it.value().toBool();
            } else if (it.value().isDouble()) {
                n.dparams[it.key()] = it.value().toDouble();
            }
        }

        // outputs
        for (auto out : comp["outputs"].toArray()) {
            QString s = out.toString();
            n.outputs.push_back(s);
            edges_[n.id].push_back(s);   // works with QVector<QString>
        }


        nodes_[n.id] = n;
    }

    return true;
}
