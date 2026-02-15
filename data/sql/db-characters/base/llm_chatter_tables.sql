-- --------------------------------------------------------
-- LLM Chatter Module Tables
-- Dynamic bot conversations powered by AI
-- --------------------------------------------------------

-- Event queue for game events that may trigger chatter
DROP TABLE IF EXISTS `llm_chatter_events`;
CREATE TABLE `llm_chatter_events` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `event_type` ENUM(
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
        'bot_group_aggro_loss'
    ) NOT NULL,
    `event_scope` ENUM('global', 'zone', 'player') NOT NULL DEFAULT 'zone',
    `zone_id` INT UNSIGNED DEFAULT NULL,
    `map_id` INT UNSIGNED DEFAULT NULL,
    `priority` TINYINT UNSIGNED NOT NULL DEFAULT 5,
    `cooldown_key` VARCHAR(64) DEFAULT NULL,
    `subject_guid` INT UNSIGNED DEFAULT NULL,
    `subject_name` VARCHAR(64) DEFAULT NULL,
    `target_guid` INT UNSIGNED DEFAULT NULL,
    `target_name` VARCHAR(128) DEFAULT NULL,
    `target_entry` INT UNSIGNED DEFAULT NULL,
    `extra_data` JSON DEFAULT NULL,
    `status` ENUM('pending', 'processing', 'completed', 'expired', 'skipped') NOT NULL DEFAULT 'pending',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `react_after` TIMESTAMP NULL DEFAULT NULL,
    `expires_at` TIMESTAMP NULL DEFAULT NULL,
    `processed_at` TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_status_priority` (`status`, `priority`, `created_at`),
    KEY `idx_zone` (`zone_id`, `status`),
    KEY `idx_cooldown` (`cooldown_key`, `created_at`),
    KEY `idx_react_after` (`status`, `react_after`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Queue for chatter requests (sent to Python bridge)
DROP TABLE IF EXISTS `llm_chatter_queue`;
CREATE TABLE `llm_chatter_queue` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `request_type` ENUM('statement', 'conversation') NOT NULL DEFAULT 'statement',
    `bot1_guid` INT UNSIGNED NOT NULL,
    `bot1_name` VARCHAR(64) NOT NULL,
    `bot1_class` VARCHAR(32) NOT NULL,
    `bot1_race` VARCHAR(32) NOT NULL,
    `bot1_level` TINYINT UNSIGNED NOT NULL,
    `bot1_zone` VARCHAR(128) NOT NULL,
    `zone_id` INT UNSIGNED DEFAULT NULL,
    `weather` VARCHAR(32) DEFAULT 'clear',
    `bot_count` TINYINT UNSIGNED NOT NULL DEFAULT 1,
    `bot2_guid` INT UNSIGNED DEFAULT NULL,
    `bot2_name` VARCHAR(64) DEFAULT NULL,
    `bot2_class` VARCHAR(32) DEFAULT NULL,
    `bot2_race` VARCHAR(32) DEFAULT NULL,
    `bot2_level` TINYINT UNSIGNED DEFAULT NULL,
    `bot3_guid` INT UNSIGNED DEFAULT NULL,
    `bot3_name` VARCHAR(64) DEFAULT NULL,
    `bot3_class` VARCHAR(32) DEFAULT NULL,
    `bot3_race` VARCHAR(32) DEFAULT NULL,
    `bot3_level` TINYINT UNSIGNED DEFAULT NULL,
    `bot4_guid` INT UNSIGNED DEFAULT NULL,
    `bot4_name` VARCHAR(64) DEFAULT NULL,
    `bot4_class` VARCHAR(32) DEFAULT NULL,
    `bot4_race` VARCHAR(32) DEFAULT NULL,
    `bot4_level` TINYINT UNSIGNED DEFAULT NULL,
    `status` ENUM('pending', 'processing', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'pending',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `processed_at` TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_status` (`status`),
    KEY `idx_created` (`created_at`),
    KEY `idx_zone` (`zone_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Messages to be delivered (from completed requests or events)
DROP TABLE IF EXISTS `llm_chatter_messages`;
CREATE TABLE `llm_chatter_messages` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `queue_id` INT UNSIGNED DEFAULT NULL,
    `event_id` INT UNSIGNED DEFAULT NULL,
    `sequence` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `bot_guid` INT UNSIGNED NOT NULL,
    `bot_name` VARCHAR(64) NOT NULL,
    `message` TEXT NOT NULL,
    `emote` VARCHAR(32) DEFAULT NULL,
    `channel` VARCHAR(32) NOT NULL DEFAULT 'general',
    `delivered` TINYINT(1) NOT NULL DEFAULT 0,
    `deliver_at` TIMESTAMP NULL DEFAULT NULL,
    `delivered_at` TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_queue` (`queue_id`),
    KEY `idx_event` (`event_id`),
    KEY `idx_delivery` (`delivered`, `deliver_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Personality traits for bots in player groups
DROP TABLE IF EXISTS `llm_group_bot_traits`;
CREATE TABLE `llm_group_bot_traits` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `group_id` INT UNSIGNED NOT NULL,
    `bot_guid` INT UNSIGNED NOT NULL,
    `bot_name` VARCHAR(64) NOT NULL,
    `trait1` VARCHAR(32) NOT NULL,
    `trait2` VARCHAR(32) NOT NULL,
    `trait3` VARCHAR(32) NOT NULL,
    `role` VARCHAR(16) DEFAULT NULL,
    `farewell_msg` VARCHAR(255) DEFAULT NULL,
    `assigned_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_group_bot` (`group_id`, `bot_guid`),
    INDEX `idx_group` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Chat history for General channel conversations (per-zone)
DROP TABLE IF EXISTS `llm_general_chat_history`;
CREATE TABLE `llm_general_chat_history` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `zone_id` INT UNSIGNED NOT NULL,
    `speaker_name` VARCHAR(64) NOT NULL,
    `is_bot` TINYINT(1) NOT NULL DEFAULT 0,
    `message` TEXT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_zone_id` (`zone_id`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Chat history for group conversations (provides context)
DROP TABLE IF EXISTS `llm_group_chat_history`;
CREATE TABLE `llm_group_chat_history` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `group_id` INT UNSIGNED NOT NULL,
    `speaker_guid` INT UNSIGNED NOT NULL,
    `speaker_name` VARCHAR(64) NOT NULL,
    `is_bot` TINYINT(1) NOT NULL DEFAULT 0,
    `message` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_group_id` (`group_id`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
