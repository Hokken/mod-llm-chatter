-- Real listeners for themed topics and rumors on ambient General requests.

SET @has_audience_context = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'llm_chatter_queue'
    AND COLUMN_NAME = 'audience_context'
);

SET @sql = IF(
  @has_audience_context = 0,
  CONCAT(
    "ALTER TABLE `llm_chatter_queue` ADD COLUMN ",
    "`audience_context` JSON DEFAULT NULL AFTER `item_context`"
  ),
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
