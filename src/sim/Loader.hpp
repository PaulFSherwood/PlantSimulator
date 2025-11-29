#pragma once
#include <string>
#include <unordered_map>
#include <entt/entt.hpp>


struct Loader {
    static bool loadPlant(
        const std::string& path,
        entt::registry& reg,
        std::unordered_map<std::string, entt::entity>& entityFromId
        );
};

