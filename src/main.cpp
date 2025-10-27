#include <QApplication>
#include "app/MainWindow.hpp"

int main(int argc, char** argv) {
  QApplication app(argc, argv);
  MainWindow w;
  w.resize(960, 600);
  w.show();
  return app.exec();
}
