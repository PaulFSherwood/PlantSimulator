#pragma once
#include <QMainWindow>
#include <QGraphicsView>
#include <QGraphicsScene>
#include <QGraphicsRectItem>
#include <QGraphicsTextItem>
#include "../sim/SimCore.hpp"

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(QWidget* parent = nullptr);

private slots:
    void onFrameReady();

private:
    SimCore sim_;

    QGraphicsView* view_{nullptr};
    QGraphicsScene* scene_{nullptr};

    // For tracking entity graphics
    struct EntityVisual {
        QGraphicsRectItem* rect;
        QGraphicsTextItem* text;
    };
    std::unordered_map<entt::entity, EntityVisual> visuals_;

    void createVisuals();
    void updateVisuals();
};
