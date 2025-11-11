#include "Loader.hpp"
#include "Components.hpp"
#include <fstream>
#include <nlohmann/json.hpp>
#include <iostream>

using json = nlohmann::json;

bool Loader::loadPlant(const std::string& path, entt::registry& reg) {
    std::ifstream in(path);
    if (!in.is_open()) {
        std::cerr << "Could not open " << path << "\n";
        return false;
    }

    json j;
    in >> j;
    if (!j.contains("components")) return false;

    for (auto& c : j["components"]) {
        std::string type = c.value("type", "");
        auto e = reg.create();

        if (type == "Pump")
            reg.emplace<Pump>(e, c.value("running", true),
                              c.value("dp_nominal", 1.8f),
                              c.value("flow", 0.0f));

        else if (type == "Tank")
            reg.emplace<Tank>(e, c.value("level", 0.3f),
                              c.value("area", 2.0f),
                              0.f, 0.f);

        else if (type == "HeatExchanger")
            reg.emplace<HeatExchanger>(e, c.value("power_on", true),
                                       c.value("comp_inlet_stream", 1.0f),
                                       c.value("comp_outlet_stream", 1.0f),
                                       c.value("flow_rate", 1.0f),
                                       c.value("tau_s", 5.0f),
                                       c.value("temp", 70.0f),
                                       c.value("pressure", 1.0f));
    }
    return true;
}
