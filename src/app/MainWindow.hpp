#pragma once
#include <QMainWindow>
#include <QLabel>
#include <QTimer>
#include "../sim/SimCore.hpp"

class MainWindow : public QMainWindow {
  Q_OBJECT
public:
  MainWindow(QWidget* parent=nullptr);
private slots:
  void onFrameReady();
private:
  SimCore sim_;
  QLabel* kpiLabel_{nullptr}; // simple visible output for now
};
