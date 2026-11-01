-- Orphan recovery runs on every bridge cleanup tick and groups the
-- pending memories (active = 0) by session; this index keeps that
-- query from scanning the whole table.
-- Adds the index only when it is missing; safe to run again.

SET @has_idx := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_bot_memories'
      AND INDEX_NAME = 'idx_active_group'
);
SET @sql := IF(
    @has_idx = 0,
    'ALTER TABLE `llm_bot_memories`
       ADD INDEX `idx_active_group`
       (`active`, `group_id`, `bot_guid`, `player_guid`)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
