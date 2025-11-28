#include "PlantLayout.hpp"
#include <QHash>

void PlantLayout::computeLayout(PlantModel& m)
{
    QSet<QString> visited;

    // find roots (nodes that no one outputs to)
    QHash<QString, bool> hasInput;
    for (auto it = m.edges_.begin(); it != m.edges_.end(); ++it) {
        const QString& a = it.key();
        const QList<QString>& outs = it.value();

        for (const QString& b : outs)
            hasInput[b] = true;
    }

    std::vector<QString> roots;
    for (auto it = m.nodes_.begin(); it != m.nodes_.end(); ++it) {
        const QString& id = it.key();
        // const PlantNode& node = it.value();  // unused but available

        if (!hasInput.contains(id))
            roots.push_back(id);
    }

    // BFS placing columns
    std::vector<QString> frontier = roots;
    int col = 0;

    while (!frontier.empty()) {
        std::vector<QString> next;
        int row = 0;

        for (const QString& id : frontier) {
            m.col_[id] = col;
            m.row_[id] = row++;
            visited.insert(id);

            for (const QString& o : m.edges_[id]) {
                if (!visited.contains(o))
                    next.push_back(o);
            }
        }

        frontier = next;
        col++;
    }
}
