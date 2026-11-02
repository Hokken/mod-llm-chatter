-- Bot memories remember where they happened and who else was there,
-- so recall can prefer the current place and companions.
-- Adds each column only when it is missing; safe to run again.

SET @col_exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'llm_bot_memories'
      AND COLUMN_NAME  = 'zone_id'
);
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `llm_bot_memories` ADD COLUMN `zone_id` INT UNSIGNED DEFAULT NULL AFTER `session_start`',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'llm_bot_memories'
      AND COLUMN_NAME  = 'map_id'
);
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `llm_bot_memories` ADD COLUMN `map_id` INT UNSIGNED DEFAULT NULL AFTER `zone_id`',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'llm_bot_memories'
      AND COLUMN_NAME  = 'companions'
);
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `llm_bot_memories` ADD COLUMN `companions` VARCHAR(255) DEFAULT NULL AFTER `map_id`',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
