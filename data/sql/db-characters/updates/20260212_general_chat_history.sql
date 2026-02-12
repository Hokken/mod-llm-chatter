-- Migration: Add General channel chat history table and ENUM value
-- Date: 2026-02-12

-- 1. Create llm_general_chat_history table
CREATE TABLE IF NOT EXISTS `llm_general_chat_history` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `zone_id` INT UNSIGNED NOT NULL,
    `speaker_name` VARCHAR(64) NOT NULL,
    `is_bot` TINYINT(1) NOT NULL DEFAULT 0,
    `message` TEXT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_zone_id` (`zone_id`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Add 'player_general_msg' to event_type ENUM
ALTER TABLE `llm_chatter_events`
    MODIFY COLUMN `event_type` ENUM(
        'weather_change',
        'holiday_start',
        'holiday_end',
        'creature_death_boss',
        'creature_death_rare',
        'creature_death_guard',
        'player_enters_zone',
        'bot_pvp_kill',
        'bot_level_up',
        'bot_achievement',
        'bot_quest_complete',
        'world_boss_spawn',
        'rare_spawn',
        'transport_arrives',
        'day_night_transition',
        'enemy_player_near',
        'bot_loot_item',
        'bot_group_join',
        'bot_group_kill',
        'bot_group_death',
        'bot_group_loot',
        'bot_group_player_msg',
        'bot_group_combat',
        'bot_group_levelup',
        'bot_group_quest_complete',
        'bot_group_achievement',
        'bot_group_spell_cast',
        'bot_group_quest_objectives',
        'bot_group_resurrect',
        'bot_group_zone_transition',
        'bot_group_dungeon_entry',
        'bot_group_wipe',
        'player_general_msg'
    ) NOT NULL;
