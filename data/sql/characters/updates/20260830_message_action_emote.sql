-- Carry the LLM's `action` field to delivery separately from the
-- spoken line. It used to be inlined into `message` as
-- *asterisks*; it is now sent as a /e text emote just before the
-- speech, so the two need to travel as separate columns.

SET @has_action := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_chatter_messages'
      AND COLUMN_NAME = 'action'
);
SET @sql := IF(
    @has_action = 0,
    'ALTER TABLE `llm_chatter_messages`
       ADD COLUMN `action` VARCHAR(120) DEFAULT NULL AFTER `emote`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
