-- Party chat pacing gate metadata.

CREATE TABLE IF NOT EXISTS `llm_party_chat_pacing` (
    `group_id` INT UNSIGNED NOT NULL,
    `next_available_at` TIMESTAMP NULL DEFAULT NULL,
    `last_activity_at` TIMESTAMP NULL DEFAULT NULL,
    `last_policy` VARCHAR(24) DEFAULT NULL,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`group_id`),
    KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @has_group_id := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_chatter_messages'
      AND COLUMN_NAME = 'group_id'
);
SET @sql := IF(
    @has_group_id = 0,
    'ALTER TABLE `llm_chatter_messages`
       ADD COLUMN `group_id` INT UNSIGNED DEFAULT NULL
       AFTER `player_guid`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_policy := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_chatter_messages'
      AND COLUMN_NAME = 'delivery_policy'
);
SET @sql := IF(
    @has_policy = 0,
    'ALTER TABLE `llm_chatter_messages`
       ADD COLUMN `delivery_policy` VARCHAR(24) DEFAULT NULL
       AFTER `group_id`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_reason := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_chatter_messages'
      AND COLUMN_NAME = 'delivery_reason'
);
SET @sql := IF(
    @has_reason = 0,
    'ALTER TABLE `llm_chatter_messages`
       ADD COLUMN `delivery_reason` VARCHAR(64) DEFAULT NULL
       AFTER `delivery_policy`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_gate_idx := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_chatter_messages'
      AND INDEX_NAME = 'idx_party_gate'
);
SET @sql := IF(
    @has_gate_idx = 0,
    'ALTER TABLE `llm_chatter_messages`
       ADD KEY `idx_party_gate`
       (`channel`, `group_id`, `delivered`, `deliver_at`)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
