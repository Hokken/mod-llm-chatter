-- Migration v8: Add missing ENUM values for group events
-- The C++ hooks insert these event types but they were missing from the ENUM:
-- bot_group_quest_complete, bot_group_levelup, bot_group_achievement, bot_group_spell_cast

ALTER TABLE llm_chatter_events MODIFY COLUMN event_type ENUM(
    'weather_change','holiday_start','holiday_end',
    'creature_death_boss','creature_death_rare','creature_death_guard',
    'player_enters_zone','bot_pvp_kill','bot_level_up','bot_achievement',
    'bot_quest_complete','world_boss_spawn','rare_spawn',
    'transport_arrives','day_night_transition','enemy_player_near',
    'bot_loot_item',
    'bot_group_join','bot_group_kill','bot_group_death',
    'bot_group_loot','bot_group_player_msg','bot_group_combat',
    'bot_group_quest_complete','bot_group_levelup','bot_group_achievement',
    'bot_group_spell_cast','bot_group_quest_objectives'
) NOT NULL;
