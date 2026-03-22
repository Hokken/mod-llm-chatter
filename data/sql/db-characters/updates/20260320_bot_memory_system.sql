-- --------------------------------------------------------
-- Consolidated migration: bot memory system
-- Brings a fresh origin/master install up to date with
-- the Playerbot branch as of 2026-03-20.
--
-- Changes:
--   1. Add bot_group_farewell to llm_chatter_events
--   2. Add tone column to llm_group_bot_traits
--   3. Create llm_bot_identities table
--   4. Create llm_bot_memories table
-- --------------------------------------------------------

-- 1. Add bot_group_farewell event type
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
        'bot_group_corpse_run',
        'player_general_msg',
        'minor_event',
        'bot_group_low_health',
        'bot_group_oom',
        'bot_group_aggro_loss',
        'bot_group_quest_accept',
        'bot_group_quest_accept_batch',
        'bot_group_discovery',
        'weather_ambient',
        'bot_group_nearby_object',
        'bot_group_join_batch',
        'bg_match_start',
        'bg_match_end',
        'bg_pvp_kill',
        'bg_flag_picked_up',
        'bg_flag_dropped',
        'bg_flag_captured',
        'bg_flag_returned',
        'bg_node_contested',
        'bg_node_captured',
        'bg_score_milestone',
        'bg_idle_chatter',
        'bg_player_arrival',
        'raid_boss_pull',
        'raid_boss_kill',
        'raid_boss_wipe',
        'raid_idle_morale',
        'bot_group_farewell'
    ) NOT NULL;

-- 2. Add tone column to llm_group_bot_traits
ALTER TABLE `llm_group_bot_traits`
    ADD COLUMN `tone` VARCHAR(120) DEFAULT NULL
    AFTER `role`;

-- 3. Persistent bot identities
CREATE TABLE IF NOT EXISTS `llm_bot_identities` (
    `bot_guid`         INT UNSIGNED NOT NULL PRIMARY KEY,
    `bot_name`         VARCHAR(12)  NOT NULL,
    `trait1`           VARCHAR(64)  NOT NULL,
    `trait2`           VARCHAR(64)  NOT NULL,
    `trait3`           VARCHAR(64)  NOT NULL,
    `role`             VARCHAR(32)  DEFAULT NULL,
    `farewell_msg`     VARCHAR(255) DEFAULT NULL,
    `identity_version` INT UNSIGNED NOT NULL DEFAULT 1,
    `created_at`       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Bot memories
CREATE TABLE IF NOT EXISTS `llm_bot_memories` (
    `id`            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `bot_guid`      INT UNSIGNED NOT NULL,
    `player_guid`   INT UNSIGNED NOT NULL,
    `group_id`      INT UNSIGNED NOT NULL,
    `memory_type`   ENUM(
        'ambient', 'boss_kill', 'wipe', 'rare_kill',
        'dungeon', 'party_member', 'player_message',
        'first_meeting', 'quest_complete', 'achievement',
        'level_up', 'bg_win', 'bg_loss',
        'discovery', 'pvp_kill'
    ) NOT NULL,
    `memory`        TEXT         NOT NULL,
    `mood`          VARCHAR(32)  NOT NULL,
    `emote`         VARCHAR(32)  DEFAULT NULL,
    `active`        TINYINT(1)   NOT NULL DEFAULT 0,
    `session_start` DOUBLE       NOT NULL,
    `created_at`    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_bot_player`        (`bot_guid`, `player_guid`),
    INDEX `idx_bot_player_active` (`bot_guid`, `player_guid`, `active`),
    INDEX `idx_group`             (`group_id`, `active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
