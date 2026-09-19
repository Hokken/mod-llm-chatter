-- Ground ambient trade requests in a live seller-inventory snapshot.

SET @has_message_type = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'llm_chatter_queue'
    AND COLUMN_NAME = 'message_type'
);

SET @sql = IF(
  @has_message_type = 0,
  CONCAT(
    "ALTER TABLE `llm_chatter_queue` ADD COLUMN ",
    "`message_type` VARCHAR(16) DEFAULT NULL AFTER `bot_count`"
  ),
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_item_context = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'llm_chatter_queue'
    AND COLUMN_NAME = 'item_context'
);

SET @sql = IF(
  @has_item_context = 0,
  CONCAT(
    "ALTER TABLE `llm_chatter_queue` ADD COLUMN ",
    "`item_context` JSON DEFAULT NULL AFTER `message_type`"
  ),
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
