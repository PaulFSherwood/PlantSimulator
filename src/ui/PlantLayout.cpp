#include "PlantLayout.hpp"
#include <QHash>

void PlantLayout::computeLayout(PlantModel& m)
{
    QSet<QString> visited;

    // find roots (nodes that no one outputs to)
    QHash<QString, bool> hasInput;
    for (auto& [a, outs] : m.edges_) {
        for (auto& b : outs)
            hasInput[b] = true;
    }

    std::vector<QString> roots;
    for (auto& [id, node] : m.nodes_) {
        if (!hasInput[id])
            roots.push_back(id);
    }

    // BFS placing columns
    std::vector<QString> frontier = roots;
    int col = 0;

    while (!frontier.empty()) {
        std::vector<QString> next;
        int row = 0;

        for (auto& id : frontier) {
            m.col_[id] = col;
            m.row_[id] = row++;
            visited.insert(id);

            for (auto& o : m.edges_[id]) {
                if (!visited.count(o))
                    next.push_back(o);
            }
        }

        frontier = next;
        col++;
    }
}
