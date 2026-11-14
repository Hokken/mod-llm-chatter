#ifndef MOD_LLM_CHATTER_SCENE_CLOSURE_H
#define MOD_LLM_CHATTER_SCENE_CLOSURE_H

/*
 * mod-llm-chatter - closed proximity scenes (pure part)
 *
 * Standard library only, so the closure decisions can be
 * unit-tested outside the server build
 * (tools/tests/cpp/test_group_guard.cpp).
 *
 * A proximity scene is closed when a line of it was dropped
 * because its speaker's group changed (issue #94). From then on
 * no row of that scene may be spoken, even one committed later
 * by the bridge (lines are inserted one by one), no reply to it
 * may be spoken, and delivering a row may not recreate it.
 *
 * Scene identity: a scene is keyed by the event id of its rows.
 * A proximity_reply row starts a scene under its own event id
 * and continues the scene named by its scene_id.
 */

#include <cstdint>
#include <ctime>
#include <map>

namespace LLMChatterSceneClosure
{

class ClosedScenes
{
public:
    void Close(std::uint32_t sceneId, std::time_t now,
               std::time_t retentionSeconds)
    {
        Prune(now, retentionSeconds);
        if (sceneId)
            _closed[sceneId] = now;
    }

    bool IsClosed(std::uint32_t sceneId) const
    {
        return sceneId && _closed.count(sceneId) > 0;
    }

    void Prune(std::time_t now, std::time_t retentionSeconds)
    {
        for (auto it = _closed.begin(); it != _closed.end();)
        {
            if (now - it->second > retentionSeconds)
                it = _closed.erase(it);
            else
                ++it;
        }
    }

private:
    std::map<std::uint32_t, std::time_t> _closed;
};

// True when a proximity row belongs to a closed scene: its own
// event's scene, or (for a reply) the scene it continues.
inline bool RowBelongsToClosedScene(
    ClosedScenes const& closed, std::uint32_t eventId,
    std::uint32_t originSceneId)
{
    return closed.IsClosed(eventId) || closed.IsClosed(originSceneId);
}

} // namespace LLMChatterSceneClosure

#endif // MOD_LLM_CHATTER_SCENE_CLOSURE_H
