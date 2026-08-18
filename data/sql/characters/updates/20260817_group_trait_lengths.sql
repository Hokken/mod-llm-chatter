-- Keep per-group traits large enough to mirror persistent identities.
-- Some valid personality traits exceed the original 32-character columns.

SET @needs_group_trait_widening = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'llm_group_bot_traits'
    AND COLUMN_NAME = 'trait1'
    AND CHARACTER_MAXIMUM_LENGTH < 64
);

SET @sql = IF(@needs_group_trait_widening = 1,
  'ALTER TABLE `llm_group_bot_traits`\n     MODIFY COLUMN `trait1` VARCHAR(64) NOT NULL,\n     MODIFY COLUMN `trait2` VARCHAR(64) NOT NULL,\n     MODIFY COLUMN `trait3` VARCHAR(64) NOT NULL',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
