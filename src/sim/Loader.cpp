#include "Loader.hpp"
#include "Components.hpp"
#include <fstream>
#include <nlohmann/json.hpp>
#include <iostream>

using json = nlohmann::json;

bool Loader::loadPlant(const std::string& path,
                       entt::registry& reg,
                       std::unordered_map<std::string, entt::entity>& entityFromId)
{
    std::ifstream in(path);
    if (!in.is_open()) {
        std::cerr << "Could not open " << path << "\n";
        return false;
    }

    json j;
    in >> j;
    if (!j.contains("components"))
        return false;

    for (auto& c : j["components"])
    {
        std::string id   = c.value("id", "");
        std::string type = c.value("type", "");

        // Create ECS entity
        entt::entity e = reg.create();

        // Store mapping id → entity
        if (!id.empty())
            entityFromId[id] = e;

        auto& params = c["params"];

        if (type == "Pump") {
            reg.emplace<Pump>(e,
                              params.value("running",    true),
                              params.value("dp_nominal", 1.8f),
                              0.0f);
        }
        else if (type == "Tank") {
            reg.emplace<Tank>(e,
                              params.value("level", 0.3f),
                              params.value("area",  2.0f),
                              0.f, 0.f);
        }
        else if (type == "HeatExchanger") {
            reg.emplace<HeatExchanger>(e,
                                       params.value("power_on",            true),
                                       params.value("comp_inlet_stream",   1.0f),
                                       params.value("comp_outlet_stream",  1.0f),
                                       params.value("flow_rate",           1.0f),
                                       params.value("tau_s",               5.0f),
                                       params.value("temp",                70.0f),
                                       params.value("pressure",            1.0f));
        }
    }

    return true;
}

