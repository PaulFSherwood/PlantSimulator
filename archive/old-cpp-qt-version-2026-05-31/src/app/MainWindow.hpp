#pragma once
#include <QMainWindow>
#include <QGraphicsView>
#include "../sim/SimCore.hpp"
#include "../ui/PlantScene.hpp"
#include "../ui/PlantModel.hpp"
#include "../ui/PlantLayout.hpp"

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(QWidget* parent = nullptr);

private slots:
    void onFrameReady();

private:
    SimCore sim_;

    QGraphicsView* view_{nullptr};
    PlantScene* pscene_{nullptr};
    PlantModel model_;
};
