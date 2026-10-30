-- Voice (TTS) mailbox: one row per line the bound listener received.
-- The host agent plays a row only while its generation matches the
-- listener presence row and it has not passed expires_at.
CREATE TABLE IF NOT EXISTS `llm_chatter_voice` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `account_id` INT UNSIGNED NOT NULL,
    `listener_guid` INT UNSIGNED NOT NULL,
    `generation` BIGINT UNSIGNED NOT NULL,
    `message_id` INT UNSIGNED DEFAULT NULL,
    `speaker_guid` INT UNSIGNED NOT NULL,
    `speaker_kind` ENUM('bot', 'npc') NOT NULL,
    `speaker_race` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `speaker_gender` TINYINT UNSIGNED NOT NULL DEFAULT 2,
    `speaker_class` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `channel` VARCHAR(16) NOT NULL,
    `text` TEXT NOT NULL,
    `distance` FLOAT NOT NULL,
    `rel_angle` FLOAT NOT NULL,
    `speaker_x` FLOAT NOT NULL,
    `speaker_y` FLOAT NOT NULL,
    `speaker_z` FLOAT NOT NULL,
    `map_id` INT UNSIGNED NOT NULL,
    `instance_id` INT UNSIGNED NOT NULL,
    `state` ENUM('pending', 'claimed', 'playing', 'played', 'expired')
        NOT NULL DEFAULT 'pending',
    `created_at` TIMESTAMP(3) NOT NULL,
    `expires_at` TIMESTAMP(3) NOT NULL,
    -- Playback lease: set by the agent when the clip actually starts.
    `play_until` TIMESTAMP(3) NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_poll` (`account_id`, `state`, `id`),
    KEY `idx_created` (`created_at`),
    KEY `idx_message` (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Current listener per bound account. generation only moves forward,
-- so out-of-order async writes cannot revive an older session.
CREATE TABLE IF NOT EXISTS `llm_chatter_voice_listener` (
    `account_id` INT UNSIGNED NOT NULL,
    `generation` BIGINT UNSIGNED NOT NULL,
    `listener_guid` INT UNSIGNED NOT NULL DEFAULT 0,
    `map_id` INT UNSIGNED NOT NULL DEFAULT 0,
    `instance_id` INT UNSIGNED NOT NULL DEFAULT 0,
    `updated_at` TIMESTAMP(3) NOT NULL,
    PRIMARY KEY (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Live geometry of speakers whose clip is playing, so the agent can
-- follow movement. One reused row per speaker; written only while a
-- playback lease is active.
CREATE TABLE IF NOT EXISTS `llm_chatter_voice_live` (
    `account_id` INT UNSIGNED NOT NULL,
    `speaker_kind` ENUM('bot', 'npc') NOT NULL,
    `speaker_guid` INT UNSIGNED NOT NULL,
    `generation` BIGINT UNSIGNED NOT NULL,
    `listener_guid` INT UNSIGNED NOT NULL,
    `distance` FLOAT NOT NULL,
    `rel_angle` FLOAT NOT NULL,
    -- Speaker world position, for camera-relative panning.
    `speaker_x` FLOAT NOT NULL DEFAULT 0,
    `speaker_y` FLOAT NOT NULL DEFAULT 0,
    `updated_at` TIMESTAMP(3) NOT NULL,
    PRIMARY KEY (`account_id`, `speaker_kind`, `speaker_guid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Upgrade a mailbox created before playback leases existed
-- (idempotent: MODIFY is repeatable, the column add is guarded).
ALTER TABLE `llm_chatter_voice`
    MODIFY COLUMN `state`
        ENUM('pending', 'claimed', 'playing', 'played', 'expired')
        NOT NULL DEFAULT 'pending';

SET @col_exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME   = 'llm_chatter_voice'
    AND COLUMN_NAME  = 'play_until'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE `llm_chatter_voice`
     ADD COLUMN `play_until` TIMESTAMP(3) NULL DEFAULT NULL
     AFTER `expires_at`',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists = (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME   = 'llm_chatter_voice'
    AND INDEX_NAME   = 'idx_message'
);
SET @sql = IF(@idx_exists = 0,
  'ALTER TABLE `llm_chatter_voice` ADD KEY `idx_message` (`message_id`)',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME   = 'llm_chatter_voice_live'
    AND COLUMN_NAME  = 'speaker_x'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE `llm_chatter_voice_live`
     ADD COLUMN `speaker_x` FLOAT NOT NULL DEFAULT 0 AFTER `rel_angle`',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME   = 'llm_chatter_voice_live'
    AND COLUMN_NAME  = 'speaker_y'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE `llm_chatter_voice_live`
     ADD COLUMN `speaker_y` FLOAT NOT NULL DEFAULT 0 AFTER `speaker_x`',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
