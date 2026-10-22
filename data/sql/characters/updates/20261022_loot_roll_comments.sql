-- Party bots explain their Need or Greed roll on an item.
-- Appends only the missing value to whatever the column already holds,
-- so this file can run before or after other event-type migrations.

SET @event_type = (
  SELECT COLUMN_TYPE FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'llm_chatter_events'
    AND COLUMN_NAME = 'event_type'
);

SET @add_values = CONCAT_WS(',',
  IF(@event_type LIKE '%''bot_group_loot_roll''%', NULL, '''bot_group_loot_roll''')
);

SET @sql = IF(
  @event_type IS NULL OR @add_values = '',
  'SELECT 1',
  CONCAT(
    'ALTER TABLE `llm_chatter_events` MODIFY COLUMN `event_type` ',
    LEFT(@event_type, CHAR_LENGTH(@event_type) - 1),
    ',', @add_values, ') NOT NULL'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
