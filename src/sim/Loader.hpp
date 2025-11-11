#pragma once
#include <entt/entt.hpp>


struct Loader {
    static bool loadPlant(const std::string& path, entt::registry& reg);
};

