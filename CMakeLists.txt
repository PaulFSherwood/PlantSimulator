cmake_minimum_required(VERSION 3.22)
project(ExecSim LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable Qt's codegen
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORRC ON)

find_package(Qt6 COMPONENTS Widgets REQUIRED)

include(FetchContent)
# Header-only EnTT
FetchContent_Declare(
  entt
  GIT_REPOSITORY https://github.com/skypjack/entt.git
  GIT_TAG v3.13.2
)
FetchContent_MakeAvailable(entt)

add_executable(execsim
  src/main.cpp
  src/app/MainWindow.hpp src/app/MainWindow.cpp
  src/sim/Components.hpp
  src/sim/Systems.hpp src/sim/Systems.cpp
  src/sim/SimCore.hpp src/sim/SimCore.cpp
  src/sim/Loader.cpp
  src/sim/Loader.hpp
  library/plant_default.json
)
target_include_directories(execsim PRIVATE src)
target_link_libraries(execsim PRIVATE Qt6::Widgets EnTT::EnTT)

# On Windows, bundle Qt DLLs (optional for later):
# set(CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS_SKIP TRUE)
# include(InstallRequiredSystemLibraries)

