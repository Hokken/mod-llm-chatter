-- Widen session trait columns to match `llm_bot_identities`.
-- `llm_bot_identities` and the `.llmc set` validation both allow 64
-- characters per trait, so copying a stored identity into the session
-- table failed with "Data too long for column 'trait1'" whenever a
-- trait exceeded 32 characters.

SET @trait1_len := (
    SELECT CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'trait1'
);
SET @sql := IF(
    @trait1_len IS NOT NULL AND @trait1_len < 64,
    'ALTER TABLE `llm_group_bot_traits`
       MODIFY COLUMN `trait1` VARCHAR(64) NOT NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @trait2_len := (
    SELECT CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'trait2'
);
SET @sql := IF(
    @trait2_len IS NOT NULL AND @trait2_len < 64,
    'ALTER TABLE `llm_group_bot_traits`
       MODIFY COLUMN `trait2` VARCHAR(64) NOT NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @trait3_len := (
    SELECT CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'trait3'
);
SET @sql := IF(
    @trait3_len IS NOT NULL AND @trait3_len < 64,
    'ALTER TABLE `llm_group_bot_traits`
       MODIFY COLUMN `trait3` VARCHAR(64) NOT NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
