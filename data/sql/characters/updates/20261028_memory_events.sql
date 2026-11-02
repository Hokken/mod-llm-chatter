-- Discovery and duel memories: the bot_group_discovery event type and
-- the duel memory type. Appends only the missing values to whatever the
-- columns already hold, so this file can run before or after other
-- enum migrations, and again.

SET @event_type = (
  SELECT COLUMN_TYPE FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'llm_chatter_events'
    AND COLUMN_NAME = 'event_type'
);

SET @add_values = CONCAT_WS(',',
  IF(@event_type LIKE '%''bot_group_discovery''%', NULL, '''bot_group_discovery''')
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

SET @memory_type = (
  SELECT COLUMN_TYPE FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'llm_bot_memories'
    AND COLUMN_NAME = 'memory_type'
);

SET @add_values = CONCAT_WS(',',
  IF(@memory_type LIKE '%''duel''%', NULL, '''duel''')
);

SET @sql = IF(
  @memory_type IS NULL OR @add_values = '',
  'SELECT 1',
  CONCAT(
    'ALTER TABLE `llm_bot_memories` MODIFY COLUMN `memory_type` ',
    LEFT(@memory_type, CHAR_LENGTH(@memory_type) - 1),
    ',', @add_values, ') NOT NULL'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
