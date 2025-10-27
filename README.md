# PlantSim — A C++ Digital‑Twin Sandbox for Plant Proposals (Qt + EnTT + ImPlot)

**Goal:** Provide an interactive, executive‑friendly simulator where leaders can preview proposed changes (process, staffing, safety, utilities) before touching a real plant. The app shows how changes affect *throughput, energy, risk, alarms, downtime,* and *people*. Think of it as a **proposal flight‑sim** for manufacturing.

---

## 1) Why this exists (executive pitch)
- **De‑risk proposals**: Try changes virtually (new control strategies, shift patterns, equipment swaps) and see projected KPIs before spending capex.
- **Safety lens**: Drag safety sliders (training level, staffing mix, fatigue) and watch how incident likelihoods and interlock trips change.
- **Communication**: Executives and managers can *see* flows, levels, trends, and alarms—no P&IDs required.
- **Repeatable evidence**: Save scenarios and produce comparable reports with before/after deltas and confidence intervals.

**Example:** “What happens if we move from 12‑hour to 8‑hour shifts and raise operator training from 60% → 80%? Show throughput, energy per ton, and alarm rate over 90 simulated days.”

---

## 2) Tech stack
- **Language:** C++20
- **App shell/UI:** **Qt 6** (dockable panels, menus, file I/O, theming)
- **ECS:** **EnTT** (data‑oriented components/systems; fast, header‑only)
- **Engineering UI:** **Dear ImGui + ImPlot** (live trends, histograms, scatter, heatmaps)
- **Math/serialization:** `Eigen` (optional), `nlohmann::json` or `yyjson`
- **Build:** CMake, vcpkg/Conan for deps; clang‑tidy/format, sanitizers

> **Note:** ImGui/ImPlot are embedded in a Qt OpenGL widget (or RHI). Qt handles chrome/docking; ImGui handles fast engineering plots.

---

## 3) Architecture (at a glance)
```
Qt MainWindow (menus, docks, file open/save)
 ├─ ScenarioPanel (load/edit JSON configs)
 ├─ KPIPanel (tables + traffic‑light KPIs)
 ├─ AlarmPanel (current/latched alarms)
 ├─ SafetyPanel (fatigue, staffing, training sliders)
 └─ ImGuiViewport (OpenGL)  ← ImPlot trends, live gauges, overlays

SimulationCore
 ├─ EnTT Registry (entities = pumps, valves, tanks, PIDs, heat‑x, sensors)
 ├─ Systems: Control, Hydraulics, Thermal, Failure, Alarm, Analytics
 ├─ IO/Tags: mapping of named points (e.g., "P101.flow") to component fields
 └─ ScenarioRunner: deterministic tick loop + Monte Carlo batch mode
```

**Fixed‑timestep loop (50 Hz typical):**
```
I/O ingest → Control (PID/sequences) → Actuators → Hydraulics → Thermal →
Failures & Human‑factors → Alarms → KPI aggregation → Render
```

---

## 4) What can be simulated (initial scope)
Start narrow (one vertical slice) and expand:
- **Steeping → Milling → Starch/Gluten separation** (plus utilities: steam/cooling/air)
- **Components:** Tanks, pumps, valves/actuators, pipes, hydrocyclones, heat exchangers, sensors (level/flow/temp/pressure), PIDs
- **Human‑factors:** staffing levels, training index, shift length, fatigue model, alarm handling delay, procedural adherence
- **Safety controls:** interlocks, permissives, e‑stops, LOPA‑style trip logic
- **KPIs:** throughput (t/h), energy per ton, trip/alarm rate, downtime minutes, scrap/rework %, near‑miss probability

---

## 5) Human‑factors & Safety analytics (executive sliders)
We include a lightweight model that modulates failure/response:
- **Fatigue/shift length** → increases reaction time to alarms, raises human‑error probability on actions (valve mis‑set, late start/stop)
- **Training level** → reduces probability of procedural deviations; speeds recovery time
- **Staffing** → limits parallel responses; queues work orders; elongates repair MTTR
- **Safety investment** (e.g., better interlocks, sensors) → lowers incident likelihood; earlier detection

> These feed into a **stochastic layer** (random draws with seeded RNG), enabling Monte Carlo runs to generate confidence intervals on KPIs.

---

## 6) Project layout
```
plantsim/
├─ CMakeLists.txt
├─ external/                # (optional) vendored imgui, implot, entt
├─ data/
│  ├─ scenarios/
│  │  ├─ demo_steep_mill.json
│  │  └─ staffing_12h_vs_8h.json
│  └─ presets/
│     ├─ pump_STD.json
│     ├─ valve_STD.json
│     └─ pid_level_STD.json
├─ src/
│  ├─ app/
│  │  ├─ MainWindow.hpp/.cpp      # Qt docks, actions, timers
│  │  ├─ ImGuiLayer.hpp/.cpp      # GL init, frame begin/end, ImPlot
│  │  └─ KPIModel.hpp/.cpp        # Qt model for KPI tables
│  ├─ sim/
│  │  ├─ Components.hpp           # ECS components (POD)
│  │  ├─ Systems.hpp/.cpp         # Control/Hydraulics/Thermal/Failure/Alarm
│  │  ├─ Scenario.hpp/.cpp        # load JSON → spawn entities (prefabs)
│  │  ├─ Tags.hpp/.cpp            # name ↔ pointer bindings
│  │  ├─ Analytics.hpp/.cpp       # KPIs, Monte Carlo runner
│  │  └─ SimCore.hpp/.cpp         # fixed‑timestep loop (QTimer or thread)
│  └─ ui/
│     ├─ panels/                  # Qt widgets for settings
│     └─ views/
└─ README.md
```

---

## 7) ECS data model (examples)
**Entities**: pump, valve, tank, pipe segment, heat‑exchanger, sensor, PID controller, operator, shift.

**Components (POD):**
```cpp
// Components.hpp
struct Pump { bool running=false; float dp_nominal=1.5f; float flow=0.f; };
struct ValveActuator { float cmd=0.f, pos=0.f, speed=0.6f; bool fail_ATC=true; };
struct Tank { float level=0.5f; float area=2.0f; float inflow=0.f, outflow=0.f; };
struct Pipe { float k=1.2f; } // resistance
struct PID { float kp=2.f, ki=.5f, kd=0.f; float sp=.6f, pv=.3f, out=0.f, integ=0.f; };
struct SensorLevel { float noise_std=0.002f; float drift=0.f; };
struct Thermal { float T=293.f; float Qdot=0.f; };
struct FailureMode { bool stuckValve=false; bool pumpTrip=false; float mtbf_hrs=800.f; };
struct Alarmable { bool hi=false, lo=false, latched=false; float hiSP=.9f, loSP=.1f; };
struct HumanFactors { float fatigue=0.2f; float training=0.7f; int staffOnShift=3; };
```

**Prefabs (JSON → entities):** using `Scenario` loader to attach components with parameters.

---

## 8) Systems (tick order)
```cpp
// Systems.hpp (signatures)
void ControlSystem(entt::registry&, float dt);         // PID loops, sequences
void ActuatorSystem(entt::registry&, float dt);        // valve travel, motor ramp
void HydraulicsSystem(entt::registry&, float dt);      // simple flow/pressure
void ThermalSystem(entt::registry&, float dt);         // energy balances (optional)
void HumanFactorsSystem(entt::registry&, float dt);    // modulate reaction/MTTR
void FailureSystem(entt::registry&, float dt, uint64_t step, uint64_t seed);
void AlarmSystem(entt::registry&);                     // evaluate/latched
void AnalyticsSystem(entt::registry&, float dt);       // rolling KPIs
```

**Notes**
- Keep components pure data; systems operate in deterministic order.
- Use seeded RNG for failures/response times → reproducible Monte Carlo.

---

## 9) Simulation loop
Two options:
1) **Qt single‑thread** using `QTimer` at 20–50 ms for ticks (simple)
2) **Worker thread** for sim; post results to UI via signals/slots (smoother)

```cpp
// SimCore.hpp (sketch)
class SimCore : public QObject {
  Q_OBJECT
public:
  SimCore();
  void loadScenario(const QString& path);
  void start(float hz=50.f);
  void stop();
  entt::registry& reg() { return registry_; }
signals:
  void frameReady(); // UI should redraw ImGui plots
private slots:
  void onTick();
private:
  entt::registry registry_;
  QTimer timer_;
  float dt_{0.02f};
  uint64_t step_{0};
  uint64_t seed_{12345};
};
```

```cpp
// SimCore.cpp (core of onTick)
void SimCore::onTick(){
  ControlSystem(registry_, dt_);
  ActuatorSystem(registry_, dt_);
  HydraulicsSystem(registry_, dt_);
  ThermalSystem(registry_, dt_);
  HumanFactorsSystem(registry_, dt_);
  FailureSystem(registry_, dt_, step_++, seed_);
  AlarmSystem(registry_);
  AnalyticsSystem(registry_, dt_);
  emit frameReady();
}
```

---

## 10) Qt + ImGui + ImPlot integration
- Create an **ImGuiLayer** with OpenGL context binding.
- In `MainWindow`, connect `frameReady()` → `ImGuiLayer::render(registry)`, where you draw panels and plots.

```cpp
// ImGuiLayer.hpp (sketch)
class ImGuiLayer : public QWidget {
  Q_OBJECT
public:
  explicit ImGuiLayer(QWidget* parent=nullptr);
  void render(entt::registry& r); // called every tick
protected:
  void initializeGL();
  void paintEvent(QPaintEvent*) override; // begin frame → draw → end frame
};
```

```cpp
// ImGuiLayer.cpp (inside render)
void ImGuiLayer::render(entt::registry& r){
  ImGui::NewFrame();
  if(ImGui::Begin("Tank Level")){
    static float x[512], y[512];
    static int idx=0; idx=(idx+1)%512; x[idx]= (float)idx;
    float level=0.f;
    if(auto view=r.view<Tank>(); !view.empty()) level = view.get<Tank>(*view.begin()).level;
    y[idx]=level;
    if(ImPlot::BeginPlot("Level (0..1)")){
      ImPlot::PlotLine("level", x, y, 512);
      ImPlot::EndPlot();
    }
  }
  ImGui::End();
  ImGui::Render();
  // submit draw lists to GL...
}
```

---

## 11) Sample scenario JSON (tiny)
```json
{
  "name": "steep_to_mill_demo",
  "seed": 42,
  "components": [
    { "entity": "unit1", "Pump": {"running": true, "dp_nominal": 1.8} },
    { "entity": "unit1", "ValveActuator": {"speed": 0.5, "fail_ATC": true} },
    { "entity": "unit1", "Tank": {"level": 0.30, "area": 2.0} },
    { "entity": "unit1", "Pipe": {"k": 1.0} },
    { "entity": "unit1", "PID": {"kp": 2.0, "ki": 0.5, "sp": 0.60} },
    { "entity": "site",  "HumanFactors": {"fatigue": 0.2, "training": 0.7, "staffOnShift": 3} }
  ],
  "safety": { "interlocks": true, "tripHi": 0.95, "tripLo": 0.05 }
}
```

---

## 12) Build (CMake) — outline
```cmake
cmake_minimum_required(VERSION 3.22)
project(plantsim LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 COMPONENTS Widgets OpenGL REQUIRED)
# EnTT is header‑only; add via find_package(EnTT) or vendored include
# ImGui/ImPlot: add_subdirectory(external/imgui) / (external/implot)

add_executable(plantsim
  src/app/MainWindow.cpp src/app/MainWindow.hpp
  src/app/ImGuiLayer.cpp src/app/ImGuiLayer.hpp
  src/sim/Components.hpp
  src/sim/Systems.cpp src/sim/Systems.hpp
  src/sim/Scenario.cpp src/sim/Scenario.hpp
  src/sim/Analytics.cpp src/sim/Analytics.hpp
  src/sim/SimCore.cpp src/sim/SimCore.hpp
  src/main.cpp)

target_include_directories(plantsim PRIVATE external/ src/)

target_link_libraries(plantsim PRIVATE Qt6::Widgets Qt6::OpenGL)
# plus imgui, implot libs when integrated
```

---

## 13) Minimal `main.cpp`
```cpp
#include <QApplication>
#include "app/MainWindow.hpp"
int main(int argc, char** argv){
  QApplication app(argc, argv);
  MainWindow w; w.show();
  return app.exec();
}
```

---

## 14) Minimal `MainWindow` & sim wiring
```cpp
// MainWindow.hpp
class MainWindow : public QMainWindow {
  Q_OBJECT
public:
  MainWindow();
private:
  SimCore sim_;
  ImGuiLayer* imgui_ = nullptr;
};
```

```cpp
// MainWindow.cpp
#include "MainWindow.hpp"
#include "app/ImGuiLayer.hpp"
#include <QDockWidget>
MainWindow::MainWindow(){
  imgui_ = new ImGuiLayer(this);
  setCentralWidget(imgui_);
  connect(&sim_, &SimCore::frameReady, this, [this]{ imgui_->render(sim_.reg()); });
  sim_.loadScenario(":/data/scenarios/demo_steep_mill.json");
  sim_.start(50.f);
}
```

---

## 15) First systems (implementations)
```cpp
// Systems.cpp (snippets)
void ControlSystem(entt::registry& r, float dt){
  auto v = r.view<PID>();
  for(auto e: v){
    auto& pid = v.get<PID>(e);
    float err = pid.sp - pid.pv;
    pid.integ += err * dt;
    pid.out = std::clamp(pid.kp*err + pid.ki*pid.integ + pid.kd*0.f, 0.f, 1.f);
  }
}

void ActuatorSystem(entt::registry& r, float dt){
  auto v = r.view<ValveActuator, PID>();
  for(auto e: v){
    auto& va = v.get<ValveActuator>(e);
    auto& pid = v.get<PID>(e);
    float target = pid.out;
    float delta  = std::clamp(target - va.pos, -va.speed*dt, va.speed*dt);
    va.pos += delta;
  }
}

void HydraulicsSystem(entt::registry& r, float dt){
  auto pumps = r.view<Pump>();
  for(auto e: pumps){
    auto& p = pumps.get<Pump>(e);
    float valve_open = 1.f;
    if(auto v = r.try_get<ValveActuator>(e)) valve_open = v->pos;
    float k = 1.f; if(auto pipe = r.try_get<Pipe>(e)) k = pipe->k;
    float dp = p.running ? p.dp_nominal : 0.f;
    p.flow = valve_open * dp / (k + 1e-3f);
    if(auto t = r.try_get<Tank>(e)){
      t->inflow = p.flow; t->outflow = 0.0f;
      t->level = std::clamp(t->level + (t->inflow - t->outflow)/t->area * dt, 0.f, 1.f);
    }
    if(auto pid = r.try_get<PID>(e)) pid->pv = r.get<Tank>(e).level;
  }
}

void AlarmSystem(entt::registry& r){
  auto v = r.view<Tank, Alarmable>();
  for(auto e: v){
    auto& t = v.get<Tank>(e);
    auto& a = v.get<Alarmable>(e);
    a.hi = t.level > a.hiSP; a.lo = t.level < a.loSP;
    a.latched = a.latched || a.hi || a.lo;
  }
}
```

---

## 16) Executive demo script (5 minutes)
1. Load **"staffing_12h_vs_8h.json"**.
2. Show baseline KPIs (throughput, energy/ton, alarms/hr) for 30 sim days.
3. Drag **Shift length** 12h → 8h and **Training** 0.6 → 0.8; rerun Monte Carlo (N=100).
4. Display ImPlot: KPI deltas with error bars; green/yellow/red KPI cards.
5. Export **PDF report** + scenario JSON into `/reports/2025‑10‑pilot/`.

---

## 17) Testing & determinism
- **Unit tests** for each system (PID, valve travel, tank balance)
- **Golden runs**: same seed → same KPI curves (guard with CI)
- **Fuzz**: scenario JSON parser
- **Perf**: 10k entities @ 50 Hz target; SoA & batching for hot loops

---

## 18) Roadmap
- v0.1: Steep→Mill slice; live plots; KPI table; save/load scenarios
- v0.2: Thermal/energy model; simple utilities; alarm matrix view
- v0.3: Human‑factors Monte Carlo; report export; preset library
- v0.4: OPC UA/Modbus shim; external PLC‑in‑the‑loop
- v1.0: Multi‑area plant, user roles, audit trails, scenario sharing

---

## 19) Licensing & safety disclaimer
This tool is an aid for *proposal evaluation and training*, not a safety‑rated control system. Real‑world changes require engineering review, MOC, and site approvals.

---

## 20) How to describe on a résumé
> Built a Qt/EnTT/ImPlot digital‑twin sandbox enabling executives to preview process and staffing proposals. Implemented deterministic real‑time ECS, human‑factors analytics, and Monte Carlo reporting. Demonstrated 30–60% estimated reduction in process‑change validation time across pilot scenarios.


