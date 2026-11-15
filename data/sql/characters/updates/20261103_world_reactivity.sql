-- World reactivity (letters and rumors).
-- Triggers wait here until the bridge reads them. This is not
-- llm_chatter_events: startup expires every pending event there, and
-- a letter earned just before a restart must not be lost.
CREATE TABLE IF NOT EXISTS `llm_reactivity_inbox` (
    `id`          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `kind`        ENUM('achievement', 'quest', 'level', 'login') NOT NULL,
    `player_guid` INT UNSIGNED NOT NULL,
    `trigger_id`  INT UNSIGNED NOT NULL DEFAULT 0,
    `extra_data`  TEXT,
    -- Failed handling attempts; a row at the bridge's limit is kept
    -- for inspection but no longer picked up.
    `attempts`    TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `created_at`  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- One row per letter, from scheduling to delivery. The unique key is
-- what keeps a dungeon with several achievements to a single letter.
CREATE TABLE IF NOT EXISTS `llm_reactivity_letters` (
    `id`          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `player_guid` INT UNSIGNED NOT NULL,
    `kind`        ENUM('memory', 'dungeon', 'raid', 'quest',
                       'starter', 'profession') NOT NULL,
    `letter_key`  VARCHAR(64) NOT NULL,
    `status`      ENUM('scheduled', 'generating', 'ready', 'sending',
                       'sent', 'failed', 'skipped')
                  NOT NULL DEFAULT 'scheduled',
    `not_before`  DATETIME NOT NULL,
    `team`        ENUM('Alliance', 'Horde') NOT NULL,
    `sender_type` ENUM('creature', 'bot') NOT NULL DEFAULT 'creature',
    `sender_id`   INT UNSIGNED NOT NULL DEFAULT 0,
    `subject`     VARCHAR(128) DEFAULT NULL,
    `body`        TEXT DEFAULT NULL,
    `items`       VARCHAR(255) DEFAULT NULL,
    `context`     TEXT DEFAULT NULL,
    `attempts`    TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `created_at`  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP,
    `sent_at`     DATETIME DEFAULT NULL,
    UNIQUE KEY `uq_player_letter` (`player_guid`, `kind`, `letter_key`),
    INDEX `idx_status_due` (`status`, `not_before`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Per-character letter pacing. Rolled once, so a level is not re-rolled
-- at every login.
CREATE TABLE IF NOT EXISTS `llm_reactivity_player_state` (
    `player_guid`           INT UNSIGNED NOT NULL PRIMARY KEY,
    `team`                  ENUM('Alliance', 'Horde') NOT NULL,
    `next_memory_at`        DATETIME DEFAULT NULL,
    `starter_one_level`     TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `starter_two_level`     TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `starter_one_skill`     VARCHAR(32) DEFAULT NULL,
    `next_profession_level` TINYINT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Rumors about a player that have been unlocked or told. A deed from
-- before this feature gets a row the first time it is told, not fresh.
CREATE TABLE IF NOT EXISTS `llm_reactivity_rumors` (
    `player_guid`    INT UNSIGNED NOT NULL,
    `kind`           ENUM('achievement', 'quest', 'dungeon') NOT NULL,
    `rumor_key`      VARCHAR(64) NOT NULL,
    `fresh`          TINYINT(1) NOT NULL DEFAULT 0,
    `voiced_count`   INT UNSIGNED NOT NULL DEFAULT 0,
    `last_voiced_at` TIMESTAMP NULL DEFAULT NULL,
    `created_at`     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`player_guid`, `kind`, `rumor_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- A rumor line queued for speech. It only counts as voiced once the
-- message row shows it was delivered.
CREATE TABLE IF NOT EXISTS `llm_reactivity_rumor_voicings` (
    `id`          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `event_id`    INT UNSIGNED NOT NULL,
    `player_guid` INT UNSIGNED NOT NULL,
    `kind`        ENUM('achievement', 'quest', 'dungeon') NOT NULL,
    `rumor_key`   VARCHAR(64) NOT NULL,
    `created_at`  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_event` (`event_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Where a fresh rumor may be told, read by proximity scans. Zone 0
-- means anywhere.
CREATE TABLE IF NOT EXISTS `llm_reactivity_fresh_rumor_zones` (
    `player_guid` INT UNSIGNED NOT NULL,
    `zone_id`     INT UNSIGNED NOT NULL,
    `kind`        ENUM('achievement', 'quest', 'dungeon') NOT NULL,
    `rumor_key`   VARCHAR(64) NOT NULL,
    PRIMARY KEY (`player_guid`, `zone_id`, `kind`, `rumor_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
