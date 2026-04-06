-- Add tone column to llm_bot_identities if it doesn't exist
SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'llm_bot_identities'
      AND COLUMN_NAME  = 'tone'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `llm_bot_identities` ADD COLUMN `tone` VARCHAR(120) DEFAULT NULL AFTER `role`',
    'SELECT 1');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
